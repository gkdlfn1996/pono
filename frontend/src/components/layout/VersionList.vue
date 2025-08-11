<!-- frontend/src/components/versions/VersionList.vue -->
<template>
  <!-- 로딩 상태 표시는 props.isLoading을 직접 사용합니다. -->
  <div v-if="props.isLoading" class="text-center py-10">
    <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
    <p class="mt-4 text-grey-lighten-1">버전 목록을 불러오는 중입니다...</p>
  </div>

  <!-- 데이터가 있을 때는 props.versions를 직접 사용합니다. -->
  <div v-else-if="props.versions && props.versions.length > 0" class="versions-section">
    <div class="d-flex align-center mb-2">
      <h2 class="mr-2">Version</h2>
      <v-btn
        icon="mdi-refresh"
        size="small"
        variant="text"
        @click="refreshVersions"
        :disabled="props.isLoading"
      ></v-btn>
    </div>
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
              <DraftNotesData :version="versionItem" />
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

// import { versions, isLoading, selectedTask, selectTask } from '../../composables/useShotGridData';

// const props = defineProps({
//   notes: Object, // notesContent 객체 (초기값 및 외부 업데이트용)
//   notesComposable: Object, // notes composable 전체를 받음
//   isSaving: Object, // isSaving prop 타입을 Object로 변경
//   sendMessage: Function, // 웹소켓 메시지 전송 함수
// });

// const emit = defineEmits(['save-note', 'input-note', 'reload-other-notes']);

// const refreshVersions = () => {
//   if (selectedTask.value) {
//     // 현재 선택된 태스크로 버전 목록을 다시 로드합니다.
//     // selectTask 함수는 내부적으로 로딩 상태를 관리하고 versions를 업데이트합니다.
//     selectTask(selectedTask.value.name);
//   }
// };

// 부모로부터 받을 props를 명확하게 정의합니다.
// App.vue에서 :versions="versions"로 넘겨주었으므로, 여기서 받습니다.
const props = defineProps({
  versions: {
    type: Array,
    required: true,
  },
  isLoading: {
    type: Boolean,
    default: false,
  }
});

// 'refresh-versions' 이벤트를 부모에게 전달하기 위해 emit을 정의합니다.
const emit = defineEmits(['refresh-versions']);

// 새로고침 버튼 클릭 시 이 함수가 호출됩니다.
function refreshVersions() {
  // isLoading 상태와 관계없이 항상 이벤트를 발생시켜
  // 데이터 재로딩은 부모(App.vue)가 책임지도록 합니다.
  emit('refresh-versions');
}

</script>

<style scoped>
.version-list {
  /* 필요에 따라 스타일 추가 */
}
</style>