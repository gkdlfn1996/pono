<template>
  <v-app>
    <template v-if="loggedInUser">
      <!-- AppHeader 컴포넌트 -->
      <AppHeader :loggedInUser="loggedInUser" @toggle-drawer="drawer = !drawer" />

      <!-- 환영 스낵바 (로그인 성공 시 표시) -->
      <v-alert
        v-if="showWelcomeSnackbar"
        type="success"
        dense
        text
        class="welcome-snackbar"
        style="position: absolute; top: 64px; left: 0; width: 100%; z-index: 1000;"
      >
        <span>환영합니다, {{ loggedInUser }}!</span>
      </v-alert>

      <!-- AppSidebar 컴포넌트 -->
      <AppSidebar v-model="drawer" />
    </template>

    <v-main style="min-height: 100vh;">
      <!-- 로그인 섹션 (로그인되지 않았을 때만 표시) -->
      <LoginSection
        v-if="!loggedInUser"
        :username="username"
        :password="password"
        :loginError="loginError"
        @update:username="username = $event"
        @update:password="password = $event"
        @login="handleLoginEvent"
      />

       <!-- 로그인 성공 시 표시되는 메인 UI -->
       <v-container fluid v-else-if="loggedInUser" class="main-content-container fill-height">
         <v-row>
           <v-col cols="12">
           </v-col>
         </v-row>
        <v-row>
          
        </v-row>
        <!-- 버전 리스트 컴포넌트 (프로젝트와 태스크가 모두 선택되었을 때만 표시) -->
        <v-row v-if="projectName.value && selectedTaskName.value">
          <v-col cols="12">
            <!-- 버전 리스트 컴포넌트 -->
            <VersionList
              :versions="versions"
              :notes="notesContent"
              :notesComposable="notes"
              :isSaving="isSaving"
              @save-note="handleSaveNote"
              @input-note="handleInputNote"
              @refresh-versions="loadVersions"
              @reload-other-notes="notes.reloadOtherNotesForVersion"
              :sendMessage="sendMessage"
            />
          </v-col>
        </v-row>
        <!-- 프로젝트/태스크 선택 요청 메시지 (프로젝트 또는 태스크가 선택되지 않았을 때 표시) -->
        <v-container fluid v-else class="fill-height d-flex align-center justify-center">
          <v-col class="text-center">
            <v-icon size="128" color="grey-lighten-1">mdi-folder-open-outline</v-icon>
            <h2 class="text-h3 text-grey-lighten-1 mt-6">
              프로젝트와 테스크가 선택되지 않았습니다.
            </h2>
            <p class="text-h5 text-grey-lighten-1 mt-9">
              상단 바에서 프로젝트와 테스크를 선택하여 시작하세요.
            </p>
          </v-col>
        </v-container>
      </v-container>
    </v-main>

    <!-- NotesPanel 컴포넌트 -->
    <NotesPanel v-model="showNotesPanel" />

    <!-- ShotDetailPanel 컴포넌트 -->
    <ShotDetailPanel v-model="showShotDetailPanel" />
  </v-app>
</template>

<script>
import { onMounted, computed, watch, ref } from 'vue'; // onMounted는 App.vue에서 직접 사용
import useAuth from './composables/useAuth'; // 인증 로직
import useShotGridData from './composables/useShotGridData'; // ShotGrid 데이터 로직
import useNotes from './composables/useNotes'; // 노트 로직

import useWebSocket from './composables/useWebSocket'; // 웹소켓 로직

import LoginSection from './components/layout/LoginSection.vue'; // 로그인 컴포넌트
// import ShotSelector from './components/layout/ShotSelector.vue'; // 샷 선택 컴포넌트 (제거)
import VersionList from './components/versions/VersionList.vue'; // 버전 리스트 컴포넌트

// 새로운 레이아웃 및 패널 컴포넌트 임포트
import AppHeader from './components/layout/AppHeader.vue';
import AppSidebar from './components/layout/AppSidebar.vue';
import FloatingMenu from './components/layout/FloatingMenu.vue';
import NotesPanel from './components/panels/NotesPanel.vue';
import ShotDetailPanel from './components/panels/ShotDetailPanel.vue';


