# PONO Frontend
이 프로젝트는 Vue 3와 Vuetify 3를 사용하여 개발되었습니다.

<br>

# fast_vue

## Project setup
```
npm install
```

### Compiles and hot-reloads for development
```
npm run serve
```

### Compiles and minifies for production
```
npm run build
```

### Lints and fixes files
```
npm run lint
```

### Customize configuration
See [Configuration Reference](https://cli.vuejs.org/config/).

---

## **프로젝트 구조**

- **`src/components`**: UI를 구성하는 재사용 가능한 컴포넌트들이 위치합니다.
- **`src/composables`**: Vue 3의 Composition API를 사용하여 기능별 로직과 상태를 분리한 '훅(Hook)'들이 위치합니다.
    - `useAuth.js`: 사용자 인증 및 세션 관리
    - `useShotGridData.js`: ShotGrid 데이터 조회, 캐싱, 필터링
    - `useDraftNotes.js`: 임시 노트 CRUD 및 WebSocket 통신
- **`src/plugins`**: `axios` (API 클라이언트), `vuetify` (UI 프레임워크) 등 전역 플러그인 설정이 위치합니다.
- **`src/App.vue`**: 애플리케이션의 최상위 레이아웃 컴포넌트입니다.
- **`src/main.js`**: Vue 앱의 시작점(Entry Point)입니다.

## **환경 변수**
프론트엔드 위치한 `.env`파일에서 설정을 변경하실 수 있습니다.

```bash
# 프론트엔드 개발 서버 포트
VUE_APP_FRONTEND_PORT=8080

#연결할 백엔드 서버의 포트
VUE_APP_BACKEND_PORT=8000
```
