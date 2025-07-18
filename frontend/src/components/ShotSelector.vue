<!-- frontend/src/components/ShotSelector.vue -->
<template>
  <v-container fluid>
    <div class="d-flex align-center mb-4">
      <v-autocomplete
        :model-value="projectName"
        @update:modelValue="handleProjectUpdate"
        label="Project"
        :items="projects"
        class="mr-4"
      ></v-autocomplete>
      <v-autocomplete
        :model-value="selectedShotName"
        @update:modelValue="updateSelectedShotName"
        label="Shot"
        :items="shots.map(s => s.code)"
        :disabled="!shots.length"
        class="mr-4"
      ></v-autocomplete>
      <v-btn @click="loadVersions" :disabled="!selectedShotName">OK</v-btn>
      <v-btn @click="clear" class="ml-4">Clear</v-btn>
    </div>
  </v-container>
</template>

<script setup>


const props = defineProps({
  projectName: String,
  projects: Array,
  shots: Array,
  selectedShotName: String,
});

const emit = defineEmits([
  'update:projectName',
  'update:selectedShotName',
  'onProjectSelected',
  'loadVersions',
  'clear',
]);

const handleProjectUpdate = (value) => {
  emit('update:projectName', value);
  emit('onProjectSelected', value); // 프로젝트 이름이 업데이트된 후 onProjectSelected 호출
};

const updateSelectedShotName = (value) => {
  emit('update:selectedShotName', value);
};

const loadVersions = () => {
  emit('loadVersions');
};

const clear = () => {
  emit('clear');
};
</script>

<style scoped>
/* 필요한 스타일이 있다면 여기에 추가 */
</style>