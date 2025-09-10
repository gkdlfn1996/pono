<template>
  <!-- 2단: Draft Notes 영역 -->
  <div class="d-flex flex-column h-100">
    <!-- My Draft Note -->
    <div class="d-flex flex-column" style="flex-basis: 50%; padding-bottom: 8px;">
      <h4 class="text-subtitle-1 font-weight-bold mb-2">My Draft Note</h4>
      <v-textarea
        label="여기에 노트를 작성하세요"
        :model-value="localContent"
        @update:model-value="onInput"
        @focus="isFocused = true"
        @blur="onBlur"
        variant="outlined"
        :class="{ 'saved-note': props.isSaved }"
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
      <v-card 
        variant="outlined" 
        class="notes-container flex-grow-1 d-flex flex-column"
        @click="handleInteraction"
        @scroll.passive="handleInteraction"
        :ripple="false"
      >
        <template v-if="props.otherNotes && props.otherNotes.length">
          <div 
            v-for="(note, index) in props.otherNotes" 
            :key="note.id" 
            :ref="el => noteRefs[note.id] = el"
            :data-note-id="note.id"
            class="note-item"
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
  isSaved: Boolean,
  newNoteIds: Set,
  saveNote: Function,
  debouncedSave: Function,
  clearNewNoteFlag: Function,
});

const localContent = ref(props.myNote || '');
const isFocused = ref(false); // 사용자가 입력창에 포커스 중인지 추적하는 상태
const noteRefs = ref({});
const visibleNoteIds = ref(new Set()); // 현재 화면에 보이는 노트 ID를 추적
const timedNoteIds = new Set(); // 중복 타이머 생성을 방지하기 위한 Set
let observer = null;

// Prop(myNote)이 외부(웹소켓 등)에서 변경될 때, 내부 상태(localContent)도 업데이트합니다.
watch(() => props.myNote, (newVal) => {
  // 사용자가 현재 입력 중(포커스 상태)이라면, 외부 데이터로 덮어쓰지 않고 무시합니다.
  if (isFocused.value) {
    return;
  }
  // 포커스 상태가 아닐 때만, 외부 데이터와 내부 데이터가 다를 경우 동기화합니다.
  if (newVal !== localContent.value) {
    localContent.value = newVal || '';
  }
});

// 사용자가 입력할 때마다 내부 상태를 업데이트하고, 디바운스 저장 함수를 호출합니다.
const onInput = (value) => {
  localContent.value = value;
  props.debouncedSave(props.version, value);
};

// 포커스를 잃었을 때, 포커스 상태를 false로 바꾸고 즉시 저장 함수를 호출합니다.
const onBlur = () => {
  isFocused.value = false;
  props.saveNote(props.version, localContent.value);
};

const handleInteraction = () => {
  // 현재 화면에 보이면서, 하이라이트 상태이고, 아직 타이머가 설정되지 않은 노트들을 찾습니다.
  const notesToTime = (props.otherNotes || []).filter(
    note => 
      visibleNoteIds.value.has(note.id) &&
      props.newNoteIds.has(note.id) && 
      !timedNoteIds.has(note.id)
  );

  notesToTime.forEach(note => {
    // 타이머가 설정되었음을 기록하여 중복 실행을 방지합니다.
    timedNoteIds.add(note.id);

    // 3초 후에 하이라이트를 제거합니다.
    setTimeout(() => {
      props.clearNewNoteFlag(note.id);
      timedNoteIds.delete(note.id);
    }, 500);
  });
};

// IntersectionObserver를 설정하여, 노트 요소가 화면에 보이는지 여부를 감시합니다.
const setupObserver = () => {
  if (observer) observer.disconnect();

  observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      const noteId = parseInt(entry.target.dataset.noteId);
      if (entry.isIntersecting) {
        visibleNoteIds.value.add(noteId);
      } else {
        visibleNoteIds.value.delete(noteId);
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
  cursor: default;
  overflow-y: auto;
}
.note-content {
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.4;
}
.note-item {
  background-color: transparent;
  transition: background-color 0.3s ease-in-out;
}

:deep(.v-textarea .v-field__field) {
  transition: background-color 0.3s ease-in-out;
}

/* My Draft Note 변경사항 저장 시각 피드백  */
:deep(.v-textarea.saved-note .v-field__field) {
  background-color: #E3F2FD; /* 연한 파란색 배경 */
}


.new-note-highlight {
  background-color: #FFF9C4; /* 연한 노란색으로 새 노트 표시 */
}


</style>
