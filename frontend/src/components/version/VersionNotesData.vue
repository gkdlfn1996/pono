<template>
  <!-- 3단: Version Notes 영역 -->
  <div class="d-flex flex-column h-100">
    <h4 class="text-subtitle-1 font-weight-bold mb-2">Version Notes</h4>
    <v-card variant="outlined" class="flex-grow-1 d-flex flex-column">
      <v-card-text class="flex-grow-1 pa-0 notes-container" style="min-height: 0;">
        <template v-if="version.notes && version.notes.length > 0">
          <div v-for="(note, index) in version.notes" :key="note.id">
            <div class="d-flex justify-space-between align-center px-3 pt-2 pb-1">
              <span class="text-subtitle-2 font-weight-bold">{{ note.user.name }}</span>
              <span class="text-caption text-grey">{{ formatDateTime(note.created_at) }}</span>
            </div>
            <div v-if="note.subject" class="text-subtitle-2 font-weight-bold px-3 pb-1 text-grey">
              {{ note.subject }}
            </div>
            <div class="text-body-2 pt-0 pb-2 px-3" style="white-space: pre-wrap; word-wrap: break-word;">{{ note.content }}</div>
            <v-divider v-if="index < version.notes.length - 1"></v-divider>
          </div>
        </template>
        <div v-else class="d-flex align-center justify-center fill-height">
          <p class="text-grey text-center">
            버전 노트가 없습니다.
          </p>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
const props = defineProps({
  version: {
    type: Object,
    required: true,
  },
});

const formatDateTime = (isoString) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleString('ko-KR', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
    hour12: false
  }).replace(/\.\s/g, '.');
};
</script>

<style scoped>
.notes-container {
  overflow-y: auto;
  height: 300px;
}
</style>