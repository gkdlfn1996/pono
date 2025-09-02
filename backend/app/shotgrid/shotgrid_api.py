"""
ShotGrid 데이터 조회 로직을 담당하는 모듈입니다.

이 모듈은 두 가지 방식으로 사용할 수 있습니다.

1. 동기 방식 (Synchronous):
   - 이 파일에 정의된 대부분의 함수(예: get_projects)는 표준 동기 함수입니다.
   - 일반적인 Python 스크립트 환경에서 기존 방식 그대로 가져와서 사용할 수 있습니다.
   - 예: `from shotgrid_api import get_projects`

2. 비동기 방식 (Asynchronous):
   - FastAPI와 같은 비동기 환경에서의 사용을 위해, 모든 동기 함수에 대응하는
     비동기 버전을 `async_api` 객체를 통해 제공합니다.
   - `async_api` 객체는 이 모듈이 로드될 때 자동으로 생성됩니다.
   - 비동기 환경에서는 이 객체를 통해 함수를 호출해야 서버 블로킹을 방지할 수 있습니다.
   - 예: `from shotgrid_api import async_api`
   - 사용법: `await async_api.get_projects(...)`

`async_api`는 이 파일 하단의 자동화 코드를 통해, 이 모듈에 있는 모든 공개 함수들의
비동기 버전을 자동으로 생성하여 포함하므로, 별도의 수동 관리가 필요 없습니다.
"""

from functools import wraps
from pprint import pprint
from typing import List
import time


def timing(f):
    @wraps(f)
    def count_time(*args, **kwargs):
        start_time = time.time()      # 시작 시간 기록
        ret = f(*args, **kwargs) # 원래 메서드 실행
        end_time = time.time()      # 끝나는 시간 기록
        duration = end_time - start_time # 실행 시간 계산
        print(f"functions took {f.__name__}: {duration:.6f} seconds")
        return ret
    return count_time


# ===================================================================
# Part 1: 동기 API_샷그리드 데이터 관련 api 모음
# ===================================================================

def get_projects(sg):
    """
    모든 프로젝트의 이름 목록을 조회합니다.
    """
    print("Attempting to fetch projects...")
    result = sg.find(
        "Project",
        [["archived", "is", False],
         ["sg_restricted_user", "is", False],
         ["is_template", "is", False]], 
        ["name", "id"]
    )
    print(f"Successfully fetched {len(result)} projects.")
    return result

def get_pipeline_steps_for_project(sg, project_id):
    """
    특정 프로젝트에 연결된 Pipeline Step 목록을 조회합니다.
    """
    # 1. 프로젝트에 속한 모든 Task를 찾고, 각 Task에 연결된 Step 정보를 요청합니다.
    tasks = sg.find(
        "Task",
        [["project", "is", {"type": "Project", "id": project_id}]],
        ["step"]  # 'step' 필드는 Step 엔티티과의 연결 정보를 담고 있습니다.
    )

    if not tasks:
        return []

    # 2. 가져온 Task들에서 Step 이름만 추출하여 중복을 제거합니다.
    seen_steps = set()
    for task in tasks:
        if task.get('step') and task['step'].get('name'):
            seen_steps.add(task['step']['name'])

    # 3. 정렬된 딕셔너리 리스트 형태로 가공하여 반환합니다.
    return sorted([{'name': name} for name in seen_steps], key=lambda x: x['name'].lower())

@timing
def get_lightweight_versions(sg, project_id, pipeline_step_name):
    """
    특정 프로젝트와 파이프라인 스텝 이름에 연결된 '가벼운' Version 목록을 조회합니다.
    (성능을 위해 썸네일과 노트는 제외)
    """
    print(f"Attempting to fetch lightweight versions for pipeline_step '{pipeline_step_name}' in project {project_id}")

    # 기본적으로 프로젝트 필터만 설정합니다.
    filters = [['project', 'is', {'type': 'Project', 'id': project_id}]]

    # pipeline_step_name이 'All'이 아닐 경우에만 스텝 이름 필터를 추가합니다.
    if pipeline_step_name != 'All':
        filters.append(['sg_task.Task.step.Step.code', 'is', pipeline_step_name])

    fields = [
        "id", "code", "created_at", "tags", "playlists",
        "sg_status_list", "user", "sg_task", "entity", "step",
        "sg_task.Task.due_date",
        "sg_task.Task.sg_status_list",
        "entity.Shot.sg_status_list",
        "entity.Shot.sg_end_date",  # Asset이면 None
        "entity.Shot.sg_rnum",
        "entity.Asset.sg_status_list",  # Asset일 경우의 상태
    ]
    versions = sg.find("Version", filters, fields)
    
    print(f"Successfully fetched {len(versions)} versions.")
    return versions

