<template>
  <v-app>
    <v-main>
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
      <v-container fluid v-else-if="loggedInUser" :class="{'mt-5': loggedInUser}">
        <v-alert type="success" dense text class="mb-5">
          <span>환영합니다, {{ loggedInUser }}!</span>
        </v-alert>

        <!-- 샷 선택 컴포넌트 -->
        <ShotSelector
          :projectName="projectName"
          :projects="projects"
          :shots="shots"
          :selectedShotName="selectedShotName"
          @update:projectName="projectName = $event"
          @update:selectedShotName="selectedShotName = $event"
          @onProjectSelected="onProjectSelected"
          @loadVersions="loadVersions"
          @clear="clear"
        />

        <!-- 버전 테이블 컴포넌트 -->
        <VersionTable
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
      </v-container>
    </v-main>
  </v-app>
</template>

<script>
import { onMounted, computed, watch } from 'vue'; // onMounted는 App.vue에서 직접 사용
import useAuth from './composables/useAuth'; // 인증 로직
import useShotGridData from './composables/useShotGridData'; // ShotGrid 데이터 로직
import useNotes from './composables/useNotes'; // 노트 로직
import { fetchVersionsForShot } from './api'; // API 호출 함수

import useWebSocket from './composables/useWebSocket'; // 웹소켓 로직

import LoginSection from './components/LoginSection.vue'; // 로그인 컴포넌트
import ShotSelector from './components/ShotSelector.vue'; // 샷 선택 컴포넌트
import VersionTable from './components/VersionTable.vue'; // 버전 테이블 컴포넌트


export default {
  components: {
    LoginSection,
    ShotSelector,
    VersionTable,
  },
  setup() {
    const auth = useAuth();
    const shotGridData = useShotGridData();
    const notes = useNotes(auth.loggedInUserId);
    const { connectWebSocket, sendMessage, disconnectWebSocket, receivedMessage } = useWebSocket();

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

    // App.vue의 onMounted 로직
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
    const loadVersions = async () => {
      try {
        const selectedShot = shotGridData.shots.value.find(s => s.code === shotGridData.selectedShotName.value);
        if (!selectedShot) return;

        const versionData = await fetchVersionsForShot(selectedShot.id);
        const loadedVersions = versionData.versions || [];

        // useNotes의 loadVersionNotes 함수를 호출하여 노트 데이터 로딩
        await notes.loadVersionNotes(loadedVersions);

        // 웹소켓 연결 (선택된 샷의 모든 버전에 대해 연결)
        // 각 버전별로 웹소켓 연결을 맺는 대신, 현재는 하나의 샷에 대한 모든 버전을 관리하는 방식으로 진행
        // 실제로는 각 버전별로 웹소켓 연결을 맺거나, 서버에서 특정 샷의 모든 버전을 브로드캐스트하는 방식 고려
        connectWebSocket(selectedShot.id, auth.loggedInUserId.value); // 샷 ID를 version_id로 사용
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
      shotGridData.shots.value = [];
      shotGridData.versions.value = [];
      shotGridData.selectedShotName.value = '';
      auth.loginError.value = null;
      notes.notesContent.value = {}; // 노트 내용도 초기화
    };
    disconnectWebSocket(); // Clear 시 웹소켓 연결 해제

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
      shots: shotGridData.shots,
      selectedShotName: shotGridData.selectedShotName,
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
    };
  },
};
</script>

<style src="./assets/styles.css"></style>