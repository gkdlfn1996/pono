<template>
  <!-- 2단: Draft Notes 영역 -->
  <div class="d-flex flex-column h-100">
    <!-- My Draft Note -->
    <div class="d-flex flex-column" style="flex-basis: 50%; padding-bottom: 8px;">
      <h4 class="text-subtitle-1 font-weight-bold mb-2">My Draft Note</h4>
      <v-textarea
        label="여기에 노트를 작성하세요"
        :model-value="props.myNote"
        @update:model-value="onInput"
        @blur="onBlur"
        variant="outlined"
        :class="{ 'saving-note': props.isSaving }"
        class="flex-grow-1"
        no-resize
        rows="1"
      ></v-textarea>
    </div>

    <!-- Other's Draft Notes -->
    <div class="d-flex flex-column" style="flex-basis: 50%; padding-top: 8px;">
      <div class="d-flex align-center mb-2">
        <h4 class="text-subtitle-1 font-weight-bold">Others Draft Notes</h4>
      </div>
      <v-card variant="outlined" class="notes-container flex-grow-1 d-flex flex-column">
        <template v-if="props.otherNotes && props.otherNotes.length">
          <div 
            v-for="(note, index) in props.otherNotes" 
            :key="note.id" 
            :ref="el => noteRefs[note.id] = el"
            :data-note-id="note.id"
            :class="{ 'new-note-highlight': props.newNoteIds.has(note.id) }"
          >
            <div class="d-flex justify-space-between align-center px-2 pb-1">
              <span class="text-subtitle-2 text-grey-darken-1">{{ note.owner.username }}</span>
              <span class="text-caption text-right text-grey-darken-1">{{ formatDateTime(note.updated_at) }}</span>
            </div>
            <v-card-text class="note-content text-body-2 pa-2">
              {{ note.content }}
            </v-card-text>
            <v-divider v-if="index < props.otherNotes.length - 1"></v-divider>
          </div>
        </template>
        <v-card-text v-else class="d-flex align-center justify-center flex-grow-1">
          <p class="text-grey">다른 사용자의 노트가 없습니다.</p>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';

const props = defineProps({
  version: { type: Object, required: true },
  myNote: String,
  otherNotes: Array,
  isSaving: Boolean,
  newNoteIds: Set,
  saveNote: Function,
  debouncedSave: Function,
  clearNewNoteFlag: Function,
});

const localContent = ref(props.myNote || '');
const noteRefs = ref({});
let observer = null;

// Prop이 외부에서 변경될 때, 내부 상태도 업데이트합니다.
watch(() => props.myNote, (newVal) => {
  localContent.value = newVal || '';
});

// 사용자가 입력할 때마다 내부 상태를 업데이트하고, 디바운스 저장 함수를 호출합니다.
const onInput = (value) => {
  localContent.value = value;
  props.debouncedSave(props.version, value);
};

// 포커스를 잃었을 때 즉시 저장 함수를 호출합니다.
const onBlur = () => {
  props.saveNote(props.version, localContent.value);
};

/**
 * IntersectionObserver를 설정하여, 노트 요소가 화면에 보이면
 * 하이라이트를 제거하는 로직을 수행합니다.
 */
const setupObserver = () => {
  if (observer) observer.disconnect();

  observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const noteId = parseInt(entry.target.dataset.noteId);
        if (props.newNoteIds.has(noteId)) {
          props.clearNewNoteFlag(noteId);
        }
      }
    });
  }, { threshold: 0.8 });

  // 현재 렌더링된 모든 노트 DOM 요소를 관찰 대상으로 추가합니다.
  Object.values(noteRefs.value).forEach(el => {
    if (el) observer.observe(el);
  });
};

// 컴포넌트가 마운트되면 Observer를 설정합니다.
onMounted(() => {
  setupObserver();
});

// 컴포넌트가 파괴되기 전에 Observer 연결을 해제합니다.
onBeforeUnmount(() => {
  if (observer) observer.disconnect();
});

// 다른 사람의 노트 목록이 변경될 때마다, 관찰 대상을 다시 설정합니다.
watch(() => props.otherNotes, () => {
  nextTick(() => {
    setupObserver();
  });
}, { deep: true });


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
}
.note-content {
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.4;
}
.saving-note {
  background-color: #E3F2FD; /* 연한 파란색으로 저장 중 표시 */
  transition: background-color 0.2s ease-in-out;
}
.new-note-highlight {
  background-color: #FFF9C4; /* 연한 노란색으로 새 노트 표시 */
  transition: background-color 0.5s ease;
}
</style>
