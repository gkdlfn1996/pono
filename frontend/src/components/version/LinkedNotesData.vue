<template>
  <!-- 3단: Linked Shot/Asset Notes 영역 -->
  <div class="d-flex flex-column fill-height">
    <div class="flex-shrink-0 mb-2">
      <v-text-field
        v-model="searchQuery"
        label="Search Subject or Body"
        variant="outlined"
        density="compact"
        hide-details
        prepend-inner-icon="mdi-magnify"
        clearable
        @keydown.enter="applySearch"
        @click:clear="clearSearch"
      ></v-text-field>
    </div>
    <v-card variant="outlined" class="flex-grow-1 d-flex flex-column" style="min-height: 0;">
      <v-card-text class="pa-0 notes-container flex-grow-1">
        <!-- 로딩 상태 표시 -->
        <div v-if="!notes" class="d-flex align-center justify-center fill-height">
          <v-progress-circular indeterminate color="grey-lighten-1"></v-progress-circular>
        </div>
        <!-- 데이터가 있을 때만 노트를 렌더링 -->
        <template v-else-if="filteredNotes && filteredNotes.length > 0">
          <div v-for="(note, index) in filteredNotes" :key="index">
            <div class="d-flex justify-space-between align-center px-3 pt-2 pb-1">
              <span class="text-subtitle-2 font-weight-bold">{{ note.user.name }}</span>
              <span class="text-caption text-grey">{{ formatDateTime(note.created_at) }}</span>
            </div>
            <div v-if="note.subject" class="text-subtitle-2 font-weight-bold px-3 pb-1 text-grey">
              {{ note.subject }}
            </div>
            <div class="text-body-2 pt-0 pb-2 px-3" style="white-space: pre-wrap; word-wrap: break-word;">{{ note.content }}</div>
            <v-divider v-if="index < filteredNotes.length - 1"></v-divider>
          </div>
        </template>
        <!-- 데이터가 없을 때 메시지 표시 -->
        <div v-else class="d-flex align-center justify-center fill-height">
          <p class="text-grey text-center">
            연결된 노트가 없습니다.
          </p>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

const props = defineProps({
  entity: {
    type: Object,
    default: null,
  },
  notes: {
    type: Array,
    default: null, // 초기에는 null, 로딩 완료 후 배열
  }
});

watch(() => props.notes, (newNotes) => {
  console.log('[LinkedNotesData] notes prop 변경됨:', newNotes);
}, { immediate: true });

const searchQuery = ref(''); // 검색어 입력을 위한 ref
const activeSearchTerm = ref(''); // Enter로 확정된 검색어

// Enter 키를 눌렀을 때, 현재 검색어를 확정된 검색어로 설정
const applySearch = () => {
  activeSearchTerm.value = searchQuery.value;
};

// 검색창의 x 버튼을 눌렀을 때, 검색어와 확정된 검색어를 모두 초기화
const clearSearch = () => {
  searchQuery.value = '';
  activeSearchTerm.value = '';
};

// 확정된 검색어(activeSearchTerm)를 기준으로 노트를 필터링하는 computed 속성
const filteredNotes = computed(() => {
  if (!props.notes) return [];
  if (!activeSearchTerm.value) {
    return props.notes; // 확정된 검색어가 없으면 전체 목록 반환
  }
  const lowerCaseQuery = activeSearchTerm.value.toLowerCase();
  return props.notes.filter(note => 
    (note.subject && note.subject.toLowerCase().includes(lowerCaseQuery)) ||
    (note.content && note.content.toLowerCase().includes(lowerCaseQuery))
  );
});

const formatDateTime = (isoString) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleString('ko-KR', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
    hour12: false
  }).replace(/\.\s/g, '.');
};
</script>

<style scoped>
.notes-container {
  overflow-y: auto;
  height: 300px;
}
</style>
