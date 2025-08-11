"""
샷그리드 데이터 관련 api 모음
"""


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
    
    print(f"ShotGrid tasks for project_id {project_id}: {processed_tasks}")
    return processed_tasks

def get_versions_for_task(sg, project_id, task_name):
    """
    특정 프로젝트와 태스크 이름에 연결된 Version 목록을 조회합니다.
    """
    print(f"Attempting to fetch versions for task '{task_name}' in project {project_id}")
    filters = [
        ['project.Project.id', 'is', project_id],
        ['sg_task.Task.content', 'is', task_name],
    ]

    fields = [
        "id", "code", "description", "created_at",
        "sg_status_list", "image", "user", "sg_task", "entity",
        "sg_task.Task.due_date",
        "sg_task.Task.sg_status_list",
        "entity.Shot.sg_status_list",
        "entity.Shot.sg_end_date",  # Asset이면 None
        "entity.Asset.sg_status_list",  # Asset일 경우의 상태
        "open_notes"
    ]
    versions = sg.find("Version", filters, fields)

    if not versions:
        return []

    # 버전 ID 목록을 추출하여 연결된 노트를 한 번에 조회
    # version_ids = [version["id"] for version in versions]
    note_map = _get_notes_for_versions(sg, versions)

    # 각 버전에 해당하는 노트를 추가
    for version in versions:
        version['notes'] = note_map.get(version['id'], [])
    
    print(f"Successfully fetched {len(versions)} versions.")
    return versions


def _get_notes_for_versions(sg, versions):
    """
    주어진 버전 ID 목록에 연결된 모든 노트를 조회하고,
    버전 ID를 키로 하는 딕셔너리로 정리하여 반환합니다.
    """
    if not versions:
        return {}
    
    note_filters = [['note_links', 'in', versions]]
    note_fields = ['content', 'user', 'created_at', 'note_links']
    notes = sg.find("Note", note_filters, note_fields)

    print("######")
    print(notes)
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


if __name__ == "__main__":
    import sys
    sys.path.append("/netapp/INHouse/sg")
    from SG_Authenticator import UserSG, SessionTokenSG
    from pprint import pprint
    
    session_token = '9b9e8b4c02c63ff19d00d7a5de652f16'
    project_id = 1046
    task_name = 'light'
    
    token_sg = SessionTokenSG(session_token).sg

    versions = get_versions_for_task(token_sg, project_id, task_name)
    # pprint(versions)
    
