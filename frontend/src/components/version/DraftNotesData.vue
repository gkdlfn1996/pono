<template>
  <!-- 2단: Draft Notes 영역 -->
  <div class="d-flex flex-column h-100">
    <!-- My Draft Note 섹션 -->
    <div class="my-notes-section mb-4">
    <!-- <div style="height: 50%; display: flex; flex-direction: column; padding-bottom: 8px;"> -->
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
      <!-- 고정 높이 컨테이너 -->
      <div class="note-input-container" style="height: 150px;">
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
      <!-- 내 첨부파일 목록 (고정 높이 컨테이너 바깥으로 이동) -->
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
    <div class="other-notes-section">
    <!-- <div style="height: 50%; display: flex; flex-direction: column; padding-top: 8px;"> -->
      <div class="d-flex align-center mb-2">
        <h4 class="text-subtitle-1 font-weight-bold">Others Draft Notes</h4>
      </div>
      <v-card 
        variant="outlined" 
        class="notes-container"
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
            <!-- ================================================================== -->
            <!-- 다른 사람 노트 첨부파일 UI 예시 (첫 번째 노트에만 임시로 표시) -->
            <div v-if="index === 0" class="attachments-section ma-2 pa-2 rounded" style="border: 1px solid #E0E0E0;">
              <div class="text-caption font-weight-bold mb-1">첨부파일 (예시)</div>
              <div class="d-flex align-center text-caption">
                <v-icon size="small" class="mr-1">mdi-image</v-icon>
                <a href="#" target="_blank" class="text-decoration-none text-blue-lighten-2">design_reference_v01.jpg</a>
              </div>
            </div>
            <!-- ================================================================== -->
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
import AttachmentModal from '../layout/AttachmentModal.vue'; // AttachmentModal 임포트

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
const showAttachmentModal = ref(false); // 첨부파일 모달 표시 여부
const myAttachments = ref([]); // 내 첨부파일 임시 데이터 (type 추가)

// 임시 데이터 삭제 함수 (UI 테스트용)
const deleteMyAttachment = (index) => {
  myAttachments.value.splice(index, 1);
};

// 파일 이름으로 아이콘을 결정하는 헬퍼 함수
const getIconForFile = (fileName) => {
  if (!fileName) return 'mdi-link-variant'; // 이름이 없으면(URL의 경우) 링크 아이콘 반환
  const extension = fileName.split('.').pop().toLowerCase();
  if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(extension)) return 'mdi-image';
  if (['mov', 'mp4', 'avi', 'mkv'].includes(extension)) return 'mdi-filmstrip';
  if (['pdf'].includes(extension)) return 'mdi-file-pdf-box';
  if (['doc', 'docx'].includes(extension)) return 'mdi-file-word';
  if (['xls', 'xlsx'].includes(extension)) return 'mdi-file-excel';
  return 'mdi-file'; // 기본 아이콘
};

// AttachmentModal에서 'upload' 이벤트가 발생했을 때 실행되는 핸들러
const handleUploadFiles = (uploadData) => {
  console.log('업로드할 아이템:', uploadData);

  // 파일 처리
  uploadData.files.forEach(file => {
    myAttachments.value.push({ name: file.name, url: '#', type: 'file' });
  });

  // URL 처리
  uploadData.urls.forEach(url => {
    myAttachments.value.push({ name: url, url: url, type: 'url' });
  });
};

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

// 사용자가 노트를 직접 클릭했을 때 하이라이트를 즉시 제거하는 함수
const onNoteClick = (note) => {
  if (props.newNoteIds.has(note.id)) {
    props.clearNewNoteFlag(note.id);
  }
}

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
  }, { threshold: 0.5 });

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
