<template>
  <v-dialog :model-value="modelValue" @update:model-value="close" max-width="1200px" :persistent="isProcessing">
    <v-card>
      <v-card-title class="d-flex justify-space-between align-center">
        <span>Publish All Notes</span>
        <v-btn icon="mdi-close" variant="text" @click="close"></v-btn>
      </v-card-title>
      <v-divider></v-divider>

      <!-- 최종 결과 알림창 -->
      <v-alert
        v-if="publishResults.length > 0"
        :type="failedNotes.length === 0 ? 'success' : 'warning'"
        class="ma-4"
        variant="tonal"
      >
        <div class="d-flex justify-space-between align-center">
          <span>{{ summaryMessage }}</span>
        </div>
        <v-list v-if="failedNotes.length > 0" density="compact" class="bg-transparent mt-2">
          <v-list-item v-for="(item, i) in failedNotes" :key="i" class="pa-0">
            <v-list-item-title class="text-caption">
              <strong>{{ item.version.code }}:</strong> {{ item.error }}
            </v-list-item-title>
          </v-list-item>
        </v-list>
      </v-alert>

      <v-card-text style="max-height: 80vh; overflow-y: auto;">
        <p class="text-caption text-medium-emphasis mb-4">
          이 노트는 ShotGrid에 게시(Publish)될 최종본입니다. 내용을 마지막으로 확인하고 정리해 주세요.
        </p>

        <!-- 전역 헤더/서브젝트 표시 -->
        <div class="global-header-section pa-4 mb-4">
          <!-- <h3 class="text-h6 mb-4">Global Settings</h3> -->
          <div class="text-body-1">
            <p><span class="font-weight-bold" style="width: 120px; display: inline-block; text-align:right; margin-right: 8px;">Author :</span> {{ currentUser?.name }}</p>
            <p><span class="font-weight-bold" style="width: 120px; display: inline-block; text-align:right; margin-right: 8px;">Subject :</span> {{ modalGlobalNotes.subject }}</p>
            <p><span class="font-weight-bold" style="width: 120px; display: inline-block; text-align:right; margin-right: 8px;">Header Note :</span> {{ modalGlobalNotes.headerNote }}</p>
          </div>
        </div>

        <v-divider class="mb-4"></v-divider>

        <!-- 로딩 중 -->
        <div v-if="isLoadingNotes" class="d-flex justify-center align-center" style="height:200px;">
          <v-progress-circular indeterminate size="32" />
        </div>
        <!-- 노트 리스트 (로컬 사본 사용) -->
        <div v-else-if="notesToDisplay.length > 0" class="notes-list">
          <v-card 
            v-for="note in notesToDisplay" 
            :key="note.draft_note_id" 
            class="mb-4" 
            variant="outlined"
            :class="{ 'failed-note-card': failedNotes.some(f => f.noteId === note.draft_note_id) }">
            <v-card-text>
              <v-row no-gutters>
                <!-- 1. 정보 영역 (버전, 썸네일, To/CC) -->
                <v-col cols="12" md="4" class="pa-2">
                  <div class="text-subtitle-2 font-weight-bold mb-2">{{ note.version.code }}</div>
                  <v-responsive :aspect-ratio="16/9" class="rounded mb-2">
                    <!-- 썸네일 로딩 중 -->
                    <div v-if="note.version.image === undefined" class="d-flex align-center justify-center fill-height bg-grey-darken-1">
                      <v-progress-circular color="grey-lighten-4" indeterminate></v-progress-circular>
                    </div>
                    <!-- 썸네일 없음 -->
                    <div v-else-if="note.version.image === null" class="d-flex align-center justify-center fill-height bg-grey-darken-1">
                      <v-icon size="48" color="grey-lighten-1">mdi-image-off</v-icon>
                    </div>
                    <!-- 썸네일 있음 -->
                    <v-img v-else :src="note.version.image" cover class="fill-height">
                      <template v-slot:placeholder>
                        <div class="d-flex align-center justify-center fill-height">
                          <v-progress-circular color="grey-lighten-4" indeterminate></v-progress-circular>
                        </div>
                      </template>
                      <template v-slot:error>
                        <div class="d-flex align-center justify-center fill-height text-center pa-2 bg-grey-darken-1">
                          <span style="color: white; text-shadow: 1px 1px 2px rgba(0,0,0,0.7);">Error loading thumbnail.</span>
                        </div>
                      </template>
                    </v-img>
                  </v-responsive>
                  <!-- To/CC -->
                  <div class="mt-2">
                    <div class="d-flex align-center mb-2">
                      <div class="text-body-2 font-weight-bold" style="width: 40px;">To:</div>
                      <v-chip v-if="note.to" size="small" color="primary" variant="tonal">{{ note.to.name }}</v-chip>
                    </div>
                    <div class="d-flex">
                      <div class="text-body-2 font-weight-bold mr-3" style="width: 40px;">CC:</div>
                      <div class="d-flex flex-wrap" v-if="note.cc && note.cc.length > 0">
                        <v-chip v-for="user in note.cc" :key="user.id" size="small" variant="tonal" class="ma-1">{{ user.name }}</v-chip>
                      </div>
                    </div>
                  </div>
                </v-col>

                <!-- 2. 노트 내용 -->
                <v-col cols="12" md="8" class="pa-2 pl-6 d-flex flex-column">
                  <div class="text-subtitle-2 font-weight-bold mb-1">Note Content</div>
                  <div class="text-body-2" style="white-space: pre-wrap; word-wrap: break-word; flex-grow: 1; min-height: 100px;">{{ note.formattedContent }}</div>

                  <!-- Attachments section: Only render if attachments exist -->
                  <template v-if="note.attachments && note.attachments.length > 0">
                    <v-divider class="my-2"></v-divider>
                    <div class="text-subtitle-2 font-weight-bold mb-2">Attachments</div>
                    <div v-for="att in note.attachments" :key="att.id" class="d-flex align-center text-caption mb-1">
                      <v-icon size="small" class="mr-1">{{ getIconForFile(att) }}</v-icon>
                      <a href="#" @click.prevent="handleAttachmentClick(att)" class="text-decoration-none text-blue-lighten-2">{{ att.file_name || att.path_or_url }}</a>
                    </div>
                  </template>
                  
                  <v-btn
                    icon="mdi-close"
                    variant="text"
                    size="small"
                    class="position-absolute"
                    style="top: 8px; right: 8px;"
                    @click="removeNoteFromList(note.draft_note_id)"
                  ></v-btn>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </div>
        <!-- 데이터 없는 경우 -->
        <div v-else class="text-center py-10 text-grey">
          <v-icon size="64">{{ publishResults.length > 0 && successfulNotes.length > 0 ? 'mdi-check-all' : 'mdi-note-off-outline' }}</v-icon>
          <p class="mt-4">{{ publishResults.length > 0 && successfulNotes.length > 0 ? '모든 노트가 성공적으로 게시되었습니다.' : '게시할 임시 노트가 없습니다.' }}</p>
        </div>
      </v-card-text>

      <v-divider></v-divider>
      <v-card-actions class="pa-4">
        <v-spacer></v-spacer>
        <v-btn @click="close" variant="text" :disabled="isProcessing">Cancel</v-btn>
        <v-btn 
          color="primary" 
          variant="flat" 
          :disabled="notesToDisplay.length === 0 || isProcessing"
          :loading="isProcessing"
          @click="handlePublishAll"
        >
          Publish All ({{ notesToDisplay.length }})
        </v-btn>
      </v-card-actions>

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
    </v-card>
  </v-dialog>
