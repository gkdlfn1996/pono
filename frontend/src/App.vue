<template>
  <v-app>
    <template v-if="loggedInUser">
      <!-- AppHeader 컴포넌트 -->
      <AppHeader :loggedInUser="loggedInUser" @toggle-drawer="drawer = !drawer" @load-versions="loadVersions" />

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
        <v-row v-if="selectedProject && selectedTask">
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

    <!-- FloatingMenu 컴포넌트 -->
    <FloatingMenu
      @open-notes-panel="showNotesPanel = true"
      @open-shot-detail-panel="showShotDetailPanel = true"
    />
  

    <!-- NotesPanel 컴포넌트 -->
    <NotesPanel v-model="showNotesPanel" />

    <!-- ShotDetailPanel 컴포넌트 -->
    <ShotDetailPanel v-model="showShotDetailPanel" />
  </v-app>
</template>

<script>
import { ref } from 'vue';

import LoginSection from './components/layout/LoginSection.vue';
import AppHeader from './components/layout/AppHeader.vue';
import AppSidebar from './components/layout/AppSidebar.vue';
import FloatingMenu from './components/layout/FloatingMenu.vue';
import NotesPanel from './components/panels/NotesPanel.vue';
import ShotDetailPanel from './components/panels/ShotDetailPanel.vue';
import VersionList from './components/versions/VersionList.vue';

export default {
  components: {
    LoginSection,
    VersionList,
    AppHeader,
    AppSidebar,
    FloatingMenu,
    NotesPanel,
    ShotDetailPanel,
  },
  setup() {
    // --- 로그인 기능에 필요한 상태 ---
    const loggedInUser = ref(null); // null이면 로그인 화면, 값이 있으면 메인 화면
    const username = ref('');
    const password = ref('');
    const loginError = ref(null);

    // 로그인 버튼 클릭 시 실행될 임시 함수
    const handleLoginEvent = () => {
      console.log('Login attempt with:', username.value);
      // 실제 로그인은 다음 단계에서 구현합니다.
      // 지금은 로그인 성공을 시뮬레이션하기 위해 임시 사용자를 설정합니다.
      if (username.value) {
        loggedInUser.value = username.value;
      } else {
        loginError.value = "Username cannot be empty.";
      }
    };
    // --- 여기까지 ---

    // 메인 UI에 필요한 더미 데이터 (현재는 기능하지 않음)
    const drawer = ref(false);
    const showWelcomeSnackbar = ref(false);
    
    return {
      // 로그인 관련
      loggedInUser,
      username,
      password,
      loginError,
      handleLoginEvent,

      // 레이아웃 관련 (현재는 더미)
      drawer,
      showWelcomeSnackbar,
      showNotesPanel: ref(false),
      showShotDetailPanel: ref(false),
      versions: ref([]),
      notesContent: ref({}),
      isSaving: ref({}),
      selectedProject: ref(null),
      selectedTask: ref(null),
      loadVersions: () => {},
      handleSaveNote: () => {},
      handleInputNote: () => {},
      sendMessage: () => {},
      notes: { reloadOtherNotesForVersion: () => {} },
    };
  },
};
</script>
