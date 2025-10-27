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
    <AppSidebar v-if="isAuthenticated" v-model="drawer" @open-publish-all-modal="showPublishAllModal = true" />

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
              :isSaved="isSaved"
              :newNoteIds="newNoteIds"
              :saveNote="saveMyNote"
              :debouncedSave="debouncedSave"
              :clearNewNoteFlag="clearNewNoteFlag"
              :uploadAttachments="uploadAttachments"
              :deleteAttachment="deleteAttachment"
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

    <!-- 다른 UI 요소들 (로그인 상태일 때만 표시) -->
    <ShotDetailPanel v-if="isAuthenticated" v-model="showShotDetailPanel" />
        <PublishAllNotesModal
          v-if="isAuthenticated"
          v-model="showPublishAllModal"
          :my-notes="myNotes"
        />
    
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
    import { ref, onMounted, onErrorCaptured, watch, onUnmounted } from 'vue';
    import { useAuth } from './composables/useAuth';
    import { useDraftNotes } from './composables/useDraftNotes';
    import { useShotGridData } from './composables/useShotGridData';
    
    // 컴포넌트 임포트
    import LoginSection from './components/layout/LoginSection.vue';
    import AppHeader from './components/layout/AppHeader.vue';
    import AppSidebar from './components/layout/AppSidebar.vue';
    import ShotDetailPanel from './components/layout/ShotDetailPanel.vue';
    import PublishAllNotesModal from './components/sidebar/PublishAllNotesModal.vue';
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
      clearShotGridDataState,
    } = useShotGridData();

// --- Draft Notes & WebSocket 중앙 상태 ---
const { 
  myNotes, 
  otherNotes, 
  isSaved, 
  newNoteIds, 
  fetchNotesByStep, 
  saveMyNote, 
  debouncedSave,
  clearNewNoteFlag,
  uploadAttachments,
  deleteAttachment,
  clearDraftNotesState,
  disconnectAllNotes,
} = useDraftNotes();


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
const showShotDetailPanel = ref(false);
const showPublishAllModal = ref(false);

// --- 이벤트 핸들러 ---
const handleLogin = async (credentials) => {
  await login(credentials.username, credentials.password);
};

// 로그아웃 시 모든 웹소켓 연결을 해제합니다.
const handleLogout = () => {
  disconnectAllNotes(); // 모든 웹소켓 연결 해제
  logout(); // useAuth의 로그아웃 처리 (인증 정보 삭제)
  clearShotGridDataState(); // useShotGridData 상태 초기화
  clearDraftNotesState(); // useDraftNotes 상태 초기화
};

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

// --- 로직 통합 ---

// 1. 선택된 스텝이 변경되면, 버전과 노트를 동시에 로딩
watch(selectedPipelineStep, (newStep) => {
    if (newStep && selectedProject.value) {
        Promise.all([
            loadVersions(false), // 캐시 미사용하고 새로고침
            fetchNotesByStep(selectedProject.value.id, newStep)
        ]);
    }
});

// 2. 로그아웃 시 모든 연결 해제
watch(isAuthenticated, (isAuth) => {
    if (!isAuth) {
        disconnectAllNotes();
    }
});

// 3. 컴포넌트가 언마운트될 때 (예: 페이지 이동, 브라우저 닫기) 모든 연결 해제
onUnmounted(() => {
  disconnectAllNotes();
});

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