</template>

<script setup>
/**
 * @file PublishAllNotesModal.vue
 * @description 여러 버전의 임시 노트를 일괄적으로 ShotGrid에 게시하기 위한 모달 컴포넌트.
 *              모달이 열릴 때, 필요한 모든 데이터를(버전, 썸네일, 노트) 비동기적으로 로드합니다.
 */
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { useAuth } from '@/composables/useAuth';
import { useShotGridData } from '@/composables/useShotGridData';
import { useAttachments } from '@/composables/useAttachments';
import { useShotGridPublish } from '@/composables/useShotGridPublish';

/**
 * @props {Boolean} modelValue - v-model을 통해 모달의 열림/닫힘 상태를 제어.
 * @props {Object} myNotes - 현재 사용자가 작성한 모든 임시 노트 객체.
 */
const props = defineProps({
  modelValue: Boolean,
  myNotes: {
    type: Object,
    default: () => ({})
  }
});

const emit = defineEmits(['update:modelValue']);

const { getCachedVersionsForPub, fetchThumbnailsForPub, selectedProject, loadVersions } = useShotGridData();
const { 
  isProcessing,
  publishResults,
  summaryMessage,
  failedNotes,
  successfulNotes,
  clearPublishResults,
  publishNotes,
  getInitialPublishUsers, getGlobalNotes
} = useShotGridPublish();
const { getIconForFile, handleAttachmentClick, copiedPath } = useAttachments();
const { user: currentUser } = useAuth();

