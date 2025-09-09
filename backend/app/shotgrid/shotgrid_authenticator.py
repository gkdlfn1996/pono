# -*- coding: utf-8 -*-
import os
import pprint
import shotgun_api3
from fastapi import Request
from fastapi.responses import JSONResponse


SG_SERVER_URL = "https://idea.shotgrid.autodesk.com"


class SetSG:
    """
    ShotGrid 인증을 위한 기본 클래스.
    자식 클래스가 _authenticate()를 구현하면, 그 반환값(sg 연결)을
    최초 한 번만 생성하여 이후 모든 인스턴스에서 재사용합니다.
    """
    def __init__(self):
        self.sg = self._authenticate()

    def _authenticate(self):
        raise NotImplementedError("Child class must implement 'authenticate' method.")


class UserSG(SetSG):
    """
    사용자 인증(아이디/비전 or 세션 쿠키 등)으로 로그인하는 클래스.
    """
    def __init__(self, login_id="", login_pwd=""):
        self.sg_login_id = login_id
        self.sg_login_pw = login_pwd
        super().__init__()

    def _authenticate(self):
        # Shotgrid API 연결
        sg = shotgun_api3.Shotgun(
            SG_SERVER_URL,
            login=self.sg_login_id,
            password=self.sg_login_pw)
        return sg

    def get_session_token(self) -> str:
        """
        사용자 계정으로 세션 토큰을 반환합니다.
        """
        token = self.sg.get_session_token()

        return token


class SessionTokenSG(SetSG):
    """
    Shotgrid 세션 토큰 키 인증 클래스
    샷그리드 웹 로그인 시 발급된  session token을 받아 인증
    """
    def __init__(self, session_token=""):
        self.session_token = session_token
        super().__init__()

    def _authenticate(self):
        # Shotgrid API 연결
        sg = shotgun_api3.Shotgun(
            SG_SERVER_URL,
            session_token=self.session_token
        )
        return sg


import requests

def is_session_token_valid(server_url: str, session_token: str) -> bool:
    """
    ShotGrid 세션 토큰이 유효한지 검사합니다.
    :param server_url: ShotGrid 사이트 URL (예: "https://your-site.shotgrid.autodesk.com")
    :param session_token: sg.get_session_token() 또는 직접 입력한 세션 토큰
    :return: 유효하면 True, 그렇지 않으면 False
    """
    url = f"{server_url}/api/v1.1/auth/access_token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    data = {
        "grant_type": "session_token",
        "session_token": session_token
    }

    response = requests.post(url, headers=headers, data=data)
    # HTTP 200 OK 일 때만 유효한 세션 토큰으로 판단
    return response.status_code == 200

async def authentication_fault_handler(request: Request, exc):
    """
    ShotGrid의 AuthenticationFault를 처리하는 핸들러 함수.
    서버가 멈추는 대신 401 Unauthorized 응답을 반환합니다.
    """
    print(f"AuthenticationFault caught by handler: {exc}")
    return JSONResponse(
        status_code=401,
        content={"detail": "Authentication failed. Invalid or expired session token."},
    )

if __name__ == "__main__":
    SERVER_URL = "https://idea.shotgrid.autodesk.com"
    GOOD_TOKEN = "151694bc8447e762f8c9e82610b32ed2"
    BAD_TOKEN  = "wrongtoken"

    print("GOOD →", is_session_token_valid(SERVER_URL, GOOD_TOKEN))  # True 예상
    print("BAD  →", is_session_token_valid(SERVER_URL, BAD_TOKEN))   # False 예상
