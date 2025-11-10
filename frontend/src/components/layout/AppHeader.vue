<template>
  <v-app-bar app>
    <v-row class="flex-grow-1 align-center">
      <v-col cols="4" class="d-flex align-center pl-4 justify-space-between">
        <!-- 1. 좌측 그룹 -->
        <v-app-bar-nav-icon @click="emit('toggle-drawer')"></v-app-bar-nav-icon>
        <v-col cols="auto" class="pa-0 flex-shrink-0">
          <v-toolbar-title class="font-weight-black text-blue-lighten-2 pl-4 mr-10 d-none d-md-flex">PONO</v-toolbar-title>
        </v-col>
        <!-- 프로젝트 & 파이프라인스텝 -->
        <v-autocomplete
          label="Project"
          :items="projects"
          item-title="name"
          item-value="id"
          :model-value="selectedProject?.id"
          @update:model-value="selectProject"
          :disabled="isVersionsLoading"
          variant="outlined"
          density="compact"
          hide-details
          class="mr-2"
          style="max-width: 200px;"
        ></v-autocomplete>
        <v-autocomplete
          label="Pipeline Step"
          :items="pipelineSteps"
          item-title="name"
          item-value="name"
          :model-value="selectedPipelineStep"
          @update:model-value="selectPipelineStep"
          :disabled="isVersionsLoading"
          variant="outlined"
          density="compact"
          hide-details
          style="max-width: 200px;">
          <template v-slot:item="{ props, item }">
            <div>
              <v-list-item v-bind="props" :title="item.raw"></v-list-item>
              <v-divider v-if="item.raw === 'All'"></v-divider>
            </div>
          </template>
        </v-autocomplete>
        <v-spacer></v-spacer>
      </v-col>
      
      <!-- 2. 중앙 요소 : 검색창 -->
      <v-col cols="4" class="d-flex align-center pa-0 justify-center">
        <SearchBar 
          :disabled="isSearchBarDisabled"
          @filters-complete="handleFiltersComplete" 
        />
      </v-col>

    <!-- 6. 우측 그룹 -->
     <!-- 유저정보 -->
    <v-col cols="4" class="d-flex align-center pr-4 justify-end">
      <v-icon color="grey-lighten-1" class="mr-2">mdi-account-circle</v-icon>
      <span class="text-subtitle-1 mr-4" style="color: #BDBDBD;">{{ username }}</span>
      <v-menu>
        <template v-slot:activator="{ props: menuProps }">
          <v-btn icon v-bind="menuProps">
            <v-icon>mdi-dots-vertical</v-icon>
          </v-btn>
        </template>
        <!-- 글로벌 옵션창 -->
        <v-list>
          <!-- 퍼블리시 노트 필터 -->
          <v-list-item>
            <v-list-item-title>
              <v-btn
                variant="text"
                block
                justify="start"
                @click="togglePublishedNotes"
              >
                {{ showPublishedNotes ? 'Hide Publish Notes' : 'Show Publish Notes' }}
              </v-btn>
            </v-list-item-title>
          </v-list-item>
          <v-divider></v-divider>
          <!-- 다크/라이트 모드 토글 -->
          <v-list-item>
            <v-list-item-title class="d-flex justify-start">
              <v-switch
                v-model="isDarkTheme"
                hide-details
                prepend-icon="mdi-white-balance-sunny"
                append-icon="mdi-weather-night"
                @update:modelValue="toggleDarkTheme"
                @click.stop
              ></v-switch>
            </v-list-item-title>
          </v-list-item>
          <v-divider></v-divider>
          <!-- 로그아웃 -->
          <v-list-item @click="emit('logout')">
            <v-list-item-title class="d-flex align-center">
              <v-icon class="mr-2">mdi-logout</v-icon>
              Logout
            </v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-col>
    </v-row>
  </v-app-bar>
</template>

<script setup>
import { onMounted, computed, watch } from 'vue';
import { useShotGridData } from '../../composables/useShotGridData';
import { useTheme } from 'vuetify';
import SearchBar from './SearchBar.vue';
import { useAppSettings } from '../../composables/useAppSettings'; // useAppSettings 임포트

const {
  projects,
  pipelineSteps,
  selectedProject,
  selectedPipelineStep,
  loadProjects,
  selectProject,
  selectPipelineStep,
  isVersionsLoading,
  applyFilters,
} = useShotGridData();
const { isDarkTheme, showPublishedNotes, toggleDarkTheme, togglePublishedNotes } = useAppSettings(); // useAppSettings 사용

const props = defineProps({
  username: String,
});

const emit = defineEmits(['toggle-drawer']);

onMounted(async () => {
  await loadProjects();
});

const theme = useTheme();
watch(isDarkTheme, (newValue) => {
  theme.global.name.value = newValue ? 'dark' : 'light';
});

// 검색창 활성화/비활성화 여부를 결정하는 computed 속성
const isSearchBarDisabled = computed(() => {
  return !selectedProject.value || !selectedPipelineStep.value;
});

// SearchBar로부터 필터 완료 이벤트를 받았을 때 실행되는 핸들러
function handleFiltersComplete(filters) {
  console.log('SearchBar로부터 필터 신호를 받았습니다. 적용될 필터:', filters);
  applyFilters(filters);
}

</script>

<style scoped>
/* Styles for AppHeader */
/* 테마변경 아이콘 사이즈 줄이기 */
:deep(.v-list-item .v-switch .v-icon) {
  font-size: 20px !important;
}

</style>