// --- Modal-specific State ---
const isLoadingNotes = ref(false);
const notesInModal = ref([]); // 모달 내에서 관리될 로컬 노트 목록
//  UI 표시에 필요한 글로벌 서브젝트와 원본 헤더를 계산합니다.
const modalGlobalNotes = ref({});

/**
 * 게시 중 실시간으로 화면에 표시될 노트 목록을 계산합니다.
 * 성공한 노트는 목록에서 제외됩니다.
 */
const notesToDisplay = computed(() => {
  if (isProcessing.value || publishResults.value.length > 0) {
    const successfulIds = new Set(successfulNotes.value.map(n => n.noteId));
    return notesInModal.value.filter(note => !successfulIds.has(note.draft_note_id));
  }
  return notesInModal.value;
});

/**
 * 모달을 닫고, 부모 컴포넌트에 상태 변경을 알립니다.
 */
const close = () => {  
  if (isProcessing.value) return;
  // 성공적으로 게시된 노트가 하나라도 있으면, 메인 뷰를 새로고침합니다.
  if (successfulNotes.value.length > 0) {
    loadVersions(false);
  }
  emit('update:modelValue', false);
  setTimeout(clearPublishResults, 300);
};

/**
 * 'x' 버튼을 누르면 해당 노트를 게시 목록에서 제거합니다.
 * @param {number} draftNoteId - 제거할 임시 노트의 ID.
 */
const removeNoteFromList = (draftNoteId) => {
  if (isProcessing.value) return; // 처리 중에는 제거 비활성화
  const index = notesInModal.value.findIndex(n => n.draft_note_id === draftNoteId);
  if (index > -1) {
    notesInModal.value.splice(index, 1);
  }
};

const handlePublishAll = async () => {
  const notesToPublish = notesInModal.value.map(note => ({
    version: note.version,
    noteContent: note.content,
    attachments: note.attachments,
    draftNoteId: note.draft_note_id,
  }));

  await publishNotes(notesToPublish);

    // 게시 성공 시 (실패한 노트가 없을 경우)
  if (failedNotes.value.length === 0) {
    // 잠시 후 모달을 닫고 성공 이벤트를 전달합니다.
    setTimeout(() => { close(); }, 1500);
  }
};

// 모달이 열리는 시점(modelValue가 true가 될 때)을 감지하여,
// 모달에 표시될 모든 데이터를 준비하는 오케스트레이션 함수.
watch(() => props.modelValue, async (newValue) => {
  if (newValue) {
    // 상태 초기화
    isLoadingNotes.value = true;
    clearPublishResults();
    notesInModal.value = [];

    modalGlobalNotes.value = getGlobalNotes();
    const allCachedVersions = await getCachedVersionsForPub();
    const versionMap = new Map(allCachedVersions.map(v => [v.id, v]));

    const notesWithFullData = Object.values(props.myNotes)
      .filter(note => (note.content || note.attachments?.length > 0) && versionMap.has(note.version_id))
      .map(note => {
        const version = versionMap.get(note.version_id);
        const { toUsers, ccUsers } = getInitialPublishUsers(version, selectedProject.value);
        const { formattedHeader } = getGlobalNotes(version);
        const formattedContent = `${formattedHeader}${note.content}`;
        // to, cc, formattedContent는 UI 표시용. content는 게시 재료용.
        return { draft_note_id: note.id, version, content: note.content, formattedContent, attachments: note.attachments || [], to: toUsers[0], cc: ccUsers };
      });

    notesInModal.value = notesWithFullData;
    fetchThumbnailsForPub(notesInModal.value.map(n => n.version));
    isLoadingNotes.value = false;
  } else {
    notesInModal.value = []; // 모달이 닫히면 데이터 초기화
  }
});
</script>

<style scoped>
.position-absolute {
  position: absolute;
}
.failed-note-card {
  border-color: #B71C1C; /* Vuetify's error color */
  border-width: 2px;
}
</style>
