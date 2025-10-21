<template>
  <!-- 
    v-dialog: Vuetify의 모달 컴포넌트. 
    v-model 바인딩을 통해 부모 컴포넌트에서 모달의 표시 여부를 제어합니다.
  -->
  <v-dialog :model-value="modelValue" @update:model-value="close" max-width="800px">
    <v-card>
      <v-card-title class="d-flex justify-space-between align-center">
        <span>Publish Note</span>
        <v-btn icon="mdi-close" variant="text" @click="close"></v-btn>
      </v-card-title>
      <v-divider></v-divider>

      <v-card-text>
        <p class="text-caption text-medium-emphasis mb-4">
          이 노트는 ShotGrid에 게시(Publish)될 최종본입니다. 내용을 마지막으로 확인하고 정리해 주세요.
        </p>

        <!-- 
          가짜 입력창 (Fake Textarea) 구현부.
          실제로는 div이지만, CSS를 통해 textarea처럼 보이게 만듭니다.
          클릭 시 실제 textarea에 포커스를 주기 위해 @click 이벤트를 사용합니다.
        -->
        <div
          class="fake-textarea-container"
          :class="{ 'v-field--focused': isFocused }"
          @click="focusTextarea"
        >
          <!-- 1. 헤더/서브젝트 오버레이 -->
          <!-- 
            localStorage에서 읽어온 헤더/서브젝트 텍스트를 표시하는 읽기 전용 영역.
            v-if를 통해 내용이 있을 때만 렌더링됩니다.
          -->
          <div v-if="currentSubject || currentHeaderNote" class="overlay-content">
            <p v-if="currentSubject" class="font-weight-bold ma-0">{{ currentSubject }}</p>
            <p v-if="formattedHeader" class="ma-0">{{ formattedHeader }}</p>
          </div>

          <!-- 2. 투명한 실제 입력창 -->
          <!-- 
            variant="plain"으로 테두리와 배경을 없앤 실제 v-textarea.
            사용자의 입력은 이 컴포넌트가 처리합니다.
          -->
          <v-textarea
            ref="textareaRef"
            v-model="internalContent"
            @focus="isFocused = true"
            @blur="isFocused = false"
            variant="plain"
            no-resize
            hide-details
            class="real-textarea"
          ></v-textarea>
        </div>
        
        <!-- 첨부파일 목록 -->
        <AttachmentHandler 
          class="mt-4"
          :attachments="attachments"
          @delete-attachment="attachmentId => deleteAttachmentFn(attachmentId)"
        />

      </v-card-text>

      <v-card-actions class="pa-4">
        <v-spacer></v-spacer>
        <v-btn @click="close" variant="text">Cancel</v-btn>
        <v-btn color="primary" variant="flat">PUBLISH</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
/**
 * @file PublishNoteModal.vue
 * @description 개별 노트를 ShotGrid에 게시하기 전, 최종 내용을 확인하고 편집하는 모달.
 */
import { ref, watch, onMounted, onBeforeUnmount, computed } from 'vue';
import { useAuth } from '@/composables/useAuth.js';
import AttachmentHandler from './draftnote_attachments/AttachmentHandler.vue';

// modelValue: v-model을 통해 모달의 열림/닫힘 상태를 제어.
// noteContent: 부모 컴포넌트의 노트 내용을 표시하고 동기화.
const props = defineProps({
  modelValue: Boolean,
  noteContent: String,
  version: Object,
  attachments: Array,
  deleteAttachmentFn: Function,
});

// 'update:modelValue': 모달을 닫을 때 부모의 v-model 상태를 업데이트.
// 'update:noteContent': 노트 내용이 변경될 때 부모의 상태를 업데이트.
const emit = defineEmits(['update:modelValue', 'update:noteContent']);

// --- 상태 변수 (State Variables) ---
const isFocused = ref(false); // '가짜 입력창'의 포커스 상태 (테두리 색상 변경용)
const textareaRef = ref(null); // 실제 v-textarea 엘리먼트를 참조하기 위함.
const currentSubject = ref(''); // localStorage에서 불러온 서브젝트.
const currentHeaderNote = ref(''); // localStorage에서 불러온 헤더 노트.
const internalContent = ref(''); // 커서 점프 버그 방지를 위한 내부 컨텐츠 상태

// --- 함수 (Functions) ---

// 모달을 닫는 함수.
const close = () => {
  emit('update:noteContent', internalContent.value); // 닫힐 때 최종 컨텐츠를 전달
  emit('update:modelValue', false);
};

// '가짜 입력창' 컨테이너를 클릭했을 때, 실제 textarea에 포커스를 주는 함수.
const focusTextarea = () => {
  textareaRef.value?.focus();
};

// --- 데이터 로딩 및 생명주기 (Data Loading & Lifecycle) ---