@timing
def get_thumbnails_by_ids(sg, version_ids: List[int]):
    """
    주어진 버전 ID 목록에 해당하는 썸네일을 한 번에 조회합니다.
    """
    if not version_ids:
        return []
    
    filters = [['id', 'in', *version_ids]]
    fields = ['id', 'image']
    return sg.find("Version", filters, fields)

@timing
def get_notes_by_ids(sg, version_ids: List[int]):
    """
    주어진 버전 ID 목록에 연결된 모든 노트를 조회하고,
    버전 ID를 키로 하는 딕셔너리로 정리하여 반환합니다.
    """
    if not version_ids:
        return {}

    # 1. 모든 버전에 대해 note_map을 None으로 초기화
    note_map = {}
    for vid in version_ids:
        note_map[vid] = None

    # 2. ShotGrid에서 노트 조회
    version_entities = []
    for vid in version_ids:
        version_entities.append({'type': 'Version', 'id': vid})

    note_filters = [['note_links', 'in', *version_entities]]
    note_fields = ['content', 'user', 'created_at', 'subject', 'note_links']
    notes = sg.find("Note", note_filters, note_fields)

    # 3. note를 Version ID 기준으로 매핑
    for note in notes:
        for linked_ver in note.get("note_links", []):
            version_id = linked_ver['id']
            if note_map.get(version_id) is None:
                note_map[version_id] = []  # 첫 노트를 발견하면 리스트로 초기화

            note_map[version_id].append({
                "content" : note["content"],
                "user" : note["user"],
                "subject" : note["subject"],
                "created_at" : note["created_at"]
            })
    
    # 4. 각 노트 목록을 생성 시간(created_at)기준으로 정렬
    for version_id in note_map:
        if note_map[version_id] is not None:
            note_map[version_id].sort(key=lambda x: x.get('created_at'), reverse=True)

    return note_map



# ===================================================================
# Part 2: 비동기 API 자동 생성 영역
# ===================================================================

import sys
import inspect
from functools import partial, wraps
from types import SimpleNamespace
from fastapi.concurrency import run_in_threadpool

# 비동기 함수들을 담을 빈 객체(네임스페이스) 생성
async_api = SimpleNamespace()

def _create_async_wrapper(sync_func):
    """동기 함수를 받아 스레드 풀에서 실행하는 비동기 함수로 변환하는 래퍼"""
    @wraps(sync_func)
    async def _wrapper(*args, **kwargs):
        func_call = partial(sync_func, *args, **kwargs)
        return await run_in_threadpool(func_call)
    return _wrapper

# 현재 모듈에 정의된 모든 공개 함수를 찾아서 비동기 버전을 생성하고 async_api 객체에 추가
_current_module_namespace = locals().copy()
for name, func in _current_module_namespace.items():
    if inspect.isfunction(func) and not name.startswith("_"):
        async_version = _create_async_wrapper(func)
        setattr(async_api, name, async_version)


if __name__ == "__main__":
    import sys
    sys.path.append("/netapp/INHouse/sg")
    from shotgrid_authenticator import UserSG, SessionTokenSG
    from pprint import pprint
    
    session_token = '1a425e3b3414dda3efc3e30d2d2c5aa7'
    project_id = 815
    task_name = 'ani'
    
    token_sg = SessionTokenSG(session_token).sg
 
 
    # # sg는 shotgun_api3.Shotgun 인스턴스
    # task_schema = token_sg.schema_field_read('Task')
    # print('step' in task_schema)
    # print(task_schema.get('step'))