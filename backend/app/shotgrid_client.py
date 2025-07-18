import os
import sys

sys.path.append("/netapp/INHouse/sg")
from SG_Authenticator import ScriptSG, UserSG


class ShotGridClient:
    """
    ShotGrid API 호출을 관리하는 클라이언트 클래스
    """
    def __init__(self):
        script_sg = ScriptSG("idea")
        self.sg = script_sg.sg

    def get_project_by_name(self, name: str):
        return self.sg.find_one(
            "Project",
            [["name", "is", name]],
            ["id"]
        )

    def get_shots(self, project_id: int):
        return self.sg.find(
            "Shot",
            [["project.Project.id", "is", project_id]],
            ["id", "code", "sg_task", "sg_cut_in", "sg_cut_out"]
        )

    def get_projects(self):
        """
        모든 프로젝트의 이름 목록을 조회합니다。
        """
        result = self.sg.find(
            "Project",
            [["archived", "is", False],
             ["sg_restricted_user", "is", False],
             ["is_template", "is", False]], 
            ["name"]
        )
        return [p["name"] for p in result]

    def get_versions_for_shot(self, shot_id: int):
        """
        특정 Shot에 연결된 Version 목록을 조회합니다。
        """
        return self.sg.find(
            "Version",
            [["entity", "is", {"type": "Shot", "id": shot_id}]], # Shot 엔티티에 연결된 버전 필터링
            ["id", "code", "sg_status_list"] # 필요한 필드 추가
        )

    def authenticate_human_user(self, login: str, password: str):
        """
        ShotGrid에 사용자 이름과 비밀번호로 인증을 시도합니다.
        성공 시 HumanUser 엔티티를 반환하고, 실패 시 None을 반환합니다.
        """
        try:
            # 사용자 자격 증명으로 Shotgun 인스턴스 생성 시도
            # 이 방법은 ShotGrid API가 인간 사용자 인증을 지원하는 방식입니다.
            user_sg = UserSG(login_id=login, login_pwd=password)
            # 인증 성공 시, 해당 사용자의 정보를 조회하여 반환
            self.sg = user_sg.sg
            user_info = self.sg.find_one("HumanUser", [["login", "is", login]], ["id", "name", "login"])
            return user_info
        except Exception as e:
            print(f"ShotGrid 사용자 인증 실패: {login} - {e}")
            return None
        
if __name__ == "__main__":
    # 테스트를 위한 사용자 이름과 비밀번호를 여기에 입력하세요.
    # 실제 ShotGrid 계정 정보를 사용해야 합니다.
    test_username = "d10583"
    test_password = "rlatpdus123@"

    client = ShotGridClient()
    print(f"ShotGrid 사용자 '{test_username}' 인증 시도...")
    user_data = client.authenticate_human_user(test_username, test_password)
    print(f"인증 결과: {user_data}")
