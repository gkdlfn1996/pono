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
        ["name", "id", "sg_sup", "sg_cg_sup", "sg_pd", "sg_pm", "sg_pa"]
    )
    print(f"Successfully fetched {len(result)} projects.")
    return result

@timing
def get_pipeline_steps_for_project(sg, project_id):
    """
    특정 프로젝트에 연결된 Pipeline Step 목록을 조회합니다.
    """
    project = {"type": "Project", "id": project_id}

    filters = []
    filters.append(["project", "is", project])
    # Task에 Step이 지정된 것만
    filters.append(["step", "is_not", None])

    summary_fields = []
    summary_fields.append({"field": "id", "type": "count"})

    grouping = []
    grouping.append({"field": "step", "type": "exact", "direction": "asc"})


    result = sg.summarize(
        entity_type="Task",
        filters=filters,
        summary_fields=summary_fields,
        grouping=grouping
    )

    # 결과 정리: (Step name만 중복 제거 후 정렬)
    used_steps = set()
    for g in result.get("groups", []):
        step_name = g.get("group_name")
        step_value = g.get("group_value")
        count = g.get("summaries", {}).get("id", 0)
        if step_value and count:
            used_steps.add(step_name)

    used_steps = sorted(used_steps)
    return used_steps

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
        "project",
        "sg_status_list", "user", "sg_task", "entity",
        "sg_task.Task.step",
        "sg_task.Task.due_date",
        "sg_task.Task.sg_status_list",
        "entity.Shot.sg_status_list",
        "entity.Shot.sg_end_date",  # Asset이면 None
        "entity.Shot.sg_rnum",
        "entity.Asset.sg_status_list",  # Asset일 경우의 상태
    ]
    versions = sg.find("Version", filters, fields)
    # pprint(versions)
    print(f"Successfully fetched {len(versions)} versions.")
    return versions

def get_thumbnails_by_ids(sg, version_ids: List[int]):
    """
    주어진 버전 ID 목록에 해당하는 썸네일을 한 번에 조회합니다.
    """
    if not version_ids:
        return []
    
    filters = [['id', 'in', *version_ids]]
    fields = ['id', 'image']
    return sg.find("Version", filters, fields)

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

def get_linked_entity_notes(sg, entity_type: str, entity_id: int):
    """
    주어진 Entity(Shot 또는 Asset)에 연결된 모든 '오픈' 상태의 노트를 조회합니다.
    """
    if not entity_type or not entity_id:
        return []

    filters = [
        ['note_links', 'in', {'type': entity_type, 'id': entity_id}],
        ['sg_status_list', 'is_not', 'cls']  # 'cls' (closed) 상태가 아닌 노트만
    ]
    fields = ['content', 'user', 'created_at', 'subject']
    order = [{'field_name': 'created_at', 'direction': 'desc'}] # 최신순 정렬

    entity_notes = sg.find("Note", filters, fields, order)
    print(f"Found {len(entity_notes)} open notes for {entity_type} ID {entity_id}")
    return entity_notes

@timing
def get_group_leaders_for_artists(sg, artist_id_list: List[int]):
    """
    주어진 아티스트 ID 목록에 대해, 각 아티스트가 속한 그룹의 리더들을 조회합니다.

    반환값 설명:
      - key: 아티스트의 ID (int)
      - value: 해당 아티스트가 속한 그룹에 포함된 'leader' 권한 유저들의 정보 리스트

    반환 형식 예시:
      {
        101: [{'id': 5, 'name': 'Leader_A'}],
        102: [{'id': 6, 'name': 'Leader_B'}]
      }
    """
    # 0) 입력 검증
    if not artist_id_list:
        return {}

    # 1) Group.users 필드에 artist_id가 포함된 Group 엔티티를 조회하기 위한 엔티티 리스트 구성
    artist_entities = []
    for artist_id in artist_id_list:
        artist_entities.append({'type': 'HumanUser', 'id': artist_id})


    # 2) Group 조회 (users 필드 포함)
    groups = sg.find(
        "Group",
        [['users', 'in', artist_entities]],    # 'in' 연산자의 값은 리스트 하나여야 함
        ['users']
    )


    # 3) 결과 구조, 중복 방지 구조, 아티스트 집합을 "한 번의 루프"로 초기화 (중복 루프 결합)
    result = {}
    added_leader_ids_by_artist = {}
    artist_id_set = set()
    for artist_id in artist_id_list:
        result[artist_id] = []
        added_leader_ids_by_artist[artist_id] = set()
        artist_id_set.add(artist_id)
 

    # 4) 모든 그룹의 users에서 user_id만 수집 (그룹 루프 1회차)
    all_user_ids = set()
    for group in groups:
        user_list = group.get('users', [])
        for user in user_list:
            user_id = user.get('id')
            if isinstance(user_id, int):
                all_user_ids.add(user_id)


    # 5) 그룹에 유저가 전혀 없으면 조기 반환
    if not all_user_ids:
        return result


    # 6) 'leader' 권한 유저 조회 (PermissionRuleSet.code 기준)
    leaders = sg.find(
        "HumanUser",
        [
            ['id', 'in', list(all_user_ids)],
            ['permission_rule_set.PermissionRuleSet.code', 'is', 'leader']
        ],
        ['id', 'name']
    )


    # 7) leader_id → leader dict 매핑 (빠른 조회용)
    leader_by_id = {}
    for leader in leaders:
        leader_id = leader.get('id')
        if isinstance(leader_id, int):
            leader_by_id[leader_id] = leader


    # 8) 그룹을 돌며 "해당 그룹의 리더"와 "해당 그룹의 아티스트"를 동시에 판별하여 매핑 (그룹 루프 2회차)
    #    - 중복 제거는 added_leader_ids_by_artist로 처리
    for group in groups:
        user_list = group.get('users', [])

        group_leaders = []       # 이 그룹에 속한 리더 dict들의 리스트
        group_artist_ids = set() # 이 그룹에 속한 아티스트 id들의 집합

        for user in user_list:
            user_id = user.get('id')
            if not isinstance(user_id, int):
                continue

            # 리더 판별
            if user_id in leader_by_id:
                group_leaders.append(leader_by_id[user_id])

            # 아티스트 판별
            if user_id in artist_id_set:
                group_artist_ids.add(user_id)

        # 이 그룹에 속한 각 아티스트에게 이 그룹의 리더들을 매핑(중복 방지)
        for artist_id in group_artist_ids:
            for leader in group_leaders:
                leader_id = leader.get('id')
                if isinstance(leader_id, int):
                    if leader_id not in added_leader_ids_by_artist[artist_id]:
                        result[artist_id].append(leader)
                        added_leader_ids_by_artist[artist_id].add(leader_id)

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
    from shotgrid_authenticator import UserSG, SessionTokenSG
    from pprint import pprint
    
    session_token = '80f4b2b334bf8f2bc65b65488258b83b'
    project_id = 848
    pipeline_step_name = 'All'
    
    token_sg = SessionTokenSG(session_token).sg
    

    versions = get_lightweight_versions(token_sg, project_id, pipeline_step_name)
    artist_id_set = set()
    for version in versions:
        if version.get('user') and version['user'].get('id'):
            artist_id_set.add(version['user']['id'])
    artist_ids = list(artist_id_set)

    leaders_by_artist = get_group_leaders_for_artists(token_sg, artist_ids)
    pprint(leaders_by_artist)
