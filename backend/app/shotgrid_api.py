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

def get_tasks_for_project(sg, project_id):
    """
    특정 프로젝트에 연결된 Task 목록을 조회합니다.
    """
    raw_tasks = sg.find(
        "Task",
        [["project.Project.id", "is", project_id]],
        ["id", "content"]
    )

    # 이름으로 중복을 제거
    grouped_tasks = {}
    for task in raw_tasks:
        if 'content' in task and task['content']:
            task_name = task['content']
            # task_id = task['id']
            if task_name not in grouped_tasks:
                grouped_tasks[task_name] = {'name': task_name}
            # grouped_tasks[task_name]['ids'].append(task_id)
    
    processed_tasks = list(grouped_tasks.values())

    # 태스크 이름을 알파벳 순으로 정렬
    processed_tasks.sort(key=lambda x: x.get('name', '').lower())
    
    print(f"ShotGrid tasks for project_id {project_id}: {[item['name'] for item in processed_tasks]}")
    return processed_tasks

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
def get_versions_for_task(sg, project_id, task_name):
    """
    특정 프로젝트와 태스크 이름에 연결된 Version 목록을 조회합니다.
    """
    print(f"Attempting to fetch versions for task '{task_name}' in project {project_id}")

    filters = [
        ['project', 'is', {'type': 'Project', 'id': project_id}],
        ['sg_task.Task.content', 'is', task_name],
    ]

    # 기본적으로 프로젝트 필터만 설정합니다.
    filters = [['project', 'is', {'type': 'Project', 'id': project_id}]]

    # task_name이 'All'이 아닐 경우에만 테스크 이름 필터를 추가합니다.
    if task_name != 'All':
        filters.append(['sg_task.Task.content', 'is', task_name])

    fields = [
        "id", "code",  "created_at", "tags", "playlists",
        "image",
        "sg_status_list",  "user", "sg_task", "entity",
        "sg_task.Task.due_date",
        "sg_task.Task.sg_status_list",
        "entity.Shot.sg_status_list",
        "entity.Shot.sg_end_date",  # Asset이면 None
        "entity.Shot.sg_rnum",
        "entity.Asset.sg_status_list",  # Asset일 경우의 상태
        "open_notes"
    ]
    versions = sg.find("Version", filters, fields)

    if not versions:
        return []

    # 버전 ID 목록을 추출하여 연결된 노트를 한 번에 조회
    note_map = _get_notes_for_versions(sg, versions)

    # 각 버전에 해당하는 노트를 추가
    for version in versions:
        version['notes'] = note_map.get(version['id'], [])
    
    print(f"Successfully fetched {len(versions)} versions.")
    return versions

@timing
def get_versions_for_pipeline_step(sg, project_id, pipeline_step_name):
    """
    특정 프로젝트와 파이프라인 스텝 이름에 연결된 Version 목록을 조회합니다.
    """
    print(f"Attempting to fetch versions for pipeline_step '{pipeline_step_name}' in project {project_id}")
    # 기본적으로 프로젝트 필터만 설정합니다.
    filters = [['project', 'is', {'type': 'Project', 'id': project_id}]]

    # pipeline_step_name이 'All'이 아닐 경우에만 스텝 이름 필터를 추가합니다.
    if pipeline_step_name != 'All':
        filters.append(['sg_task.Task.step.Step.code', 'is', pipeline_step_name])

    fields = [
        "id", "code",  "created_at", "tags", "playlists",
        "image",
        "sg_status_list",  "user", "sg_task", "entity", "step",
        "sg_task.Task.due_date",
        "sg_task.Task.sg_status_list",
        "entity.Shot.sg_status_list",
        "entity.Shot.sg_end_date",
        "entity.Shot.sg_rnum",
        "entity.Asset.sg_status_list",
        "open_notes"
    ]
    versions = sg.find("Version", filters, fields)
    if not versions:
        return []

    note_map = _get_notes_for_versions(sg, versions)
    for version in versions:
        version['notes'] = note_map.get(version['id'], [])
    
    print(f"Successfully fetched {len(versions)} versions.")
    return versions

# @timing
def _get_notes_for_versions(sg, versions):
    """
    주어진 버전 ID 목록에 연결된 모든 노트를 조회하고,
    버전 ID를 키로 하는 딕셔너리로 정리하여 반환합니다.
    """
    if not versions:
        return {}
    
    note_filters = [['note_links', 'in', versions]]
    note_fields = ['content', 'user', 'created_at', 'subject', 'note_links']
    notes = sg.find("Note", note_filters, note_fields)

    # note를 Version ID 기준으로 매핑
    note_map = {}
    for note in notes:
        for linked_ver in note.get("note_links", []):
            version_id = linked_ver['id']
            if version_id not in note_map:
                note_map[version_id] = []

            note_map[version_id].append({
                "content" : note["content"],
                "user" : note["user"],
                "subject" : note["subject"],
                "created_at" : note["created_at"]
            })
    
    # 각 노트 목록을 생성 시간(created_at)기준으로 정렬
    for version_id in note_map:
        note_map[version_id].sort(key=lambda x: x.get('created_at'), reverse=True)

    return note_map

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
    from SG_Authenticator import UserSG, SessionTokenSG
    from pprint import pprint
    
    session_token = '9099084729abe8b3995027b444ddf756'
    project_id = 815
    task_name = 'ani'
    
    token_sg = SessionTokenSG(session_token).sg

    # versions = get_versions_for_task(token_sg, project_id, task_name)
    # pprint(versions)


    # sg는 shotgun_api3.Shotgun 인스턴스
    task_schema = token_sg.schema_field_read('Task')
    print('step' in task_schema)
    print(task_schema.get('step'))
