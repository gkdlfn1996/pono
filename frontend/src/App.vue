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
              :isSaved="isSaved"
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
  handleIncomingNote, 
  clearNewNoteFlag,
  clearDraftNotesState,
} = useDraftNotes();

// '커넥션 매니저'로 업그레이드된 useWebSocket 사용
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

// 로그아웃 시 모든 웹소켓 연결을 해제합니다.
const handleLogout = () => {
  ws.disconnectAll(); // 모든 웹소켓 연결 해제
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
            fetchNotesByStep(selectedProject.value.id, newStep.name)
        ]);
    }
});

// 2. 화면에 표시되는 버전 목록(displayVersions)을 감시하여 웹소켓 연결을 동적으로 관리
watch(displayVersions, async (newVersions, oldVersions) => {
    // 로그인 상태가 아니면 아무 작업도 하지 않음
    if (!isAuthenticated.value) return;

    // 현재 화면의 버전 ID와 이전 화면의 버전 ID를 Set으로 만들어 비교 준비
    const newVersionIds = new Set(newVersions.map(v => v.id));
    const oldVersionIds = new Set((oldVersions || []).map(v => v.id));

    // --- 1. 새로 연결할 웹소켓 식별 ---
    // 이전 목록에는 없었지만 새 목록에는 있는, 즉 새로 화면에 표시된 버전들을 찾음
    const versionsToConnect = newVersions.filter(v => !oldVersionIds.has(v.id) && !ws.isConnected(v.id));
    
    // --- 2. 연결 해제할 웹소켓 식별 ---
    // 이전 목록에는 있었지만 새 목록에는 없는, 즉 화면에서 사라진 버전 ID들을 찾음
    const versionIdsToDisconnect = [...oldVersionIds].filter(id => !newVersionIds.has(id));

    // 새로 추가된 버전에 대해 연결 생성
    if (versionsToConnect.length > 0) {
        // --- 3. 모든 연결을 동시에 시도하고 Promise 배열로 만듦 ---
        const connectionPromises = versionsToConnect.map(version => {
            const wsUrl = `ws://${window.location.hostname}:8001/api/notes/ws/${version.id}`;
            // connect 함수는 Promise를 반환. 성공/실패 여부를 추적하기 위해 .then과 .catch를 사용
            return ws.connect(version.id, wsUrl, handleIncomingNote)
                     .then(() => ({ status: 'fulfilled', id: version.id })) // 성공 시
                     .catch(() => ({ status: 'rejected', id: version.id }));  // 실패 시
        });

        // --- 4. 모든 연결 시도가 완료될 때까지 기다림 ---
        const results = await Promise.allSettled(connectionPromises);
        
        // --- 5. 결과 집계 및 요약 로그 생성 ---
        const successful = results.filter(r => r.value.status === 'fulfilled').length;
        const failed = results.filter(r => r.value.status === 'rejected');
        const failedIds = failed.map(r => r.value.id);

        let logMessage = `[WebSocket Summary] ${versionsToConnect.length}개 버전 연결 시도 -> 성공: ${successful}개`;
        if (failed.length > 0) {
            logMessage += `, 실패: ${failed.length}개 (ID: ${failedIds.join(', ')})`;
        }
        console.log(logMessage);
    }

    // 화면에서 사라진 버전에 대해 연결 해제
    if (versionIdsToDisconnect.length > 0) {
        // console.log(`[App.vue] Disconnecting WebSockets for ${versionIdsToDisconnect.length} versions.`);
        versionIdsToDisconnect.forEach(id => ws.disconnect(id));
    }
}, { deep: true }); // 객체 내부의 변경까지 감지하기 위해 deep 옵션 사용

// 3. 로그아웃 시 모든 연결 해제 (handleLogout 함수로 이전)
watch(isAuthenticated, (isAuth) => {
    if (!isAuth) {
        ws.disconnectAll();
    }
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