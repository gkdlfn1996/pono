<!-- frontend/src/components/versions/VersionList.vue -->
<template>
  <div class="versions-section" v-if="versions.length > 0">
    <div class="d-flex align-center mb-2">
      <h2 class="mr-2">Version</h2>
      <v-btn
        :icon="isLoading ? 'mdi-spin mdi-refresh' : 'mdi-refresh'"
        size="small"
        variant="text"
        @click="refreshVersions"
        :disabled="isLoading"
      ></v-btn>
    </div>
    <div class="version-list">
      <VersionCard
        v-for="versionItem in versions"
        :key="versionItem.id"
        :version="versionItem"
        :notes="notes"
        :notesComposable="notesComposable"
        :isSaving="isSaving"
        :sendMessage="sendMessage"
        @save-note="emit('save-note', $event.versionId, $event.content)"
        @input-note="emit('input-note', $event.versionId, $event.content)"
        @reload-other-notes="emit('reload-other-notes', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import VersionCard from './VersionCard.vue'; // VersionCard 컴포넌트 임포트
import { versions, isLoading, selectedTask, selectTask } from '../../composables/useShotGridData';

const props = defineProps({
  notes: Object, // notesContent 객체 (초기값 및 외부 업데이트용)
  notesComposable: Object, // notes composable 전체를 받음
  isSaving: Object, // isSaving prop 타입을 Object로 변경
  sendMessage: Function, // 웹소켓 메시지 전송 함수
});

const emit = defineEmits(['save-note', 'input-note', 'reload-other-notes']);

const refreshVersions = () => {
  if (selectedTask.value) {
    // 현재 선택된 태스크로 버전 목록을 다시 로드합니다.
    // selectTask 함수는 내부적으로 로딩 상태를 관리하고 versions를 업데이트합니다.
    selectTask(selectedTask.value.id);
  }
};
</script>

<style scoped>
.version-list {
  /* 필요에 따라 스타일 추가 */
}
</style>