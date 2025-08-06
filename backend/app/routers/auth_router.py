from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
import sys # sys 임포트 유지
sys.path.append("/netapp/INHouse/sg") # 경로 추가 유지
from SG_Authenticator import UserSG, SessionTokenSG # UserSG와 SessionTokenSG 임포트 유지

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)

@router.post("/login")
async def login_for_session_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    사용자 ID/PW로 ShotGrid에 인증하고, 성공 시 ShotGrid 세션 토큰을 반환합니다.
    """
    try:
        user_sg_auth = UserSG(login_id=form_data.username, login_pwd=form_data.password) # UserSG 인스턴스 생성
        sg_session_token = user_sg_auth.get_session_token() # get_session_token 호출 (세션 토큰 문자열 반환)
        print(f"SESSION_TOKEN : {sg_session_token}")
        
        # UserSG 인스턴스 내부에 있는 sg 객체를 사용하여 사용자 정보 조회
        # user_sg_auth.sg는 UserSG.__init__에서 이미 인증된 Shotgun 객체입니다.
        user_info = user_sg_auth.sg.find_one("HumanUser", [["login", "is", form_data.username]], ["id", "name", "login"])
        
        print(f"[SUCCESS] User '{form_data.username}' authenticated. Returning session token.")
        
        return {"session_token": sg_session_token, "token_type": "bearer", "user_info": user_info}
    
    except Exception as e:
        print(f"Authentication failed for user '{form_data.username}': {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
        sg_instance = SessionTokenSG(session_token=session_token).sg
        if not sg_instance:
            raise Exception("Failed to create ShotGrid instance with session token.")
        return sg_instance
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Could not validate credentials: {e}")