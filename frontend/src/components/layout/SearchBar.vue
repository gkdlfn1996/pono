<template>
  <div class="search-bar-container">
    <!-- 2. 필터 종류 선택 메뉴 -->
    <v-menu v-model="showFilterTypeMenu" offset="4">
      <template v-slot:activator="{ props: menuProps }">
        <!-- 1. 겉모습만 텍스트 필드인 '가짜 검색창' div -->
        <div
          ref="searchContainerRef"
          class="fake-text-field"
          v-bind="menuProps"
          @click="onSearchbarClick"
          tabindex="0"
        >
          <v-icon class="ml-n1" color="grey-darken-1">mdi-magnify</v-icon>

          <!-- Placeholder -->
          <span
            v-if="!searchLabels.length && !editingChip"
            class="placeholder-text"
          >
            Search or Filter
          </span>

          <!-- 확정된 칩들 -->
          <v-chip
            v-for="(label, index) in searchLabels"
            :key="`label-${index}`"
            closable
            @click:close.stop="removeSearchLabel(index)"
            class="mr-1"
            size="small"
          >
            <span class="font-weight-bold">{{ label.type }}:</span>&nbsp;{{ label.value }}
          </v-chip>

          <!-- 편집 중 UI: 임시 칩 -->
          <div v-if="editingChip" class="d-flex align-center" @click.stop style="flex-shrink: 0;">
            <v-chip class="mr-1" size="small">
              {{ editingChip.type }}:
            </v-chip>
            <v-autocomplete
              ref="autocompleteRef"
              v-model:search="searchQuery"
              :items="shotSuggestions"
              :free-solo="true"
              :open-on-focus="true"
              autofocus
              density="compact"
              variant="plain"
              hide-details
              @keydown.enter.prevent="finalizeChip"
              @keydown.esc.prevent="cancelChipCreation"
              @blur="handleAutocompleteBlur"
              placeholder="Enter Name..."
              menu-icon=""
              style="min-width: 150px"
            ></v-autocomplete>
          </div>
        </div>
      </template>

      <v-list :style="{ minWidth: activatorWidth + 'px' }">
        <v-list-item
          v-for="option in availableFilterTypes"
          :key="option.key"
          @click="() => startChipCreation(option.key)"
          :disabled="option.disabled"
        >
          <v-list-item-title>{{ option.name }}</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>

    <!-- 3. 실제 값 입력을 위한 자동완성 메뉴 -->
    <v-menu
      v-model="showAutocompleteMenu"
      :activator="editingChipRef"
      offset="4"
      :close-on-content-click="false"
    >
      <v-autocomplete
        ref="autocompleteRef"
        v-model="searchQuery"
        :items="shotSuggestions"
        autofocus
        density="compact"
        variant="solo"
        hide-details
        @keydown.enter.prevent="finalizeChip"
        @keydown.esc.prevent="cancelChipCreation"
        placeholder="Enter Shot Name..."
        style="min-width: 200px"
      ></v-autocomplete>
    </v-menu>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, computed } from 'vue';

// --- 상태 관리 ---
const searchLabels = ref([]); // 확정된 필터 칩 목록
const editingChip = ref(null); // {type, value} 형태의 편집중인 칩 정보
const searchQuery = ref(''); // 자동완성 입력값

const showFilterTypeMenu = ref(false); // 필터 종류 메뉴 제어

// DOM 요소 참조
const searchContainerRef = ref(null);
const autocompleteRef = ref(null);

const activatorWidth = ref(0);
const shotSuggestions = ref(['SHOT_010', 'SHOT_020', 'SHOT_030']); // 임시 자동완성 데이터

// 모든 필터 타입 정의 (비활성화된 항목 포함)
const allFilterTypes = [
  { name: 'Shot', key: 'Shot' },
  { name: 'Playlist', key: 'Playlist' },
  { name: 'Version', key: 'Version' },
  { name: 'Subject', key: 'Subject' },
  { name: 'Tag', key: 'Tag' },
];

// 현재 활성화 가능한 필터 타입 (computed 속성)
const availableFilterTypes = computed(() => {
  const activeTypes = new Set(searchLabels.value.map(label => label.type));
  return allFilterTypes.filter(type => {
    // 이미 활성화된 타입이 아니거나, 원래부터 비활성화된 타입인 경우에만 목록에 포함
    return !activeTypes.has(type.key) || type.disabled;
  }).map(type => ({
    ...type,
    disabled: type.disabled, // 원래 비활성화된 상태는 유지
  }));
});

// 현재 편집 중인 칩 타입에 따른 자동완성 목록 (computed 속성)
const autocompleteItems = computed(() => {
  if (!editingChip.value) return [];

  switch (editingChip.value.type) {
    case 'Shot':
      return shotSuggestions.value;
    case 'Playlist':
      return playlistSuggestions.value;
    case 'Version':
      return versionSuggestions.value;
    case 'Subject':
      return subjectSuggestions.value;
    case 'Tag':
      return tagSuggestions.value;
    default:
      return [];
  }
});

// --- 함수 ---

const onSearchbarClick = () => {
  if (!editingChip.value) {
    activatorWidth.value = searchContainerRef.value?.clientWidth;
    showFilterTypeMenu.value = true;
  }
};

const startChipCreation = (type) => {
  // 다른 칩 편집중이면 생성 방지
  if (editingChip.value) return;

  editingChip.value = { type: type, value: '' };
  showFilterTypeMenu.value = false;

  // 자동완성 필드에 포커스
  nextTick(() => {
    autocompleteRef.value?.focus();
  });
};

const finalizeChip = () => {
  if (editingChip.value && searchQuery.value.trim()) {
    searchLabels.value.push({
      type: editingChip.value.type,
      value: searchQuery.value,
    });
    cancelChipCreation();
    nextTick(() => {
      searchContainerRef.value?.focus(); // 다음 입력을 위해 검색창에 포커스
    });
  }
};

const cancelChipCreation = () => {
  editingChip.value = null;
  searchQuery.value = '';
};

const removeSearchLabel = (index) => {
  searchLabels.value.splice(index, 1);
};

const handleAutocompleteBlur = () => {
  // 약간의 딜레이 후, 입력값이 없으면 칩 생성 취소
  // (v-autocomplete의 항목 클릭 이벤트를 위해 딜레이 필요)
  setTimeout(() => {
    if (editingChip.value && !searchQuery.value) {
      cancelChipCreation();
    }
  }, 200);
};
</script>

<style scoped>
.search-bar-container {
  position: relative;
  width: 100%;
  max-width: 800px; /* 혹은 부모에 맞춰서 조정 */
}

.fake-text-field {
  display: flex;
  align-items: center;
  width: 100%;
  min-height: 40px; /* v-text-field density="compact" 높이 */
  padding: 0 12px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 4px;
  cursor: text;
  gap: 6px;
  transition: border-color 0.15s ease-in-out;
}

.fake-text-field:hover {
  border-color: rgba(var(--v-border-color), 1);
}

.placeholder-text {
  color: rgba(var(--v-theme-on-surface), var(--v-medium-emphasis-opacity));
  font-size: 1rem;
}
</style>
