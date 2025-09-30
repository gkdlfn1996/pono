<template>
  <v-dialog
    :model-value="modelValue"
    @update:modelValue="emit('update:modelValue', $event)"
    max-width="600px"
    persistent
  >
    <v-card>
      <v-card-title class="d-flex justify-space-between align-center">
        <span class="text-h5">Add Attachments</span>
        <v-btn variant="text" icon @click="closeModal">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      <v-card-text>
        <v-container>
          <v-row>
            <v-col cols="12">
              <v-file-input
                label="여기에 파일을 드래그 앤 드롭하거나 클릭하여 선택하세요"
                counter
                multiple
                show-size
                prepend-icon="mdi-paperclip"
                variant="outlined"
                density="compact"
                :clearable="true"
                @change="handleFileSelection"
              >
                <template v-slot:selection="{ fileNames }">
                  <v-chip
                    v-for="(file, index) in selectedFiles"
                    :key="index"
                    class="me-2"
                    size="small"
                    color="primary"
                  >
                    {{ file.name }}
                  </v-chip>
                </template>
              </v-file-input>
            </v-col>
          </v-row>
          
          <v-divider class="my-4"></v-divider>

          <v-row>
            <v-col cols="12">
              <v-text-field
                label="URL/경로를 입력하세요"
                v-model="urlInput"
                prepend-icon="mdi-link-variant"
                variant="outlined"
                density="compact"
                hide-details
                @keydown.enter.prevent="addUrl"
              ></v-text-field>
            </v-col>
          </v-row>
          <v-row>
            <v-col class="text-right">
              <v-btn @click="addUrl" :disabled="!urlInput">Add</v-btn>
            </v-col>
          </v-row>

          <!-- 파일 및 URL 목록 통합 표시 -->
          <v-row v-if="selectedFiles.length > 0 || addedUrls.length > 0">
            <v-col cols="12">
              <v-list density="compact">
                <v-list-subheader>Items to Attach</v-list-subheader>
                <!-- 선택된 파일 목록 -->
                <v-list-item
                  v-for="(file, index) in selectedFiles"
                  :key="index"
                >
                  <template v-slot:prepend>
                    <v-icon>{{ getIconForFile(file.name) }}</v-icon>
                  </template>
                  <v-list-item-title>{{ file.name }}</v-list-item-title>
                  <v-list-item-subtitle>{{ (file.size / 1024 / 1024).toFixed(2) }} MB</v-list-item-subtitle>
                  <template v-slot:append>
                    <v-btn icon variant="text" size="small" @click="removeFile(index)">
                      <v-icon>mdi-close-circle</v-icon>
                    </v-btn>
                  </template>
                </v-list-item>
                <!-- 추가된 URL 목록 -->
                <v-list-item
                  v-for="(url, index) in addedUrls"
                  :key="`url-${index}`"
                >
                  <template v-slot:prepend>
                    <v-icon>mdi-link-variant</v-icon>
                  </template>
                  <v-list-item-title class="text-truncate">{{ url }}</v-list-item-title>
                  <template v-slot:append>
                    <v-btn icon variant="text" size="small" @click="removeUrl(index)">
                      <v-icon>mdi-close-circle</v-icon>
                    </v-btn>
                  </template>
                </v-list-item>
              </v-list>
            </v-col>
          </v-row>
        </v-container>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="blue-darken-1" variant="text" @click="closeModal">
          Cancel
        </v-btn>
        <v-btn color="blue-darken-1" variant="elevated" :disabled="isUploadDisabled" @click="uploadItems">
          Attach
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue';

const props = defineProps({
  modelValue: Boolean, // 모달의 열림/닫힘 상태를 제어
});

const emit = defineEmits(['update:modelValue', 'upload']);

const selectedFiles = ref([]);
const urlInput = ref('');
const addedUrls = ref([]);

// 파일 선택 input에서 파일이 선택되었을 때
const handleFileSelection = (event) => {
  // 새로 선택된 파일을 기존 목록에 누적하여 추가합니다.
  const newFiles = Array.from(event.target.files);
  selectedFiles.value.push(...newFiles);
};

// 파일 이름으로 아이콘을 결정하는 헬퍼 함수
const getIconForFile = (fileName) => {
  const extension = fileName.split('.').pop().toLowerCase();
  if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(extension)) return 'mdi-image';
  if (['mov', 'mp4', 'avi', 'mkv'].includes(extension)) return 'mdi-filmstrip';
  if (['pdf'].includes(extension)) return 'mdi-file-pdf-box';
  if (['doc', 'docx'].includes(extension)) return 'mdi-file-word';
  if (['xls', 'xlsx'].includes(extension)) return 'mdi-file-excel';
  return 'mdi-file'; // 기본 아이콘
};

// 선택된 파일 목록에서 파일 제거
const removeFile = (index) => {
  selectedFiles.value.splice(index, 1);
};

// URL 입력 필드에서 '추가' 버튼을 누르거나 Enter 키를 눌렀을 때
const addUrl = () => {
  if (urlInput.value.trim()) {
    addedUrls.value.push(urlInput.value.trim());
    urlInput.value = ''; // 입력 필드 초기화
  }
};

// 추가된 URL 목록에서 URL 제거
const removeUrl = (index) => {
  addedUrls.value.splice(index, 1);
};

// 업로드 버튼 활성화 여부를 계산하는 computed 속성
const isUploadDisabled = computed(() => {
  return selectedFiles.value.length === 0 && addedUrls.value.length === 0;
});

// '업로드' 버튼 클릭 시
const uploadItems = () => {
  if (!isUploadDisabled.value) {
    emit('upload', {
      files: selectedFiles.value,
      urls: addedUrls.value,
    });
    closeModal();
  }
};

// 모달을 닫고 모든 상태를 초기화하는 함수
const closeModal = () => {
  emit('update:modelValue', false);
};

// 모달이 닫힐 때 모든 상태 초기화
watch(() => props.modelValue, (newVal) => {
  if (!newVal) {
    selectedFiles.value = [];
    addedUrls.value = [];
    urlInput.value = '';
  }
});
</script>

<style scoped>
/* 필요한 스타일이 있다면 여기에 추가 */
</style>