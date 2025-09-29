<template>
  <!-- 로딩 상태 표시는 props.isLoading을 직접 사용합니다. -->
  <!-- v-if와 v-else-if를 사용하여 로딩, 데이터 있음, 데이터 없음 세 가지 상태를 명확히 분리합니다. -->
  <!-- 3단: VersionNotesData (Version Notes 영역) -->

  <div v-if="isVersionsLoading" class="text-center py-10">
    <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
    <p class="mt-4 text-grey-lighten-1">버전 목록을 불러오는 중입니다...</p>
    <p
      class="mt-2 text-caption text-grey"
      style="cursor: pointer; text-decoration: underline;"
      @click="cancelLoadVersions"
    >Cancel</p>
  </div>

  <!-- 데이터가 있을 때는 props.versions를 직접 사용합니다. -->
  <div v-else-if="props.versions && props.versions.length > 0" class="versions-section">
    <div class="d-flex align-center mb-2 flex-wrap">
      <h2 class="mr-2">Version</h2>
      <v-btn
        icon="mdi-refresh"
        size="small"
        variant="text"
        @click="refreshVersions"
        :disabled="isVersionsLoading"
      ></v-btn>
      <div v-if="selectedProject && selectedPipelineStep" class="ml-4 text-subtitle-1 text-grey">
        <span>{{ selectedProject.name }}</span>
        <v-icon size="small" class="mx-1">mdi-chevron-right</v-icon>
        <span>{{ selectedPipelineStep }}</span>
      </div>
      <v-spacer></v-spacer>
      <!-- 정렬 컨트롤 UI -->
      <div class="d-flex align-center">
        <v-menu offset-y>
          <template v-slot:activator="{ props: menuProps }">
            <v-btn v-bind="menuProps" variant="text" class="mr-1 text-none font-weight-regular normal-spacing">
              Sort By: {{ currentSortName }}
            </v-btn>
          </template>
          <v-list dense>
            <v-list-item
              v-for="option in sortOptions"
              :key="option.key"
              @click="() => props.setSort(option.key)"
              :disabled="option.disabled.value"
            >
              <v-list-item-title>{{ option.name }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
        <v-btn
          icon
          variant="text"
          size="small"
          @click="() => props.setSort(props.sortBy)"
        >
          <v-icon>{{ props.sortOrder === 'asc' ? 'mdi-arrow-up' : 'mdi-arrow-down' }}</v-icon>
        </v-btn>
      </div>
    </div>
    <v-divider class="mb-4"></v-divider>
    <div class="version-list">
      <v-card
        v-for="versionItem in props.versions"
        :key="versionItem.id"
        class="mb-6" variant="outlined"
      >
        <v-card-text>
          <!-- 방법 2: v-row/v-col 대신 CSS Grid를 사용한 레이아웃 -->
          <div class="version-grid-row">
            <!-- 1단: VersionFieldsData (정보 영역) -->
            <div>
              <VersionFieldsData :version="versionItem" :title="versionItem.code" />
            </div>

            <!-- 2단: DraftNotesData (Draft Notes 영역) -->
            <div>
              <DraftNotesData
                :version="versionItem"
                :myNote="props.myNotes[versionItem.id]"
                :otherNotes="props.otherNotes[versionItem.id]"
                :isSaved="props.isSaved[versionItem.id]"
                :newNoteIds="props.newNoteIds"
                :saveNote="props.saveNote"
                :debouncedSave="props.debouncedSave"
                :clearNewNoteFlag="props.clearNewNoteFlag"
                :uploadAttachments="props.uploadAttachments"
                :deleteAttachment="props.deleteAttachment"
              />
            </div>

            <!-- 3단: VersionNotesData (Version Notes 영역) -->
            <div class="d-flex flex-column h-100">
              <v-tabs v-model="tabStates[versionItem.id]" class="notes-tabs" hide-slider>
                <v-tab value="version" class="text-subtitle-1 font-weight-bold mb-3">
                  Version Notes
                </v-tab>
                <v-tab v-if="versionItem.entity" :value="'linked_entity'" class="text-subtitle-1 font-weight-bold mb-3">
                  {{ versionItem.entity.type === 'Shot' ? 'Linked Shot Notes' : 'Linked Asset Notes' }}
                </v-tab>
              </v-tabs>
              <v-window v-model="tabStates[versionItem.id]" class="notes-window flex-grow-1">
                <v-window-item value="version" class="h-100">
                  <VersionNotesData :version="versionItem" />
                </v-window-item>
                <v-window-item :value="'linked_entity'" class="h-100">
                  <LinkedNotesData 
                    :entity="versionItem.entity"
                    :notes="linkedNotes[versionItem.entity.id]"
                  />
                </v-window-item>
              </v-window>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </div>
  </div>

  <!-- 데이터가 없을 때의 메시지입니다. -->
  <div v-else class="py-6 text-center text-grey-lighten-1">
    <p class="text-h3 text-grey-lighten-1 mt-6">
      선택된 테스크에 등록된 버전이 없습니다.
    </p>
  </div>
</template>

<script setup>
import VersionFieldsData from '../version/VersionFieldsData.vue';
import DraftNotesData from '../version/DraftNotesData.vue';
import VersionNotesData from '../version/VersionNotesData.vue';
import LinkedNotesData from '../version/LinkedNotesData.vue';
import { ref, computed, watch } from 'vue';
import { useShotGridData } from '../../composables/useShotGridData';

const props = defineProps({
  versions: {
    type: Array,
    required: true,
  },
  sortBy: String,
  sortOrder: String,
  presentEntityTypes: Array,
  setSort: Function,
  // 노트 관련 props 추가
  myNotes: Object,
  otherNotes: Object,
  isSaved: Object,
  newNoteIds: Set,
  saveNote: Function,
  debouncedSave: Function,
  clearNewNoteFlag: Function,
  uploadAttachments: Function,
  deleteAttachment: Function,
});

// 각 버전 카드의 탭 상태를 독립적으로 관리하기 위한 객체
const tabStates = ref({});

// 각 버전의 링크 노트 데이터를 저장하는 객체
const linkedNotes = ref({});

// 현재 로딩 중인 엔티티 ID를 추적하는 Set
const loadingEntities = ref(new Set());

// 정렬 옵션
const sortOptions = [
  { name: 'Version - Name', key: 'version_name', disabled: computed(() => false) },
  { name: 'Shot - Rnum', key: 'shot_rnum', disabled: computed(() => !props.presentEntityTypes.includes('Shot')) },
  { name: 'Shot - Name', key: 'shot_name', disabled: computed(() => !props.presentEntityTypes.includes('Shot')) },
  { name: 'Asset - Name', key: 'asset_name', disabled: computed(() => !props.presentEntityTypes.includes('Asset')) },
  { name: 'Date Created', key: 'created_at', disabled: computed(() => false) },
];

// 현재 정렬 기준 표시 이름
const currentSortName = computed(() => {
  const found = sortOptions.find(option => option.key === props.sortBy);
  return found ? found.name : '';
});

const {
  selectedProject,
  selectedPipelineStep,
  loadLinkedNotes,
  isVersionsLoading,
  cancelLoadVersions 
} = useShotGridData();

const emit = defineEmits(['refresh-versions']);

function refreshVersions() {
  emit('refresh-versions');
}

// 탭 상태를 감시하여, 링크 노트 탭이 처음 열릴 때 데이터를 로드합니다.
watch(tabStates, async (newStates) => {
  for (const versionId in newStates) {
    const newState = newStates[versionId];

    // 탭이 'linked_entity'로 변경되었고,
    if (newState === 'linked_entity') {
      const version = props.versions.find(v => v.id == versionId);
      // 아직 해당 entity의 노트 데이터가 로드되지 않았고, 현재 로딩 중도 아니라면 데이터 로딩을 시작합니다.
      if (version && version.entity && !linkedNotes.value[version.entity.id] && !loadingEntities.value.has(version.entity.id)) {
        try {
          loadingEntities.value.add(version.entity.id); // 로딩 시작 표시

          const notesData = await loadLinkedNotes(version.entity);
          linkedNotes.value[version.entity.id] = notesData;
        } finally {
          loadingEntities.value.delete(version.entity.id); // 성공/실패 여부와 관계없이 로딩 상태 해제
        }
      }
    }
  }
}, { deep: true });

</script>

<style scoped>
.normal-spacing {
  letter-spacing: normal;
}
.version-grid-row {
  display: grid;
  grid-template-columns: 3fr 4fr 4fr; /* 11칸으로 나누고 3:4:4 비율로 할당 */
  gap: 24px; /* v-col의 기본 여백과 유사한 간격 */
  align-items: stretch; /* 모든 자식 요소들이 가장 높은 요소를 기준으로 늘어남 */
}

.version-grid-row > div {
  min-width: 0; /* 그리드 아이템이 내용보다 작아질 수 있도록 허용 */
}

.notes-window {
  min-height: 0 !important; /* Vuetify 기본값 300px 덮어쓰기 */
  height: 100%;
}

.notes-tabs {
  height: auto; /* 탭 높이를 내용에 맞게 조절 */
}

.notes-tabs .v-tab {
  line-height: 1.75rem !important; 
  padding: 0 !important;
}

.notes-tabs .v-tab:first-child {
  margin-right: 16px !important;
}


:deep(.notes-tabs .v-btn) {
  height: auto !important;
}

/* 선택되지 않은 탭의 색상을 회색으로 변경 */
:deep(.notes-tabs .v-tab:not(.v-tab--selected)) {
  color: grey;
}
</style>
