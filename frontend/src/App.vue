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
      <v-container fluid v-else class="main-content-container">
        <v-row v-if="selectedProject && selectedPipelineStep">
          <v-col cols="12">
            <VersionList
              :versions="displayVersions"
              :sortBy="sortBy"
              :sortOrder="sortOrder"
              :presentEntityTypes="presentEntityTypes"
              :setSort="setSort"
              @refresh-versions="loadVersions"
              :myNotes="myNotes"
              :otherNotes="otherNotes"
              :isSaving="isSaving"
              :newNoteIds="newNoteIds"
              :saveNote="saveMyNote"
              :debouncedSave="debouncedSave"
              :clearNewNoteFlag="clearNewNoteFlag"
            />
            <div class="text-center mt-4" v-if="!isVersionsLoading && totalPages > 1">
              <v-pagination
                :model-value="currentPage"
                :length="totalPages"
                @update:model-value="changePage"
              ></v-pagination>
            </div>
          </v-col>
        </v-row>

        <!-- 프로젝트/태스크 선택 요청 메시지 (프로젝트 또는 태스크가 선택되지 않았을 때 표시) -->
        <v-row v-else class="fill-height d-flex align-center justify-center">
          <v-col class="text-center">
            <v-icon size="128" color="grey-lighten-1">mdi-folder-open-outline</v-icon>
            <h2 class="text-h3 text-grey-lighten-1 mt-6">
              프로젝트와 테스크가 선택되지 않았습니다.
            </h2>
            <p class="text-h5 text-grey-lighten-1 mt-9">
              상단 바에서 프로젝트와 테스크를 선택하여 시작하세요.
            </p>
          </v-col>
        </v-row>
      </v-container>
    </v-main>

    <!-- FloatingMenu 등 다른 UI 요소들 (로그인 상태일 때만 표시) -->
    <FloatingMenu v-if="isAuthenticated" />
    <NotesPanel v-if="isAuthenticated" v-model="showNotesPanel" />
    <ShotDetailPanel v-if="isAuthenticated" v-model="showShotDetailPanel" />

    <!-- 최상단으로 스크롤하는 플로팅 버튼 -->
    <div class="scroll-to-top">
      <v-btn
        icon="mdi-arrow-collapse-up"
        variant="tonal"
        size="small"
        @click="scrollToTop"
      ></v-btn>
    </div>
  </v-app>
</template>

<script setup>
import { ref, onMounted, onErrorCaptured, watch } from 'vue';
import { useAuth } from './composables/useAuth';
import { useDraftNotes } from './composables/useDraftNotes';
import { useShotGridData } from './composables/useShotGridData';
import { useWebSocket } from './composables/useWebSocket';

// 컴포넌트 임포트
import LoginSection from './components/layout/LoginSection.vue';
import AppHeader from './components/layout/AppHeader.vue';
import AppSidebar from './components/layout/AppSidebar.vue';
import FloatingMenu from './components/layout/FloatingMenu.vue';
import NotesPanel from './components/panels/NotesPanel.vue';
import ShotDetailPanel from './components/panels/ShotDetailPanel.vue';
import VersionList from './components/layout/VersionList.vue';

// --- 인증 관련 상태 및 함수 ---
const { isAuthenticated, user, loginError, login, logout, checkAuthStatus } = useAuth();
const isAuthCheckComplete = ref(false);

// --- ShotGrid 데이터 중앙 상태 ---
const {
  displayVersions,
  isVersionsLoading,
  currentPage,
  totalPages,
  selectedProject,
  selectedPipelineStep,
  sortBy,
  sortOrder,
  presentEntityTypes,
  loadVersions,
  changePage,
  setSort,
} = useShotGridData();

// --- Draft Notes & WebSocket 중앙 상태 ---
const { myNotes, otherNotes, isSaving, newNoteIds, fetchNotesByStep, saveMyNote, debouncedSave, handleIncomingNote, clearNewNoteFlag } = useDraftNotes();
const ws = useWebSocket();

// App 컴포넌트가 마운트될 때 인증 상태를 확인합니다.
onMounted(async () => {
  await checkAuthStatus();
  isAuthCheckComplete.value = true;
});

// 자식 컴포넌트에서 발생하는 에러 감지
onErrorCaptured((err) => {
  console.error("A critical error occurred in a child component: ", err);
});

// --- UI 상태 ---
const drawer = ref(false);
const showNotesPanel = ref(false);
const showShotDetailPanel = ref(false);

// --- 이벤트 핸들러 ---
const handleLogin = async (credentials) => {
  await login(credentials.username, credentials.password);
};
const handleLogout = () => logout();

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

// --- 로직 통합 ---

// 1. 선택된 스텝이 변경되면, 버전과 노트를 동시에 로딩
watch(selectedPipelineStep, (newStep) => {
    if (newStep && selectedProject.value) {
        Promise.all([
            loadVersions(false), // 캐시 미사용하고 새로고침
            fetchNotesByStep(selectedProject.value.id, newStep.name)
        ]);
    }
});

// 2. 인증 상태가 되면 웹소켓 연결
watch(isAuthenticated, (isAuth) => {
    if (isAuth && !ws.isConnected.value) {
        // 백엔드 /ws/{version_id}는 특정 버전에만 한정되므로,
        // 모든 노트 변경을 수신하기 위한 범용 엔드포인트가 필요합니다.
        // 백엔드 라우터에서 /ws/{version_id}를 수정하여 version_id를 옵셔널로 받거나,
        // 새 범용 엔드포인트를 만들어야 합니다. 여기서는 임시로 version_id 0을 사용합니다.
        const wsUrl = `ws://${window.location.hostname}:8001/api/notes/ws/0`;
        ws.connect(wsUrl, handleIncomingNote);
    } else if (!isAuth && ws.isConnected.value) {
        ws.disconnect();
    }
}, { immediate: true });

</script>

<style scoped>
.scroll-to-top {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 99;
}
</style>