<template>
  <div>
    <!-- 내 첨부파일 목록 -->
    <div v-if="attachments.length > 0" class="attachments-section mt-2 pa-2 rounded" style="border: 1px solid #E0E0E0;">
      <div class="text-caption font-weight-bold mb-1">첨부파일</div>
      <div v-for="attachment in attachments" :key="attachment.id" class="d-flex align-center text-caption">
        <v-icon size="small" class="mr-1">{{ getIconForFile(attachment) }}</v-icon>
        <a @click.prevent="handleAttachmentClick(attachment)" href="#" class="text-decoration-none text-blue-lighten-2 path-link">
          {{ attachment.file_name || attachment.path_or_url }}
        </a>
        <v-spacer></v-spacer>
        <v-btn v-if="!readonly" icon variant="text" size="x-small" color="grey" @click="emit('delete-attachment', attachment.id)">
          <v-icon>mdi-close-circle</v-icon>
        </v-btn>
      </div>
    </div>

    <!-- "Copied!" 알림용 다이얼로그 -->
    <v-dialog
      :model-value="copiedPath.show"
      width="auto"
      hide-overlay
      persistent
      :scrim="false"
    >
      <v-card color="rgba(0, 0, 0, 0.7)" elevation="8" class="pa-2 rounded-lg">
        <v-card-text class="text-center d-flex align-center">
          <v-icon color="white" class="mr-2">mdi-clipboard-check-outline</v-icon>
          <span style="color: white;">Copied to clipboard!</span>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
/**
 * @file AttachmentHandler.vue
 * @description 첨부파일 목록을 표시하고, 관련 상호작용(클릭, 삭제)을 처리하는 UI 컴포넌트.
 */
import { useAttachments } from '@/composables/useAttachments.js';

/**
 * @props {Array} attachments - 표시할 첨부파일 객체의 배열.
 * @props {Boolean} readonly - true일 경우, 삭제 버튼을 숨깁니다.
 */
const props = defineProps({
  attachments: {
    type: Array,
    default: () => []
  },
  readonly: {
    type: Boolean,
    default: false
  },
});

/**
 * @emits delete-attachment - 삭제 버튼 클릭 시, 삭제할 첨부파일의 ID를 전달.
 * @emits upload-attachments - (현재 사용되지 않음) 첨부파일 업로드 이벤트를 전달.
 */
const emit = defineEmits(['delete-attachment', 'upload-attachments']);

// useAttachments 훅에서 첨부파일 관련 함수와 상태를 가져옵니다.
const {
  getIconForFile,
  handleAttachmentClick,
  copiedPath,
} = useAttachments();
</script>

<style scoped>
.path-link {
  word-break: break-all;
  overflow-wrap: break-word;
}
</style>