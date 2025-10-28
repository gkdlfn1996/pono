<template>
  <v-dialog :model-value="modelValue" @update:model-value="close" max-width="1200px" persistent>
    <v-card>
      <v-overlay
        :model-value="isLoading"
        class="align-center justify-center"
        persistent
      >
        <v-progress-circular
          color="primary"
          indeterminate
          size="64"
        ></v-progress-circular>
      </v-overlay>

      <v-card-title class="d-flex justify-space-between align-center">
        <span>Publish All Notes</span>
        <v-btn icon="mdi-close" variant="text" @click="close"></v-btn>
      </v-card-title>
      <v-divider></v-divider>

      <v-card-text style="max-height: 80vh; overflow-y: auto;">
        <p class="text-caption text-medium-emphasis mb-4">
          이 노트는 ShotGrid에 게시(Publish)될 최종본입니다. 내용을 마지막으로 확인하고 정리해 주세요.
        </p>

        <!-- 전역 헤더/서브젝트 표시 -->
        <div class="global-header-section pa-4 mb-4">
          <!-- <h3 class="text-h6 mb-4">Global Settings</h3> -->
          <div class="text-body-1">
            <p><span class="font-weight-bold" style="width: 120px; display: inline-block; text-align:right; margin-right: 8px;">Author :</span> {{ currentUser?.name }}</p>
            <p><span class="font-weight-bold" style="width: 120px; display: inline-block; text-align:right; margin-right: 8px;">Subject :</span> {{ currentSubject }}</p>
            <p><span class="font-weight-bold" style="width: 120px; display: inline-block; text-align:right; margin-right: 8px;">Header Note :</span> {{ currentHeaderNote }}</p>
          </div>
        </div>

        <v-divider class="mb-4"></v-divider>

        <!-- 노트 리스트 -->
        <div v-if="notesToPublish.length > 0" class="notes-list">
          <v-card v-for="note in notesToPublish" :key="note.version.id" class="mb-4" variant="outlined">
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
                    @click="removeNoteFromList(note.version.id)"
                  ></v-btn>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </div>
        <!-- 데이터 없는 경우 -->
        <div v-else class="text-center py-10 text-grey">
          <v-icon size="64">mdi-note-off-outline</v-icon>
          <p class="mt-4">게시할 임시 노트가 없습니다.</p>
        </div>
      </v-card-text>

      <v-divider></v-divider>
      <v-card-actions class="pa-4">
        <v-spacer></v-spacer>
        <v-btn @click="close" variant="text">Cancel</v-btn>
        <v-btn color="primary" variant="flat" :disabled="notesToPublish.length === 0">
          Publish All ({{ notesToPublish.length }})
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
import { useAuth } from '@/composables/useAuth.js';
import { useShotGridData } from '@/composables/useShotGridData.js';
import { useAttachments } from '@/composables/useAttachments.js';
import { useShotGridPublish } from '@/composables/useShotGridPublish.js'; // Missing import added

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

const { getCachedVersionsForPub, fetchThumbnailsForPub, selectedProject } = useShotGridData(); // selectedProject 추가
const isLoading = ref(false); // 모달 내부 데이터 로딩 상태
const { getPublishUsers } = useShotGridPublish(); // getPublishUsers 함수 가져오기
const { getIconForFile, handleAttachmentClick, copiedPath } = useAttachments();
const modalVersions = ref([]); // 모달 전용 버전 목록
const { user: currentUser } = useAuth();
const currentSubject = ref('');
const currentHeaderNote = ref('');

/**
 * 현재 로그인한 사용자의 고유 키를 생성하여 localStorage에서 개인화된 설정을 불러옵니다.
 */
const userSpecificStorageKey = computed(() => {
  return currentUser.value?.login ? `pono-header-${currentUser.value.login}` : null;
});

/**
 * 현재 로그인된 사용자에 맞는 Global Subject와 Header Note를 localStorage에서 불러옵니다.
 */
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

/**
 * 컴포넌트 마운트 시, 다른 곳에서 헤더/서브젝트가 수정되었을 때 동기화하기 위해
 * window 전역 이벤트 리스너를 등록합니다.
 */
onMounted(() => {
  loadHeaderData();
  window.addEventListener('pono-header-updated', loadHeaderData);
});

/**
 * 컴포넌트 언마운트 시, 메모리 누수 방지를 위해 등록했던
 * window 전역 이벤트 리스너를 제거합니다.
 */
onBeforeUnmount(() => {
  window.removeEventListener('pono-header-updated', loadHeaderData);
});

/**
 * 모달을 닫고, 부모 컴포넌트에 상태 변경을 알립니다.
 */
const close = () => {
  emit('update:modelValue', false);
};

/**
 * 'x' 버튼을 누르면 해당 노트를 게시 목록에서 제거합니다.
 * @param {number} versionId - 제거할 버전의 ID.
 */
const removeNoteFromList = (versionId) => {
  const index = modalVersions.value.findIndex(v => v.id === versionId);
  if (index > -1) {
    modalVersions.value.splice(index, 1);
  }
};

/**
 * props로 받은 myNotes와 내부 modalVersions를 기반으로, 실제로 게시될 노트 목록을 동적으로 계산합니다.
 * 내용이나 첨부파일이 있는 노트만 필터링하고, UI에 필요한 모든 정보(To, CC, 포맷된 컨텐츠 등)를 포함하여 반환합니다.
 * @returns {Array} 게시될 노트 정보 객체의 배열.
 */
const notesToPublish = computed(() => {
  if (modalVersions.value.length === 0 || !props.myNotes) {
    return [];
  }

  return modalVersions.value
    .filter(version => props.myNotes[version.id] && (props.myNotes[version.id].content || props.myNotes[version.id].attachments?.length > 0))
    .map(version => {
      const note = props.myNotes[version.id];
      const { toUsers, ccUsers } = getPublishUsers(version, selectedProject.value); // getPublishUsers 사용
      let formattedContent = note.content;
      if (currentHeaderNote.value) {
        const parts = version.code?.split('_');
        if (parts && parts.length >= 4) {
          const task = parts[2];
          const verNum = parts[3];
          formattedContent = `${currentHeaderNote.value}_${task}_${verNum}_${note.content}`;
        } else {
          formattedContent = `${currentHeaderNote.value}_${note.content}`;
        }
      }

      return {
        version: version,
        content: note.content,
        formattedContent: formattedContent,
        attachments: note.attachments || [],
        to: toUsers[0], // 'To'는 배열의 첫 번째 사용자
        cc: ccUsers, // 'CC'는 배열
      };
    });
});

// 모달이 열리는 시점(modelValue가 true가 될 때)을 감지하여,
// 모달에 표시될 모든 데이터를 준비하는 오케스트레이션 함수.
watch(() => props.modelValue, async (newValue) => {
  if (newValue) {
    isLoading.value = true;
    const allCachedVersions = await getCachedVersionsForPub();

    // myNotes에 있는 버전 ID 목록을 기반으로 필터링합니다.
    const noteVersionIds = Object.keys(props.myNotes).map(id => parseInt(id, 10));
    const filteredVersions = allCachedVersions.filter(version => noteVersionIds.includes(version.id));

    modalVersions.value = filteredVersions;
    isLoading.value = false;

    // 필터링된 버전에 대해서만 썸네일을 가져옵니다.
    fetchThumbnailsForPub(modalVersions.value);
  } else {
    modalVersions.value = []; // 모달이 닫히면 데이터 초기화
  }
});
</script>

<style scoped>
.position-absolute {
  position: absolute;
}
</style>
