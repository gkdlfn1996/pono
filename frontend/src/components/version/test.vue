<template>
  <!-- 2단: Draft Notes 영역 -->
  <div class="d-flex flex-column h-100">
    <!-- My Draft Note 섹션 -->
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
      <!-- 동적 높이 컨테이너 -->
      <div class="note-input-container flex-grow-1" style="min-height: 150px;">
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
      <!-- 내 첨부파일 목록 -->
      <div v-if="myAttachments.length > 0" class="attachments-section mt-2 pa-2 rounded" style="border: 1px solid #E0E0E0;">
        <div class="text-caption font-weight-bold mb-1">첨부파일</div>
        <div v-for="(attachment, index) in myAttachments" :key="index" class="d-flex align-center text-caption">
          <v-icon size="small" class="mr-1">{{ getIconForFile(attachment.name) }}</v-icon>
          <a :href="attachment.url" target="_blank" class="text-decoration-none text-blue-lighten-2">{{ attachment.name }}</a>
          <v-spacer></v-spacer>
          <v-btn icon variant="text" size="x-small" color="grey" @click="deleteMyAttachment(index)">
            <v-icon>mdi-close-circle</v-icon>
          </v-btn>
        </div>
      </div>
    </div>

    <!-- Other's Draft Notes 섹션 -->
    <div class="other-notes-section d-flex flex-column flex-grow-1" style="min-height: 150px;">
      <div class="d-flex align-center mb-2">
        <h4 class="text-subtitle-1 font-weight-bold">Others Draft Notes</h4>
      </div>
      <v-card 
        variant="outlined" 
        class="notes-container flex-grow-1"
        style="min-height: 150px; overflow-y: auto;"
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
            <!-- 다른 사람 노트의 첨부파일 목록 -->
            <div v-if="note.attachments && note.attachments.length > 0" class="attachments-section ma-2 pa-2 rounded" style="border: 1px solid #E0E0E0;">
              <div class="text-caption font-weight-bold mb-1">첨부파일</div>
              <div v-for="(attachment, attIndex) in note.attachments" :key="attIndex" class="d-flex align-center text-caption">
                <v-icon size="small" class="mr-1">mdi-file</v-icon>
                <a :href="attachment.url" target="_blank" class="text-decoration-none text-blue-lighten-2">{{ attachment.name }}</a>
              </div>
            </div>
            <div class="d-flex justify-space-between align-center px-2 pt-2 pb-1">
              <span class="text-subtitle-2 text-grey-darken-1">{{ note.owner.username }} ({{ note.owner.login }})</span>
              <span class="text-caption text-right text-grey-darken-1">{{ formatDateTime(note.updated_at) }}</span>
            </div>
            <v-card-text class="note-content text-body-2 pa-2 pt-0">
              {{ note.content }}
            </v-card-text>
            <v-divider v-if="index < props.otherNotes.length - 1"></v-divider>
          </div>
        </template>
        <v-card-text v-else class="d-flex align-center justify-center fill-height">
          <p class="text-grey">다른 사용자의 노트가 없습니다.</p>
        </v-card-text>
      </v-card>
    </div>

    <!-- AttachmentModal 컴포넌트 -->
    <AttachmentModal
      v-model="showAttachmentModal"
      @upload="handleUploadFiles"
    />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';
import AttachmentModal from '../layout/AttachmentModal.vue';

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

// --- 첨부파일 관련 상태 및 함수 ---
const showAttachmentModal = ref(false);
const myAttachments = ref([]);

const deleteMyAttachment = (index) => {
  myAttachments.value.splice(index, 1);
};

const getIconForFile = (fileName) => {
  if (!fileName) return 'mdi-link-variant';
  const extension = fileName.split('.').pop().toLowerCase();
  if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(extension)) return 'mdi-image';
  if (['mov', 'mp4', 'avi', 'mkv'].includes(extension)) return 'mdi-filmstrip';
  if (['pdf'].includes(extension)) return 'mdi-file-pdf-box';
  if (['doc', 'docx'].includes(extension)) return 'mdi-file-word';
  if (['xls', 'xlsx'].includes(extension)) return 'mdi-file-excel';
  return 'mdi-file';
};

const handleUploadFiles = (uploadData) => {
  uploadData.files.forEach(file => {
    myAttachments.value.push({ name: file.name, url: '#', type: 'file' });
  });
  uploadData.urls.forEach(url => {
    myAttachments.value.push({ name: url, url: url, type: 'url' });
  });
};

const localContent = ref(props.myNote || '');
const isFocused = ref(false);
const noteRefs = ref({});
const visibleNoteIds = ref(new Set());
const timedNoteIds = new Set();
let observer = null;

watch(() => props.myNote, (newVal) => {
  if (isFocused.value) return;
  if (newVal !== localContent.value) {
    localContent.value = newVal || '';
  }
});

const onInput = (value) => {
  localContent.value = value;
  props.debouncedSave(props.version, value);
};

const onBlur = () => {
  isFocused.value = false;
  props.saveNote(props.version, localContent.value);
};

const onNoteClick = (note) => {
  if (props.newNoteIds.has(note.id)) {
    props.clearNewNoteFlag(note.id);
  }
};

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

onMounted(() => {
  setupObserver();
});

onBeforeUnmount(() => {
  if (observer) observer.disconnect();
});

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
  }).replace(/\\.\\s/g, '.');
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

/* My Draft Note 저장 시각 피드백 */
:deep(.v-textarea.saved-note .v-field__field) {
  background-color: #E3F2FD;
}

.new-note-highlight {
  background-color: #FFF9C4;
}
</style>
