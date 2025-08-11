<template>
  <!-- 2단: Draft Notes 영역 -->
  <div class="d-flex flex-column h-100">
    <!-- My Draft Note -->
    <div class="d-flex flex-column" style="flex-basis: 50%; padding-bottom: 8px;">
      <h4 class="text-subtitle-1 font-weight-bold mb-2">My Draft Note</h4>
      <!-- 노트 기능 비활성화된 v-textarea -->
      <v-textarea
        label="노트 기능 비활성화"
        variant="outlined"
        disabled
        class="flex-grow-1"
        no-resize
        rows="1"
      ></v-textarea>
      <!-- 주석 해제된 v-textarea (원래 VersionCard.vue에 있던 코드) -->
      <!-- <v-textarea
        label="여기에 노트를 작성하세요"
        v-model="localNotesContent[version.id]"
        @input="emit('input-note', version.id, localNotesContent[version.id])"
        @blur="emit('save-note', version.id, localNotesContent[version.id])"
        variant="outlined"
        :class="{ 'saving-note': !!isSaving[version.id] }"
      ></v-textarea> -->
    </div>

    <!-- Other's Draft Notes -->
    <div class="d-flex flex-column" style="flex-basis: 50%; padding-top: 8px;">
      <div class="d-flex align-center mb-2">
        <h4 class="text-subtitle-1 font-weight-bold">Others Draft Notes</h4>
        <!-- 주석 해제된 v-btn (원래 VersionCard.vue에 있던 코드) -->
        <!-- <v-btn
          icon="mdi-refresh"
          size="small"
          variant="text"
          :color="notesComposable.hasNewOtherNotes.value[version.id] ? 'red' : ''" @click="emit('reload-other-notes', version.id)"></v-btn> -->
      </div>
      <v-card variant="outlined" class="notes-container flex-grow-1 d-flex flex-column">
        <!-- 주석 해제된 otherNotes 템플릿 (원래 VersionCard.vue에 있던 코드) -->
        <!-- <template v-if="notesComposable.otherNotes.value[version.id] && notesComposable.otherNotes.value[version.id].length">
          <div v-for="(note, index) in notesComposable.otherNotes.value[version.id]" :key="note.id">
            <div class="d-flex justify-space-between align-center px-2 pb-1">
              <span class="text-subtitle-2 text-grey-darken-1">{{ note.owner.username }}</span>
              <span class="text-caption text-right text-grey-darken-1">{{ formatDateTime(note.updated_at) }}</span>
            </div>
            <v-card-text class="note-content text-body-2 pa-2">
              {{ note.content }}
            </v-card-text>
            <v-divider v-if="index < notesComposable.otherNotes.value[version.id].length - 1"></v-divider>
          </div>
        </template>
        <v-card-text v-else> -->
          <p class="text-grey pa-4 text-center">다른 사용자의 노트가 없습니다.</p>
        <!-- </v-card-text> -->
      </v-card>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  version: {
    type: Object,
    required: true,
  },
});

// const emit = defineEmits(['save-note', 'input-note', 'reload-other-notes']);
// const localNotesContent = ref({});

// watch(() => props.notes, (newNotes) => {
//   localNotesContent.value = { ...newNotes };
// }, { immediate: true, deep: true });


// 필요한 경우 formatDateTime 함수를 여기에 추가하거나, 공통 유틸리티 파일에서 가져옵니다.
const formatDateTime = (isoString) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleString('ko-KR', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false
  }).replace(/\.\s/g, '.').slice(0, -1);
};
</script>

<style scoped>
.notes-container {
  overflow-y: auto;
}
.note-content {
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.4;
}
</style>