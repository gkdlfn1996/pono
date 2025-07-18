<!-- frontend/src/components/VersionTable.vue -->
<template>
  <div class="versions-section" v-if="versions.length">
    <div class="d-flex align-center mb-2">
      <h2 class="mr-2">Version</h2>
      <v-btn icon="mdi-refresh" size="small" variant="text" @click="emit('refresh-versions')"></v-btn>
    </div>
    <v-data-table
      :headers="versionHeaders"
      :items="versions"
      item-key="id"
      class="elevation-1"
      hide-default-footer
      disable-pagination
    >
      <template v-slot:item.note="{ item }">
        <div class="note-section">
          <div class="my-note">
            <h3>My Draft Note ({{ item.code }})</h3>
            <v-textarea
              label="여기에 노트를 작성하세요"
              rows="3"
              v-model="localNotesContent[item.id]"
              @input="
                emit('input-note', item.id, localNotesContent[item.id]);
                sendMessage({
                  type: 'note_update',
                  payload: {
                    version_id: item.id,
                    content: localNotesContent[item.id],
                  },
                });"
              @blur="emit('save-note', item.id, localNotesContent[item.id])"
              variant="outlined"
              :class="{ 'saving-note': !!isSaving[item.id] }"
            ></v-textarea>
          </div>
          <div class="other-notes mt-4">
            <div class="d-flex align-center mb-2">
            <h3>Others Draft Notes</h3>
            <v-btn
              icon="mdi-refresh"
              size="small"
              variant="text"
              :color="notesComposable.hasNewOtherNotes.value[item.id] ? 'red' : ''" @click="emit('reload-other-notes', item.id)"></v-btn>
            </div>
            <v-card variant="outlined" class="notes-container">
              <template v-if="notesComposable.otherNotes.value[item.id] && notesComposable.otherNotes.value[item.id].length">
                <div v-for="(note, index) in notesComposable.otherNotes.value[item.id]" :key="note.id">
                  <div class="d-flex justify-space-between align-center px-2 pb-1">
                    <span class="text-subtitle-2 text-grey-darken-1">{{ note.owner.username }}</span>
                    <span class="text-caption text-right text-grey-darken-1">{{ formatDateTime(note.updated_at) }}</span>
                  </div>
                  <v-card-text class="note-content text-body-2 pa-2">
                    {{ note.content }}
                  </v-card-text>
                  <v-divider v-if="index < notesComposable.otherNotes.value[item.id].length - 1"></v-divider>
                </div>
              </template>
              <v-card-text v-else>
                다른 사용자의 노트가 없습니다.
              </v-card-text>
            </v-card>
          </div>
        </div>
      </template>
    </v-data-table>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  versions: Array,
  notes: Object, // notesContent 객체 (초기값 및 외부 업데이트용)
  notesComposable: Object, // notes composable 전체를 받음
  isSaving: Object, // isSaving prop 타입을 Object로 변경
  sendMessage: Function, // 웹소켓 메시지 전송 함수
});

const emit = defineEmits(['save-note', 'input-note', 'refresh-versions', 'reload-other-notes']); // emit 이벤트 추가

const versionHeaders = [
  { title: 'Version', key: 'code', sortable: false },
  { title: 'Note', key: 'note', sortable: false },
];

// 로컬 노트 내용을 저장할 반응형 객체
const localNotesContent = ref({});

// props.notes가 변경될 때 localNotesContent를 초기화
watch(() => props.notes, (newNotes) => {
  localNotesContent.value = { ...newNotes };
}, { immediate: true, deep: true });

// 날짜 포맷팅 함수
const formatDateTime = (isoString) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  // ko-KR 로케일을 사용하여 'YYYY. MM. DD. HH:mm:ss' 형식으로 변환
  return date.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).replace(/\.\s/g, '.').slice(0, -1); // 마지막 '.' 제거
};

</script>

<style scoped>
/* v-textarea 컴포넌트에 saving-note 클래스가 있을 때, 내부의 v-field__field에 스타일 적용 */
::v-deep .v-textarea.saving-note .v-field__field {
  transition: background-color 0.5s ease-in-out; /* 트랜지션 시간 증가 */
  background-color: #E0F2F7; /* 연한 파란색 배경 */
}
/* 저장 완료 후 원래 색상으로 돌아오도록 CSS 트랜지션 추가 */

.notes-container {
  height: 115px; /* v-textarea의 높이와 유사하게 설정 */
  overflow-y: auto; /* 내용이 많아지면 스크롤바 표시 */
}

.note-content {
  white-space: pre-wrap; /* 줄바꿈 및 공백 유지 */
  word-wrap: break-word; /* 긴 단어가 영역을 벗어나지 않도록 줄바꿈 */
  line-height: 1.4;
}

</style>