// 이 컴포넌트가 자체적으로 헤더/서브젝트 데이터를 관리하기 위한 로직.
const { user } = useAuth();
const userSpecificStorageKey = computed(() => {
  return user.value?.login ? `pono-header-${user.value.login}` : null;
});

// localStorage에서 데이터를 읽어와 상태 변수를 업데이트하는 함수.
const loadHeaderData = () => {
  if (!userSpecificStorageKey.value) return;
  const savedData = localStorage.getItem(userSpecificStorageKey.value);
  if (savedData) {
    const { subject, headerNote } = JSON.parse(savedData);
    currentSubject.value = subject || '';
    currentHeaderNote.value = headerNote || '';
  } else {
    currentSubject.value = '';
    currentHeaderNote.value = '';
  }
};

// 헤더 포맷을 동적으로 생성하는 computed 속성
const formattedHeader = computed(() => {
  if (!currentHeaderNote.value) return '';

  const parts = props.version?.code?.split('_');
  if (parts && parts.length >= 4) {
    const task = parts[2];
    const verNum = parts[3];
    // headerNote가 비어있지 않을 때만 포맷을 적용
    return `${currentHeaderNote.value}_${task}_${verNum}_`;
  }

  // 버전 이름 포맷이 맞지 않으면 그냥 헤더 노트만 반환
  return currentHeaderNote.value;
});


// 컴포넌트가 처음 마운트될 때, 그리고 다른 곳에서 헤더가 수정되었을 때 데이터를 불러옵니다.
onMounted(() => {
  loadHeaderData();
  window.addEventListener('pono-header-updated', loadHeaderData);
});

// 컴포넌트가 파괴될 때 이벤트 리스너를 정리하여 메모리 누수를 방지합니다.
onBeforeUnmount(() => {
  window.removeEventListener('pono-header-updated', loadHeaderData);
});
// ---

// 모달이 열릴 때마다 최신 데이터를 다시 로드하고, textarea에 자동으로 포커스를 줍니다.
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    internalContent.value = props.noteContent || ''; // 모달이 열릴 때 부모 컨텐츠로 초기화
    loadHeaderData();
    setTimeout(() => textareaRef.value?.focus(), 100); // DOM 렌더링 후 포커스
  }
});
</script>

<style scoped>
/* 
  가짜 입력창의 기본 컨테이너 스타일.
  - position: relative -> 내부 오버레이의 기준점 역할.
  - border, border-radius -> v-textarea의 'outlined' 스타일 흉내.
  - height, overflow-y -> 고정 높이와 내부 스크롤 구현.
  - cursor: text -> 사용자가 텍스트 입력 영역임을 인지하도록 함.
*/
.fake-textarea-container {
  border: 1px solid rgba(0, 0, 0, 0.22);
  border-radius: 4px;
  height: 300px;
  padding: 16px;
  cursor: text;
  transition: border-color 0.15s ease-in-out;
  /* Flexbox 레이아웃으로 변경 */
  display: flex;
  flex-direction: column;
}

/* 마우스를 올렸을 때 테두리 색상을 약간 진하게 변경 */
.fake-textarea-container:hover {
  border-color: rgba(0, 0, 0, 0.54);
}

/* 
  포커스 상태일 때의 스타일.
  Vuetify의 기본 포커스 스타일(파란색, 2px 테두리)을 모방합니다.
*/
.fake-textarea-container.v-field--focused {
  border-color: rgb(var(--v-theme-primary));
  border-width: 2px;
}

/* 
  헤더/서브젝트를 표시하는 오버레이 스타일.
  - pointer-events: none -> 이 div가 마우스 이벤트를 가로채지 않아, 사용자가 이 위를 클릭해도 뒷쪽의 textarea가 클릭된 것처럼 동작하게 함.
  - white-space, word-wrap -> 원본 텍스트의 줄바꿈과 긴 단어를 올바르게 표시.
*/
.overlay-content {
  color: rgba(0, 0, 0, 0.54);
  pointer-events: none;
  white-space: pre-wrap;
  word-wrap: break-word;
  /* 간격 축소 */

  /* 컨텐츠가 많아져도 스스로 줄어들지 않도록 설정 */
  flex-shrink: 0;
}

/* 실제 입력되는 텍스트의 커서 색상을 지정 */
.real-textarea {
  caret-color: rgba(0, 0, 0, 0.87);
  /* 남은 공간을 모두 채우도록 설정 */
  flex-grow: 1;
}

/* 
  :deep() 선택자: scoped style의 한계를 넘어 자식 컴포넌트의 내부 스타일을 수정.
  v-textarea의 variant="plain" 모드에서 불필요하게 적용되는 내부 padding을 제거하여
  '가짜 입력창'의 padding과 일치시킵니다.
*/
:deep(.real-textarea .v-field),
:deep(.real-textarea .v-field__field) {
  padding: 0 !important;
  height: 100%;
}
</style>
