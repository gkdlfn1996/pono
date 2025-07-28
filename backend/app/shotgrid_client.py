import os
import sys
from typing import Optional

sys.path.append("/netapp/INHouse/sg")
from SG_Authenticator import ScriptSG, UserSG


class ShotGridClient:
    """
    ShotGrid API 호출을 관리하는 클라이언트 클래스
    """
    def __init__(self):
        self.sg = None # 인증 전에는 None으로 유지

    def _get_active_sg_connection(self):
        """
        현재 활성화된 ShotGrid 연결 객체를 반환합니다.
        인증된 연결이 없으면 ScriptSG를 사용하여 임시 연결을 반환합니다.
        """
        if self.sg:
            return self.sg
        return ScriptSG("idea").sg # 로그인 전이나 실패 시 임시 ScriptSG 사용

    def get_tasks_for_project(self, project_id: int):
        """
        특정 프로젝트에 연결된 Task 목록을 조회합니다.
        """
        sg_conn = self._get_active_sg_connection() # 활성 연결 사용
        raw_tasks = sg_conn.find(
            "Task",
            [["project.Project.id", "is", project_id]], # self.sg 사용
            ["id", "content"] # 필요한 필드만 가져옵니다.
        )

        # 중복된 content를 가진 태스크를 제거하고, id와 content를 포함하는 새 형식으로 변환
        # content를 키로 사용하여 중복을 제거하고, 마지막으로 발견된 태스크의 id를 사용합니다.
        unique_tasks_map = {}
        for task in raw_tasks:
            if 'content' in task and task['content']: # content 필드가 있고 비어있지 않은 경우만 처리
                unique_tasks_map[task['content']] = {'name': task['content'], 'id': task['id']}
        
        processed_tasks = list(unique_tasks_map.values())

        # 태스크 이름을 알파벳 순으로 정렬
        processed_tasks.sort(key=lambda x: x.get('name', '').lower())
        
        print(f"ShotGrid tasks for project_id {project_id}: {processed_tasks}")
        return processed_tasks

    def get_versions_for_task(self, task_id: int):
        """
        특정 Task에 연결된 Version 목록을 조회합니다.
        """
        # ShotGrid에서 Version 엔티티를 쿼리합니다.
        # 'sg_task' 필드를 통해 특정 Task에 연결된 Version만 필터링합니다.
        # 필요한 Version 필드를 추가합니다.
        print(f"Attempting to fetch versions for task_id: {task_id}")
        versions = self._get_active_sg_connection().find(
            "Version",
            [["sg_task", "is", {"type": "Task", "id": task_id}]],
            ["id", "code", "sg_status_list", "entity", "description", "created_at", "sg_task"]
        )
        print(f"Successfully fetched {len(versions)} versions for task_id: {task_id}")
        return versions

    def get_projects(self):
        """
        모든 프로젝트의 이름 목록을 조회합니다.
        """
        print("Attempting to fetch projects...")
        sg_conn = self._get_active_sg_connection() # 활성 연결 사용
        result = sg_conn.find(
            "Project",
            [["archived", "is", False],
             ["sg_restricted_user", "is", False],
             ["is_template", "is", False]], 
            ["name", "id"]
        )
        print(f"Successfully fetched {len(result)} projects.")
        return result


    def authenticate_human_user(self, login: str, password: str):
        """
        ShotGrid에 사용자 이름과 비밀번호로 인증을 시도합니다.
        성공 시 HumanUser 엔티티를 반환하고, 실패 시 None을 반환합니다.
        """
        try:
            # 사용자 자격 증명으로 Shotgun 인스턴스 생성 시도
            user_sg = UserSG(login_id=login, login_pwd=password)
            # 인증 성공 시, 해당 사용자의 정보를 조회하여 반환
            self.sg = user_sg.sg
            user_info = self.sg.find_one("HumanUser", [["login", "is", login]], ["id", "name", "login"])
            print(f"Successfully found HumanUser: {user_info['login']}")
            return user_info
        except Exception as e:
            print(f"ShotGrid 사용자 인증 실패: {login} - {e}")
            self.sg = None # 인증 실패 시 self.sg를 None으로 설정
            return None
        

if __name__ == "__main__":    
    # 테스트를 위한 사용자 이름과 비밀번호를 여기에 입력하세요.
    # 실제 ShotGrid 계정 정보를 사용해야 합니다. 
    # test_username = "d10583"
    # test_password = "rlatpdus123@"
    test_username = "ideatd"
    test_password = "fnxmdkagh1!"

    # HumanUser 인증 테스트                                                                                        
    client = ShotGridClient()
    print(f"ShotGrid 사용자 '{test_username}' 인증 시도...")
    user_data = client.authenticate_human_user(test_username, test_password)
    print(f"인증 결과: {user_data}")

    # ScriptSG 인증 테스트
    if user_data:
        print("--- ScriptSG 인증 테스트 ---")
        try:
            # 인증된 사용자의 sg 객체를 사용하여 프로젝트 목록 조회
            projects = client.get_projects()
            print(f"ScriptSG 인증 성공: {len(projects)} projects found.")
        except Exception as e:
            print(f"ScriptSG 인증 실패: {e}")