export default {
  components: {
    LoginSection,
    // ShotSelector, // 제거
    VersionList,
    AppHeader,
    AppSidebar,
    FloatingMenu,
    NotesPanel,
    ShotDetailPanel,
  },
  setup() {
    const auth = useAuth();
    const shotGridData = useShotGridData();
    const notes = useNotes(auth.loggedInUserId);
    const { connectWebSocket, sendMessage, disconnectWebSocket, receivedMessage } = useWebSocket();

    const drawer = ref(false); // 사이드바 상태 관리
    const showWelcomeSnackbar = ref(false); // 환영 스낵바 상태 관리
    // Create local computed property for isSaving
    

    // Watch for changes in notes.isSaving.value for debugging
    watch(() => notes.isSaving.value, (newValue) => {
      console.log('isSaving changed:', newValue);
    });

    // Create local wrapper functions for notes composable methods
    const handleSaveNote = async (versionId, content) => {
      // 진행중인 디바운스 저장이 있다면 취소
      notes.debouncedSave.cancel();
      // UI에 즉시 반영 (한글 입력 문제 해결을 위해)
      notes.notesContent.value[versionId] = content;
      await notes.saveImmediately(versionId, content);
    };

    const handleInputNote = (versionId, content) => {
      // UI에 즉시 반영
      notes.notesContent.value[versionId] = content;
      notes.debouncedSave(versionId, content);
    };

    // 웹소켓 메시지 수신 감지 및 otherNotes 업데이트
    watch(receivedMessage, (newMessage) => {
      if (newMessage && newMessage.type === 'note_update') {
        const { version_id, owner_id, content, updated_at, owner_username } = newMessage.payload;
        // 현재 사용자의 노트가 아닌 경우에만 업데이트
        if (owner_id !== auth.loggedInUserId.value) {
          notes.setNewOtherNotesFlag(version_id, true); // 새로운 노트 알림 플래그 설정
        }
      }
    });

    // LoginSection에서 발생한 'login' 이벤트를 처리하는 함수
    const handleLoginEvent = async () => {
      console.log('handleLoginEvent triggered in App.vue');
      await auth.login();
    };

    // 로그인 상태 변화 감지 및 환영 메시지 표시
    watch(() => auth.loggedInUser.value, (newVal) => {
      if (newVal) {
        showWelcomeSnackbar.value = true;
        setTimeout(() => {
          showWelcomeSnackbar.value = false;
        }, 3000); // 3초 후 사라짐
      }
    }, { immediate: true }); // 컴포넌트 마운트 시 즉시 실행

    onMounted(async () => {
      const storedUser = sessionStorage.getItem('loggedInUser');
      if (storedUser) {
        const user = JSON.parse(storedUser);
        auth.loggedInUser.value = user.name; // useAuth의 loggedInUser 업데이트
        auth.loggedInUserId.value = user.id; // useAuth의 loggedInUserId 업데이트
      }
      await shotGridData.loadProjects();
    });

    // loadVersions 함수는 App.vue에서 직접 관리 (ShotGridData와 Notes를 연결)
    const loadVersions = async (versionsData) => { // AppHeader에서 버전 데이터를 직접 받음
      try {
        const loadedVersions = versionsData || [];

        // useNotes의 loadVersionNotes 함수를 호출하여 노트 데이터 로딩
        await notes.loadVersionNotes(loadedVersions);

        // 웹소켓 연결 (선택된 Task의 모든 버전에 대해 연결)
        // Task ID를 version_id로 사용
        connectWebSocket(loadedVersions[0].sg_task.id, auth.loggedInUserId.value); // 첫 번째 버전의 Task ID를 사용

        // 모든 데이터가 준비되면 버전 목록 업데이트 (UI 렌더링 유발)
        shotGridData.setVersions(loadedVersions);
      } catch (error) {
        console.error("Error in loadVersions:", error);
        // 사용자에게 에러를 알리는 로직을 추가할 수 있습니다.
      }
    };

    // Clear 함수 (App.vue에서 직접 관리)
    const clear = () => { // useShotGridData의 clear 로직을 호출
      shotGridData.projectName.value = '';
      shotGridData.tasks.value = []; // tasks로 변경
      shotGridData.versions.value = [];
      shotGridData.selectedTaskName.value = ''; // selectedTaskName으로 변경
      auth.loginError.value = null;
      notes.notesContent.value = {}; // 노트 내용도 초기화
    };
    disconnectWebSocket(); // Clear 시 웹소켓 연결 해제

    // 패널 가시성 상태
    const showNotesPanel = ref(false);
    const showShotDetailPanel = ref(false);

    return {
      // useAuth에서 노출된 속성/함수
      username: auth.username,
      password: auth.password,
      loggedInUser: auth.loggedInUser,
      loginError: auth.loginError,
      login: auth.login,

      // useShotGridData에서 노출된 속성/함수
      projectName: shotGridData.projectName,
      projects: shotGridData.projects,
      tasks: shotGridData.tasks, // tasks로 변경
      selectedTaskName: shotGridData.selectedTaskName, // selectedTaskName으로 변경
      versions: shotGridData.versions,
      onProjectSelected: shotGridData.onProjectSelected,

      // useNotes에서 노출된 속성/함수
      notesContent: notes.notesContent, // notesContent ref 자체를 전달
      notes: notes, // VersionTable에 notes composable 전체를 전달하기 위해 필요
      isSaving: notes.isSaving, // useNotes의 isSaving을 직접 노출

      // App.vue에서 직접 관리하는 속성/함수
      loadVersions,
      clear,
      handleSaveNote,
      handleInputNote,
      sendMessage, // VersionTable로 전달
      handleLoginEvent, // 새로 추가한 로그인 이벤트 핸들러 노출
      drawer, // 사이드바 상태 노출
      showWelcomeSnackbar, // 환영 스낵바 상태 노출
      showNotesPanel,
      showShotDetailPanel,
      
     };
   },
 };
</script>

<style src="./assets/styles.css"></style>