import requests
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..draftnote import database_models as models
from ..draftnote.database import get_db
from ..shotgrid import shotgrid_authenticator

SERVER_URL = "https://idea.shotgrid.autodesk.com"

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)

@router.post("/login")
async def login_for_session_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)): # db 의존성 추가
    """
    사용자 ID/PW로 ShotGrid에 인증하고, 성공 시 ShotGrid 세션 토큰을 반환합니다.
    """
    try:
        user_sg_auth = shotgrid_authenticator.UserSG(
            login_id=form_data.username, login_pwd=form_data.password
        )
        sg_session_token = user_sg_auth.get_session_token() # get_session_token 호출 (세션 토큰 문자열 반환)
        print(f"SESSION_TOKEN : {sg_session_token}")
        
        # UserSG 인스턴스 내부에 있는 sg 객체를 사용하여 사용자 정보 조회
        # user_sg_auth.sg는 UserSG.__init__에서 이미 인증된 Shotgun 객체입니다.
        sg_user_info = user_sg_auth.sg.find_one("HumanUser", [["login", "is", form_data.username]], ["id", "name", "login"])

        # 로컬 DB에 사용자 정보 저장 또는 조회
        local_user = db.query(models.User).filter(models.User.login == sg_user_info["login"]).first()
        if not local_user:
            # 사용자가 없으면 새로 생성
            local_user = models.User(
                id=sg_user_info["id"],          # ShotGrid User ID
                login=sg_user_info["login"],     # ShotGrid 로그인 ID(사번)
                username=sg_user_info["name"]   # SHotGrid 사용자 이름
                )
            db.add(local_user)
            db.commit()
            db.refresh(local_user)
        
        print(f"[SUCCESS] User '{form_data.username}' authenticated. Returning session token. Local user ID: {local_user.id}")
        
        return {"session_token": sg_session_token, "token_type": "bearer", "user_info": sg_user_info} # ShotGrid에서 받은 user_info 그대로 반환
    
    except Exception as e:
        print(f"Authentication failed for user '{form_data.username}': {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/validate-session-token", response_model=bool)
async def validate_session_token(authorization: str = Header(None)):
    """
    헤더의 Bearer 세션 토큰으로 ShotGrid에 인증이 가능한지 검사하여
    유효하면 True, 그렇지 않으면 False를 반환합니다.
    """
    if authorization is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authorization header missing")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid authorization format")

    session_token = parts[1]

    url = f"{SERVER_URL}/api/v1.1/auth/access_token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    data = {
        "grant_type": "session_token",
        "session_token": session_token
    }

    resp = requests.post(url, headers=headers, data=data)
    return resp.status_code == 200


async def get_shotgrid_instance(authorization: str = Header(None)):
    """
    요청 헤더의 세션 토큰으로 ShotGrid 인스턴스를 생성하고 반환하는 의존성.
    """
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    session_token = parts[1]
    try:
        sg_instance = shotgrid_authenticator.SessionTokenSG(
            session_token=session_token
        ).sg
        if not sg_instance:
            raise Exception("Failed to create ShotGrid instance with session token.")
        return sg_instance
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Could not validate credentials: {e}")