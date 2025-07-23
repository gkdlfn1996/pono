<template>
  <v-app-bar app>
    <!-- 1. 좌측 그룹 -->
    <div class="d-flex align-center mr-4">
      <v-app-bar-nav-icon @click="emit('toggle-drawer')"></v-app-bar-nav-icon>
      <v-toolbar-title class="font-weight-black text-blue-lighten-2 mr-2">PONO</v-toolbar-title>
    </div>
    <!-- 2. 프로젝트, 테스크 선택 그룹 -->
    <div class="d-flex align-center">
      <v-autocomplete
        label="Project"
        :items="projects"
        item-title="name"
        item-value="name"
        v-model="projectName"
        @update:modelValue="handleProjectSelection"
        variant="outlined"
        density="compact"
        hide-details
        style="width: 200px;"
        class="mr-2"
      ></v-autocomplete>
      <v-autocomplete
        label="Task"
        :items="tasks"
        item-title="name"
        item-value="name"
        v-model="selectedTaskName"
        @update:modelValue="onTaskSelected"
        variant="outlined"
        density="compact"
        hide-details
        style="width: 200px;"
      ></v-autocomplete>
    </div>


    <!-- 3. 첫 번째 스페이서 -->
    <v-spacer></v-spacer>

    <!-- 4. 중앙 요소들 -->
    <div class="d-flex align-center" style="position: absolute; left: 50%; transform: translateX(-50%);">
        <v-menu :close-on-content-click="false" v-model="showSearchOptions">
            <template v-slot:activator="{ props: menuProps }">
                <v-text-field
                    label="Search or Filter"
                    v-model="searchQuery"
                    variant="outlined"
                    density="compact"
                    hide-details
                    prepend-inner-icon="mdi-magnify"
                    style="width: 800px;"
                    v-bind="menuProps"
                    @keydown.enter="handleSearchInputEnter"
                ></v-text-field>
            </template>
            <v-list>
                <v-list-item @click="addSearchLabel('Shot')">
                    <v-list-item-title>Shot</v-list-item-title>
                </v-list-item>
                <v-list-item disabled><v-list-item-title>Playlist</v-list-item-title></v-list-item>
                <v-list-item disabled><v-list-item-title>Subject</v-list-item-title></v-list-item>
                <v-list-item disabled><v-list-item-title>Version</v-list-item-title></v-list-item>
                <v-list-item disabled><v-list-item-title>Tag</v-list-item-title></v-list-item>
            </v-list>
        </v-menu>
        <div class="d-flex align-center ml-2">
            <v-chip v-for="(label, index) in searchLabels" :key="index" closable @click:close="removeSearchLabel(index)" class="mr-1">
                {{ label.type }}: {{ label.value }}
            </v-chip>
        </div>
    </div>

    <!-- 5. 두 번째 스페이서 -->
    <v-spacer></v-spacer>

    <!-- 6. 우측 그룹 -->
    <div class="d-flex align-center">
      <v-icon color="grey-lighten-1" class="mr-2">mdi-account-circle</v-icon>
      <span class="text-subtitle-1 mr-4" style="color: #BDBDBD;">{{ loggedInUser }}</span>
      <v-btn icon>
        <v-icon>mdi-dots-vertical</v-icon>
      </v-btn>
    </div>
  </v-app-bar>
</template>

<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'; // nextTick 추가
import useShotGridData from '../../composables/useShotGridData';
import { fetchVersionsForTask } from '../../api';

const props = defineProps({
  loggedInUser: String,
});

const emit = defineEmits(['toggle-drawer', 'load-versions']);

const {
  projectName,
  projects,
  tasks,
  selectedTaskName,
  loadProjects,
  onProjectSelected,
} = useShotGridData();

const handleProjectSelection = async (newProjectName) => {
  console.log('handleProjectSelection called with:', newProjectName);
  await onProjectSelected(newProjectName); // useShotGridData의 onProjectSelected 호출
};

const onTaskSelected = async (newTaskName) => {
  const selectedTask = tasks.value.find(t => t.name === newTaskName);
  if (selectedTask) {
    const versions = await fetchVersionsForTask(selectedTask.id);
    emit('load-versions', versions);
  }
};

onMounted(async () => {
  await loadProjects();
});

watch(() => props.loggedInUser, (newVal) => {
  if (newVal) {
    loadProjects();
  }
});

const searchQuery = ref('');
const showSearchOptions = ref(false);
const searchLabels = ref([]);

const addSearchLabel = (type) => {
  if (type === 'Shot') {
    searchLabels.value.push({ type: 'Shot', value: '' });
    searchQuery.value = 'Shot: ';
    // 커서 위치를 'Shot: ' 뒤로 이동
    nextTick(() => {
      const inputElement = document.querySelector('.v-text-field input');
      if (inputElement) {
        inputElement.focus();
        inputElement.setSelectionRange(searchQuery.value.length, searchQuery.value.length);
      }
    });
  }
  showSearchOptions.value = false;
};

const removeSearchLabel = (index) => {
  searchLabels.value.splice(index, 1);
};

// 검색 입력란에서 엔터 키 입력 시 라벨 추가
const handleSearchInputEnter = () => {
  if (searchQuery.value.startsWith('Shot: ')) {
    const shotName = searchQuery.value.replace('Shot: ', '').trim();
    if (shotName) {
      searchLabels.value.push({ type: 'Shot', value: shotName });
      searchQuery.value = '';
    }
  }
};

// 기존 watch(searchQuery)는 handleSearchInputEnter로 대체되므로 제거
// watch(searchQuery, (newQuery) => {
//   if (newQuery.startsWith('Shot: ') && newQuery.endsWith('\n')) { // 엔터 키 감지
//     const shotName = newQuery.replace('Shot: ', '').trim();
//     if (shotName) {
//       searchLabels.value.push({ type: 'Shot', value: shotName });
//       searchQuery.value = ''; // 입력란 초기화
//     }
//   }
// });

defineExpose({
  projectName,
  projects,
  tasks,
  selectedTaskName,
  onProjectSelected,
  onTaskSelected,
  searchQuery,
  searchLabels,
});
</script>

<style scoped>
/* Styles for AppHeader */
</style>