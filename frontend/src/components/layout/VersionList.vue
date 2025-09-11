<template>
  <!-- 로딩 상태 표시는 props.isLoading을 직접 사용합니다. -->
  <!-- v-if와 v-else-if를 사용하여 로딩, 데이터 있음, 데이터 없음 세 가지 상태를 명확히 분리합니다. -->
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
          <v-row>
            <!-- 1단: VersionFieldsData (정보 영역) -->
            <v-col cols="12" md="3">
              <VersionFieldsData :version="versionItem" :title="versionItem.code" />
            </v-col>

            <!-- 2단: DraftNotesData (Draft Notes 영역) -->
            <v-col cols="12" md="5">
              <DraftNotesData
                :version="versionItem"
                :myNote="props.myNotes[versionItem.id]"
                :otherNotes="props.otherNotes[versionItem.id]"
                :isSaved="props.isSaved[versionItem.id]"
                :newNoteIds="props.newNoteIds"
                :saveNote="props.saveNote"
                :debouncedSave="props.debouncedSave"
                :clearNewNoteFlag="props.clearNewNoteFlag"
              />
            </v-col>

            <!-- 3단: VersionNotesData (Version Notes 영역) -->
            <v-col cols="12" md="4">
              <VersionNotesData :version="versionItem" />
            </v-col>
          </v-row>
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
import { computed } from 'vue';
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
});

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
  isVersionsLoading,
  cancelLoadVersions 
} = useShotGridData();

const emit = defineEmits(['refresh-versions']);

function refreshVersions() {
  emit('refresh-versions');
}
</script>

<style scoped>
.version-list {
  /* 필요에 따라 스타일 추가 */
}
.normal-spacing {
  letter-spacing: normal;
}
</style>
