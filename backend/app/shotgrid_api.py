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

def get_versions_for_task(sg, task_name):
    """
    특정 Task에 연결된 Version 목록을 조회합니다。
    """
    print(f"Attempting to fetch versions for task_name: {task_name}")
    versions = sg.find(
        "Version",
        [["sg_task.Task.content", "is", task_name]],
        ["id", "code", "sg_status_list", "entity", "description", "created_at", "sg_task"]
    )
    print(f"Successfully fetched {len(versions)} versions for task_name: {task_name}")
    return versions

def get_projects(sg):
    """
    모든 프로젝트의 이름 목록을 조회합니다。
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