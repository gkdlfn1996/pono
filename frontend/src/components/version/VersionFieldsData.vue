<template>
  <!-- 1단: 정보 영역 -->
  <div class="d-flex flex-column h-100">
    <h4 class="text-subtitle-1 font-weight-bold mb-2">{{ title }}</h4>
    <!-- Thumbnail: Responsive container to enforce 16:9 aspect ratio -->
    <v-responsive :aspect-ratio="16/9" class="mb-2 rounded">
      <v-img
        v-if="version.image"
        :src="version.image"
        class="fill-height"
        cover
      >
        <template v-slot:placeholder>
          <div class="d-flex align-center justify-center fill-height">
            <v-progress-circular color="grey-lighten-4" indeterminate></v-progress-circular>
          </div>
        </template>
        <template v-slot:error>
          <div class="d-flex align-center justify-center fill-height text-center pa-2 bg-grey-darken-1">
            <span class="text-white">Error loading thumbnail.</span>
          </div>
        </template>
      </v-img>
      <div
        v-else
        class="d-flex align-center justify-center bg-grey-darken-1"
        style="width: 100%; height: 100%;"
      >
        <v-icon size="48" color="grey-lighten-1">mdi-image-off</v-icon>
      </div>
    </v-responsive>

    <v-row no-gutters class="flex-grow-1">
      <v-col>
        <div class="text-body-2">
          <p><strong class="mr-2">Final Due:</strong> {{ version['entity.Shot.sg_end_date'] || 'N/A' }}</p>
          <p><strong class="mr-2">2D 마감:</strong> {{ version['sg_task.Task.due_date'] || 'N/A' }}</p>
          <p><strong class="mr-2">Artists:</strong> {{ version.user ? version.user.name : 'N/A' }}</p>
        </div>
      </v-col>
      <v-col cols="auto">
        <div class="d-flex flex-column align-end">
          <template v-for="status in statuses" :key="status.label">
            <v-tooltip :text="status.label + ' Status'" location="top">
              <template v-slot:activator="{ props: tooltipProps }">
                <v-chip v-bind="tooltipProps" size="small" class="mb-1" :color="status.color">{{ status.value || 'N/A' }}</v-chip>
              </template>
            </v-tooltip>
          </template>
        </div>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  version: {
    type: Object,
    required: true,
  },
  title: {
    type: String,
    required: true,
  }
});

const statuses = computed(() => {
  const statusMap = {
      'acm': 'amber-lighten-4',
      'aok': 'yellow-lighten-4',
      'are': 'red-lighten-2',
      'assign': 'yellow-lighten-2',
      'cgi': 'cyan-lighten-3',
      'cre': 'red-lighten-1',
      'dept': 'orange-lighten-3',
      'dif': 'red-lighten-2',
      'dir': 'blue-lighten-2',
      'dre': 'red-lighten-1',
      'dwip': 'green-darken-1',
      'done': 'white',
      'hld': 'grey-darken-1',
      'lre': 'red-lighten-2',
      'lwip': 'light-green-accent-2',
      'mask': 'teal-darken-4',
      'movs': 'light-blue-lighten-1',
      'noise': 'lime-darken-3',
      'omt': 'orange-darken-3',
      'out': 'pink-lighten-3',
      'pub': 'light-green-lighten-4',
      'pubr': 'red-lighten-2',
      'pubs': 'light-green-lighten-2',
      'qc': 'red-lighten-2',
      'qna': 'purple-lighten-3',
      'retake': 'red-lighten-2',
      'sdev': 'red-lighten-2',
      'swip': 'green-lighten-1',
      'team': 'orange-lighten-3',
      'tpub': 'blue-lighten-4',
      'tpubr': 'red-lighten-2',
      'tpubs': 'blue-lighten-3',
      'vfx': 'cyan-lighten-2',
      'vre': 'red-lighten-2',
      'wip': 'light-green-lighten-1',
  };

  const result = [];

  // Version Status
  const versionStatus = props.version.sg_status_list;
  if (versionStatus) {
    result.push({ 
      label: 'Version',
      value: versionStatus,
      color: statusMap[versionStatus.toLowerCase()] || 'grey-lighten-1'
    });
  }

  // Shot Status
  // 데이터 구조에 맞게 직접 접근
  const shotStatus = props.version['entity.Shot.sg_status_list'];
  if (shotStatus) {
    result.push({ 
      label: 'Shot',
      value: shotStatus,
      color: statusMap[shotStatus.toLowerCase()] || 'grey-lighten-1'
    });
  }

  // Asset Status
  // 데이터 구조에 맞게 직접 접근
  const assetStatus = props.version['entity.Asset.sg_status_list'];
  if (assetStatus) {
    result.push({
      label: 'Asset',
      value: assetStatus,
      color: statusMap[assetStatus.toLowerCase()] || 'grey-lighten-1'
    })
  }

  // Task Status
  // 데이터 구조에 맞게 직접 접근
  const taskStatus = props.version['sg_task.Task.sg_status_list'];
  if (taskStatus) {
    result.push({ 
      label: 'Task',
      value: taskStatus,
      color: statusMap[taskStatus.toLowerCase()] || 'grey-lighten-1'
    });
  }

  return result;
});

const formatDateTime = (isoString) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleString('ko-KR', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false
  }).replace(/\.\s/g, '.').slice(0, -1);
};
</script>

<style scoped>
.text-white {
  color: white !important;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.7);
}
</style>