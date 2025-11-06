# PONO 서버 초기 셋업 매뉴얼 (Rocky Linux 9.5)

> **작성일** : 2025-11-06  
> **환경** : Rocky Linux 9.5 / PostgreSQL 15 / Python 3.10.13 / Node.js 18  
> **작성자** : 윤선진(Lazypic)

<br>

## 0) 기본 시스템 패키지 설치 (루트 계정)

```bash
# 루트 계정(su)으로 실행
su
```

~~dnf -y update --security --exclude=kernel*~~
시스템 설정 에러가 많아 제외. GUI가 없는 깨끗한 운용 서버에서는 해도 좋을듯.

```bash
dnf -y install epel-release

# 1. Git, Curl, Screen 설치
dnf -y install git curl screen

# 2. PostgreSQL 서버 설치 및 초기화
dnf -y install postgresql-server
postgresql-setup --initdb
systemctl enable --now postgresql

# 3. Node.js 18 및 npm 설치 (Frontend 실행용)
dnf -y module install nodejs:18
exit
```

<br>

## 1) 프로젝트 받기 → 루트 전환 → 환경변수 로드

```bash
cd /home/idea
git clone https://github.com/gkdlfn1996/pono
```

```bash
# 루트 계정(su)으로 실행
su
```

```bash
cd pono
source ./config.sh
echo "$DB_NAME" "$DATABASE_URL"
```

```bash
# 답변이 이렇게 나오면 성공
shotgrid_notes_db postgresql://idea:fnxmdkagh1!@localhost:5432/shotgrid_notes_db
```

<br>

## 2) Python 3.10 소스 빌드 최소 의존성 설치

```bash
dnf -y groupinstall "Development Tools"
dnf -y install \
  openssl-devel libffi-devel zlib-devel sqlite-devel \
  bzip2-devel xz-devel
```

<br>

## 3) PostgreSQL 데이터베이스 초기화(최초 1회)


**!!주의!! :   
su - postgres로 직접 들어가지 말고, 현재 셸에서 변수 확장 + su -c로 실행. (su - 루트 권환)**


```bash
su - postgres -c "createdb \"${DB_NAME}\""
su - postgres -c "createuser \"${DB_USER}\""
su - postgres -c "psql -d postgres -c \"ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';\""
su - postgres -c "psql -d postgres -c \"GRANT ALL ON DATABASE ${DB_NAME} TO ${DB_USER};\""
su - postgres -c "psql -d ${DB_NAME} -c \"GRANT USAGE, CREATE ON SCHEMA public TO ${DB_USER};\""
```

```bash
# 답변이 이렇게 나오면 성공
ALTER ROLE
GRANT
GRANT
```

<br>

## 4) PostgreSQL 인증방식을 md5로 변경 

```bash
vim /var/lib/pgsql/data/pg_hba.conf
```
- vim 수정 명령어 : `i`
- vim 저장 후 종료 명령어  : `ESC` 누르고 `:wq`

<br>

**1. pg_hba.conf 파일을 수정하여 <u>모든 인증 방식(METHOD)</u>을 md5로 변경. (su - 루트권한)**

수정 전 (예시):
```bash

  # "local" is for Unix domain socket connections only
  local   all             all                                     peer
  # IPv4 local connections:
  host    all             all             127.0.0.1/32            ident
  # IPv6 local connections:
  host    all             all             ::1/128                 ident
  
  ...이하동문..
```
여기서 마지막 컬럼에 있는 peer 또는 ident를 모두 `md5`로 변경해 주세요.
  
<br>

  수정 후:
```bash
  # "local" is for Unix domain socket connections only
  local   all             all                                     md5
  # IPv4 local connections:
  host    all             all             127.0.0.1/32            md5
  # IPv6 local connections:
  host    all             all             ::1/128                 md5

  ...이하동문...
```
<br>

**2. 데이터베이스 서비스 재시작**
```bash
systemctl restart postgresql
```

<br>

## 5) 백엔드(자동) — Python 로컬 설치 + venv + 의존성 + 실행

```bash
exit # su 해제
```

```bash
cd pono
source ./config.sh
cd "$BACKEND_DIR"
./bin/pono_backend.sh
```

- 이 스크립트가 **(1) Python 3.10.13 로컬 빌드(없으면) → (2) .venv 생성 → (3) pip install -r → (4) uvicorn을 screen 세션(`pono_backend`)으로 실행**까지 자동 처리.
- 오래 걸릴 수 있음.

### backend 설치 확인:

```bash
# 백엔드 스크린 세션 접속
screen -r pono_backend
```
```bash
# 백엔드 스크린 세션 분리
Ctrl + A, D
```

<br>

## 6) 프론트엔드(자동) — screen 세션으로 실행

```bash
cd "$BACKEND_DIR"
./bin/pono_frontend.sh
```

- 내부 커맨드: `npm install && npm run serve`를 screen 세션(`pono_frontend`)으로 실행.

### frontend 설치 확인:

```bash
# 프론트엔드 스크린 세션 접속
screen -r pono_frontend
```
```bash
# 프론트엔드 스크린 세션 분리
Ctrl + A, D
```

<br>

## 7) 서비스 접속 확인

- 프론트: `http://localhost:<FRONTEND_PORT>`
    - 2025.11.6 기준 - **10.0.1.110:8080**
- 백엔드(예: OpenAPI): `http://localhost:<BACKEND_PORT>/docs`
    - 2025.11.6 기준 - **10.0.1.110:8000/docs**

<br>

## +@) 재시작·갱신

```bash
# 최신 코드 받기
cd /home/idea/pono # 프로젝트 폴더
git pull
source ./config.sh
```
```bash
# 백엔드/프론트엔드 재시작
cd "$BACKEND_DIR" && ./bin/pono_launcher.sh
```
```bash
# 백엔드만 재시작
cd "$BACKEND_DIR" && ./bin/pono_backend.sh
```
```bash
# 프론트엔드만 재시작
cd "$BACKEND_DIR" && ./bin/pono_frontend.sh
```

<br>