<!-- frontend/src/components/versions/VersionList.vue -->
<template>
  <div class="versions-section" v-if="versions.length">
    <div class="d-flex align-center mb-2">
      <h2 class="mr-2">Version</h2>
      <v-btn icon="mdi-refresh" size="small" variant="text" @click="emit('refresh-versions')"></v-btn>
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

const props = defineProps({
  versions: Array,
  notes: Object, // notesContent 객체 (초기값 및 외부 업데이트용)
  notesComposable: Object, // notes composable 전체를 받음
  isSaving: Object, // isSaving prop 타입을 Object로 변경
  sendMessage: Function, // 웹소켓 메시지 전송 함수
});

const emit = defineEmits(['save-note', 'input-note', 'refresh-versions', 'reload-other-notes']);

</script>

<style scoped>
.version-list {
  /* 필요에 따라 스타일 추가 */
}
</style>