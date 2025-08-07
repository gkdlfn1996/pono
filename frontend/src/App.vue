<template>
  <v-app v-if="isAuthCheckComplete">
    <!-- AppHeader는 로그인 상태일 때만 표시됩니다. -->
    <AppHeader 
      v-if="isAuthenticated" 
      :username="user?.name" 
      @toggle-drawer="drawer = !drawer" 
      @logout="handleLogout"
    />

    <!-- AppSidebar는 로그인 상태일 때만 표시됩니다. -->
    <AppSidebar v-if="isAuthenticated" v-model="drawer" />

    <v-main style="min-height: 100vh;">
      <!-- 로그인 섹션 (로그인되지 않았을 때만 표시) -->
      <LoginSection
        v-if="!isAuthenticated"
        :login-error="loginError"
        @login="handleLogin"
      />

      <!-- 로그인 성공 시 표시되는 메인 UI -->
      <v-container fluid v-else class="main-content-container fill-height">
        <!-- 버전 리스트 컴포넌트 (프로젝트와 태스크가 모두 선택되었을 때만 표시) -->
        <v-row v-if="selectedProject && selectedTask">
          <v-col cols="12">
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

    <!-- FloatingMenu 등 다른 UI 요소들 (로그인 상태일 때만 표시) -->
    <FloatingMenu v-if="isAuthenticated" />
    <NotesPanel v-if="isAuthenticated" v-model="showNotesPanel" />
    <ShotDetailPanel v-if="isAuthenticated" v-model="showShotDetailPanel" />
  </v-app>
</template>

<script>
import { ref, onMounted, onErrorCaptured } from 'vue';
import { useAuth } from './composables/useAuth';

// 컴포넌트 임포트
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
    // --- 인증 관련 상태 및 함수 ---
    const { isAuthenticated, user, loginError, login, logout, checkAuthStatus } = useAuth();
    const isAuthCheckComplete = ref(false); // 인증 확인 완료 여부

    // App 컴포넌트가 마운트될 때 (시작될 때) 인증 상태를 확인합니다.
    onMounted(async() => {
      await checkAuthStatus();
      isAuthCheckComplete.value = true;
    });

    // 자식 컴포넌트에서 발생하는 처리되지 않은 에러를 여기서 감지합니다.
    onErrorCaptured((err) => {
      console.error("A critical error occurred in a child component: ", err);
      // 치명적인 에러가 발생했음을 전역 플래그에 기록합니다.
      
      // return false; 를 제거하여 에러가 화면에 정상적으로 표시되도록 합니다.
    });

    // --- 기존 UI 및 데이터 관련 상태 ---
    const drawer = ref(false);
    const showNotesPanel = ref(false);
    const showShotDetailPanel = ref(false);
    const versions = ref([]);
    const notesContent = ref({});
    const isSaving = ref({});
    const selectedProject = ref(null); // 실제로는 AppHeader 등에서 업데이트되어야 함
    const selectedTask = ref(null);  // 실제로는 AppHeader 등에서 업데이트되어야 함
    console.log('[App.vue] setup executed. Initial local selectedTask:', selectedTask.value);

    // --- 이벤트 핸들러 ---
    const handleLogin = async (credentials) => {
      await login(credentials.username, credentials.password);
      // 로그인 성공 여부와 관계없이 프로젝트/태스크 선택 상태를 변경하지 않습니다.
      // 이 로직은 향후 사용자가 직접 프로젝트와 태스크를 선택했을 때 실행되어야 합니다.
      // if (isAuthenticated.value) {
      //     selectedProject.value = { id: 1, name: 'Test Project' };
      //     selectedTask.value = { id: 1, name: 'Test Task' };
      // }
    };

    const handleLogout = () => {
      logout();
      selectedProject.value = null;
      selectedTask.value = null;
    };

    // --- 기존 더미 함수들 ---
    const handleSaveNote = () => console.log('handleSaveNote called');
    const handleInputNote = () => console.log('handleInputNote called');
    const sendMessage = () => console.log('sendMessage called');
    const notes = { reloadOtherNotesForVersion: () => console.log('reloadOtherNotesForVersion called') };

    return {
      isAuthenticated,
      user,
      loginError,
      handleLogin,
      handleLogout,
      
      drawer,
      showNotesPanel,
      showShotDetailPanel,
      versions,
      notesContent,
      isSaving,
      selectedProject,
      selectedTask,
      handleSaveNote,
      handleInputNote,
      sendMessage,
      notes,
      isAuthCheckComplete,
    };
  },
};
</script>