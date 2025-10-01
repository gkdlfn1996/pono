<template>
  <!-- 2단: Draft Notes 영역 -->
  <div class="d-flex flex-column h-100">
    <div class="my-notes-section mb-4 d-flex flex-column flex-grow-1" style="min-height: 150px;">
      <div class="d-flex align-center mb-2">
        <h4 class="text-subtitle-1 font-weight-bold">My Draft Note</h4>
        <v-spacer></v-spacer>
        <v-btn
        icon="mdi-paperclip"
        variant="text"
        size="small"
        @click="showAttachmentModal = true"
        density="compact"
      ></v-btn>
    </div>
    <div class="note-input-container flex-grow-1" style="height: 150px;">
      <v-textarea
      label="여기에 노트를 작성하세요"
      :model-value="localContent"
      @update:model-value="onInput"
          @focus="isFocused = true"
          @blur="onBlur"
          variant="outlined"
          :class="{ 'saved-note': props.isSaved }"
          no-resize
          class="fill-height"
          ></v-textarea>
        </div>
        <AttachmentHandler
        :attachments="myNoteAttachments"
        @delete-attachment="handleDeleteAttachment"
        />
    </div>

    <!-- AttachmentModal 컴포넌트 -->
    <AttachmentModal
      v-model="showAttachmentModal"
      @upload="handleUploadFiles"
    />

    <!-- Other's Draft Notes 섹션 -->
    <div class="other-notes-section d-flex flex-column flex-grow-1" style="min-height: 150px;">
      <div class="d-flex align-center mb-2">
        <h4 class="text-subtitle-1 font-weight-bold">Others Draft Notes</h4>
      </div>
      <v-card
        variant="outlined"
        class="notes-container flex-grow-1"
        style="height: 150px; overflow-y: auto;"
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
            @click="onNoteClick(note)"
          >
            <div class="d-flex justify-space-between align-center px-2 pt-2 pb-1">
              <span class="text-subtitle-2 text-grey-darken-1">{{ note.owner.username }} ({{ note.owner.login }})</span>
              <span class="text-caption text-right text-grey-darken-1">{{ formatDateTime(note.updated_at) }}</span>
            </div>
            <v-card-text class="note-content text-body-2 pa-2 pt-0">
              {{ note.content }}
            </v-card-text>
            <!-- 다른 사람 노트의 첨부파일 목록 -->
            <div class="ma-2">
            <AttachmentHandler v-if="note.attachments && note.attachments.length > 0" :attachments="note.attachments" readonly />
            </div>
            <v-divider v-if="index < props.otherNotes.length - 1"></v-divider>
          </div>
        </template>
        <v-card-text v-else class="d-flex align-center justify-center fill-height">
          <p class="text-grey">다른 사용자의 노트가 없습니다.</p>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script setup>
/**
 * @file DraftNotesData.vue
 * @description 개별 버전 카드 내의 Draft Note 영역 전체를 담당하는 컴포넌트.
 *              내 노트, 다른 사람 노트, 첨부파일 등 하위 컴포넌트를 포함하고 데이터를 전달하는 컨테이너 역할을 합니다.
 */
import { ref, watch, onMounted, onBeforeUnmount, nextTick, computed } from 'vue';
import AttachmentHandler from './draftnote_attachments/AttachmentHandler.vue';
import AttachmentModal from './draftnote_attachments/AttachmentModal.vue';
import { useAttachments } from '@/composables/useAttachments.js';

/**
 * @props {Object} version - 현재 버전 정보.
 * @props {Object} myNote - 현재 사용자의 노트 정보.
 * @props {Array} otherNotes - 다른 사용자들의 노트 정보 배열.
 * @props {Boolean} isSaved - 내 노트의 저장 상태 (시각적 피드백용).
 * @props {Set} newNoteIds - 새로 수신된 다른 사람 노트 ID 집합 (하이라이트용).
 * @props {Function} saveNote - 노트를 즉시 저장하는 함수.
 * @props {Function} debouncedSave - 노트를 디바운스하여 저장하는 함수.
 * @props {Function} clearNewNoteFlag - 새 노트 하이라이트를 제거하는 함수.
 * @props {Function} uploadAttachments - 첨부파일을 업로드하는 함수.
 * @props {Function} deleteAttachment - 첨부파일을 삭제하는 함수.
 */
const props = defineProps({
  version: { type: Object, required: true },
  myNote: Object,
  otherNotes: Array,
  isSaved: Boolean,
  newNoteIds: Set,
  saveNote: Function,
  debouncedSave: Function,
  clearNewNoteFlag: Function,
  uploadAttachments: Function,
  deleteAttachment: Function,
});

// 첨부파일 관련 로직과 상태를 가져옵니다.
const { getIconForFile, handleAttachmentClick } = useAttachments();

// 첨부파일 모달의 표시 여부를 제어하는 상태.
const showAttachmentModal = ref(false);

/**
 * 내 노트에 속한 첨부파일 목록을 계산하는 속성.
 * @returns {Array} 첨부파일 객체 배열.
 */
const myNoteAttachments = computed(() => props.myNote?.attachments || []);

/**
 * 첨부파일 모달에서 'upload' 이벤트 발생 시, 부모로부터 받은 함수를 호출합니다.
 * @param {Object} uploadData - { files: File[], urls: string[] } 형태의 업로드 데이터.
 */
const handleUploadFiles = (uploadData) => {
  props.uploadAttachments(props.version, uploadData);
};

/**
 * 첨부파일 삭제 버튼 클릭 시, 부모로부터 받은 함수를 호출합니다.
 * @param {number} attachmentId - 삭제할 첨부파일의 ID.
 */
const handleDeleteAttachment = (attachmentId) => {
  props.deleteAttachment(attachmentId);
};

// 내 노트 입력창의 내부 콘텐츠 상태.
const localContent = ref(props.myNote?.content || '');
// 내 노트 입력창의 포커스 여부 상태.
const isFocused = ref(false);
// 다른 사람 노트 목록의 DOM 요소를 참조하기 위한 객체.
const noteRefs = ref({});
// 현재 화면에 보이는 다른 사람 노트의 ID를 추적하는 Set.
const visibleNoteIds = ref(new Set());
// 하이라이트 제거 타이머의 중복 생성을 방지하기 위한 Set.
const timedNoteIds = new Set();
// IntersectionObserver 인스턴스.
let observer = null;

/**
 * 외부 (웹소켓 등)에서 내 노트 정보가 변경될 때, UI를 업데이트합니다.
 * 단, 사용자가 현재 입력 중(포커스 상태)일 때는 외부 데이터로 덮어쓰지 않습니다.
 */
watch(() => props.myNote, (newNote) => {
  const newContent = newNote?.content || '';
  if (isFocused.value) {
    return;
  }
  if (newContent !== localContent.value) {
    localContent.value = newContent;
  }
}, { deep: true });

/**
 * 사용자가 내 노트 입력창에 타이핑할 때마다 호출됩니다.
 * @param {string} value - 입력창의 현재 텍스트.
 */
const onInput = (value) => {
  localContent.value = value;
  props.debouncedSave(props.version, value);
};

/**
 * 사용자가 내 노트 입력창에서 포커스를 잃었을 때 호출됩니다.
 */
const onBlur = () => {
  isFocused.value = false;
  props.saveNote(props.version, localContent.value);
};

/**
 * 다른 사람 노트를 클릭했을 때, 해당 노트의 하이라이트를 즉시 제거합니다.
 * @param {object} note - 클릭된 노트 객체.
 */
const onNoteClick = (note) => {
  if (props.newNoteIds.has(note.id)) {
    props.clearNewNoteFlag(note.id);
  }
}

/**
 * 다른 사람 노트 목록 영역에서 스크롤이나 클릭 등 상호작용이 발생했을 때 호출됩니다.
 * 화면에 보이는 새 노트의 하이라이트를 일정 시간 후 제거합니다.
 */
const handleInteraction = () => {
  const notesToTime = (props.otherNotes || []).filter(
    note =>
      visibleNoteIds.value.has(note.id) &&
      props.newNoteIds.has(note.id) &&
      !timedNoteIds.has(note.id)
  );

  notesToTime.forEach(note => {
    timedNoteIds.add(note.id);
    setTimeout(() => {
      props.clearNewNoteFlag(note.id);
      timedNoteIds.delete(note.id);
    }, 500);
  });
};

/**
 * IntersectionObserver를 설정하여, 다른 사람 노트가 화면에 보이는지 여부를 감시합니다.
 */
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
  }, { threshold: 0.5 });
  Object.values(noteRefs.value).forEach(el => {
    if (el) observer.observe(el);
  });
};

// 컴포넌트가 마운트될 때 Observer를 설정합니다.
onMounted(() => {
  setupObserver();
});

// 컴포넌트가 파괴되기 전에 Observer 연결을 해제합니다.
onBeforeUnmount(() => {
  if (observer) observer.disconnect();
});

/**
 * 다른 사람 노트 목록이 변경될 때마다, Observer가 감시할 대상을 다시 설정합니다.
 */
watch(() => props.otherNotes, () => {
  nextTick(() => {
    setupObserver();
  });
}, { deep: true });

/**
 * ISO 8601 형식의 날짜 문자열을 'YYYY.MM.DD. HH:MM' 형식으로 변환합니다.
 * @param {string} isoString - 변환할 날짜 문자열.
 * @returns {string} 포맷팅된 날짜 문자열.
 */
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

/* My Draft Note 변경사항 저장 시각 피드백  */
:deep(.v-textarea.saved-note .v-field__field) {
  background-color: #E3F2FD;
}

.new-note-highlight {
  background-color: #FFF9C4; /* 연한 노란색으로 새 노트 표시 */
}
</style>