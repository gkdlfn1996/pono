<template>
  <v-field
    :disabled="props.disabled"
    class="search-bar-container"
    @click="focusInput"
    variant="outlined"
    color="primary"
  >
    <template #prepend-inner>
      <v-icon class="mr-2">mdi-magnify</v-icon>
    </template>

    <div class="chips-area">
      <v-chip
        v-for="(label, index) in searchLabels"
        :key="`${label.type}-${label.value}`"
        closable
        @click:close.stop="removeChip(index)"
        class="mr-1"
        size="small"
      >
        <span class="font-weight-bold">{{ label.type }}:</span>&nbsp;{{ label.value }}
      </v-chip>

      <div v-if="activeType" class="d-inline-flex align-center">
        <v-chip class="mr-1 temp-chip" size="small">
          <span class="font-weight-bold">{{ activeType }}:</span>
        </v-chip>
        
        <v-autocomplete
          ref="valueInputRef"
          v-model:search="valueSearchQuery"
          :items="valueSuggestions"
          @keydown.enter.prevent="onValueEnter"
          @keydown.esc.prevent="cancelChipCreation"
          @keydown.backspace="onValueInputBackspace"
          @blur="onValueInputBlur"
          @update:model-value="selectValue"
          @update:menu="isValueMenuOpen = $event"
          variant="plain"
          density="compact"
          menu-icon=""
          hide-details
          autofocus
          class="value-input"
        ></v-autocomplete>
      </div>
    </div>

    <v-autocomplete
      v-if="!activeType"
      ref="typeInputRef"
      v-model:search="typeSearchQuery"
      :items="typeSuggestions"
      :placeholder="placeholder"
      @keydown.enter.prevent="onTypeEnter"
      @keydown="onTypeInputKeydown"
      @keydown.backspace="onTypeInputBackspaceMain"
      @update:menu="isTypeMenuOpen = $event"
      @update:model-value="selectType"
      menu-icon=""
      variant="plain"
      density="compact"
      hide-details
      hide-no-data
      class="type-input"
    >
    </v-autocomplete>
  </v-field>
</template>

<script setup>
import { ref, computed, nextTick, watch} from 'vue';
import { useShotGridData } from '../../composables/useShotGridData';

// props 정의
const props = defineProps({
  disabled: Boolean,
});

const emit = defineEmits(['filters-complete']);
// --- 상태 (State) ---
// 최종 확정된 필터 칩 목록 { type, value }
const searchLabels = ref([]); 
// 현재 편집중인 필터 타입 (e.g., 'Shot')
const activeType = ref(null); 
// 타입 입력창의 텍스트 모델
const typeSearchQuery = ref('');

// 값 입력창의 텍스트 모델
const valueSearchQuery = ref('');
// 값 선택 메뉴의 열림/닫힘 상태
const isValueMenuOpen = ref(false);
// 타입 선택 메뉴의 열림/닫힘 상태
const isTypeMenuOpen = ref(false);

// --- DOM 참조 ---
// 타입 입력용 v-autocomplete 컴포넌트 참조
const typeInputRef = ref(null);
// 값 입력용 v-autocomplete 컴포넌트 참조
const valueInputRef = ref(null);

// --- 중앙 데이터 저장소 ---
const { suggestionSources } = useShotGridData();

// --- Computed ---

// 필터 타입 제안 목록
const typeSuggestions = computed(() => {
  const query = typeSearchQuery.value.toLowerCase();
  
  // 이미 선택된 타입을 제외한 사용 가능한 타입 목록
  const availableTypes = allFilterTypes.filter(
    type => !searchLabels.value.some(label => label.type === type.key)
  );

  // 검색어가 없으면 전체 목록 반환
  if (!query) {
    return availableTypes.map(t => t.name);
  }

  // 검색어가 있으면, 필터링 후 정렬
  return availableTypes
    .map(t => t.name)
    .filter(name => name.toLowerCase().includes(query))
    .sort((a, b) => {
      const a_starts = a.toLowerCase().startsWith(query);
      const b_starts = b.toLowerCase().startsWith(query);
      if (a_starts && !b_starts) return -1; // 시작하는 단어 우선
      if (!a_starts && b_starts) return 1;
      return a.localeCompare(b); // 그 외에는 알파벳순
    });
});

// 필터 값 제안 목록
const valueSuggestions = computed(() => {
  if (!activeType.value) return [];
  return getSuggestionsForType(activeType.value);
});

// 입력창에 동적으로 표시될 placeholder
const placeholder = computed(() => {
  if (activeType.value || searchLabels.value.length > 0) return '';
  return 'Search or Filter';
});

// --- 데이터 (Data) ---
// 지원하는 모든 필터 타입 정의
const allFilterTypes = [
  { name: 'Shot', key: 'Shot' },
  { name: 'Asset', key: 'Asset' },
  { name: 'Playlist', key: 'Playlist' },
  { name: 'Version', key: 'Version' },
  { name: 'Subject', key: 'Subject' },
  { name: 'Tag', key: 'Tag' },
];

// --- 메소드 (Methods) ---

// 타입에 따른 제안 목록을 반환하는 헬퍼 함수
const getSuggestionsForType = (type) => {
  return suggestionSources.value[type] || [];
};

// 상황에 맞는 입력창에 포커스를 주는 함수
const focusInput = () => {
  nextTick(() => {
    if (activeType.value) {
      valueInputRef.value?.focus();
    } else {
      typeInputRef.value?.focus();
    }
  });
};

// 타입 제안 목록에서 항목을 '클릭'으로 선택했을 때
const selectType = (selectedType) => {
  if (!selectedType) return;
  const typeInfo = allFilterTypes.find(t => t.name === selectedType);
  if (typeInfo) {
    activeType.value = typeInfo.key;
    typeSearchQuery.value = '';
    nextTick(() => valueInputRef.value?.focus());
  }
};

// 타입 입력창에서 'Enter' 키를 눌렀을 때
const onTypeEnter = () => {
  // 조건: 입력창이 비어있거나, 확정된 칩이 하나 이상 있을 때
  if (typeSearchQuery.value === '') {
    emit('filters-complete', searchLabels.value);
    // 콘솔에 필터 완료 신호를 보냈다는 로그를 남깁니다.
    console.log('\'Enter\' 키 입력 감지. filters-complete 신호를 보냅니다:', searchLabels.value);
    return;
  }

  // 위의 조건이 아닐 때 (즉, 새 칩을 만드는 과정일 때)만 아래 로직을 실행합니다.
  if (typeSuggestions.value.length > 0 && typeSearchQuery.value) {
    selectType(typeSuggestions.value[0]);
  }
};

// 타입 입력창에서 키보드 입력을 제어하는 핸들러
const onTypeInputKeydown = (event) => {
  // 모든 필터가 선택되었고, IME 입력 중이 아니며, 제어키가 아닌 일반 문자 입력일 경우에만 preventDefault
  if (allFilterTypes.length === searchLabels.value.length && !event.isComposing && event.key.length === 1 && !event.ctrlKey && !event.metaKey) {
    event.preventDefault();
  }
};

// 메인 입력창에서 'Backspace' 키를 눌렀을 때 (확정된 칩 삭제)
const onTypeInputBackspaceMain = () => {
  if (typeSearchQuery.value === '' && searchLabels.value.length > 0) {
    // 메뉴가 열려있는 상태에서 리사이즈가 일어나면 에러가 발생하므로,
    // 메뉴를 먼저 닫고 (blur) 칩을 삭제한다.
    if (isTypeMenuOpen.value) {
      typeInputRef.value.blur();
    }
    searchLabels.value.pop();
    // 메뉴를 닫고 칩을 삭제한 뒤, 다시 포커스를 되돌려준다.
    focusInput();
  }
};

// 값 제안 목록에서 항목을 '클릭'으로 선택했을 때
const selectValue = (value) => {
  if (value) {
    finalizeChip(value);
  }
};

// 값 입력창에서 'Enter' 키를 눌렀을 때 (free-solo 지원)
const onValueEnter = () => {
  finalizeChip(valueSearchQuery.value);
};

// 값 입력창에서 'Backspace' 키를 눌렀을 때 (임시 칩 취소)
const onValueInputBackspace = () => {
  if (valueSearchQuery.value === '') {
    cancelChipCreation();
  }
};

// ESC 키로 임시 칩을 취소하는 함수
const cancelChipCreation = () => {
    finalizeChip(null);
};

// 칩 생성을 확정하고 상태를 초기화하는 함수
const finalizeChip = (value) => {
  if (value) {
    searchLabels.value.push({ type: activeType.value, value });
  }
  activeType.value = null;
  valueSearchQuery.value = '';
  nextTick(() => typeInputRef.value?.focus());
};

// 칩의 'x' 버튼을 눌러 삭제하는 함수
const removeChip = (index) => {
  searchLabels.value.splice(index, 1);
  focusInput();
};

// 값 입력창의 포커스가 사라졌을 때
const onValueInputBlur = () => {
  setTimeout(() => {
    if (isValueMenuOpen.value) return;
    if (!valueSearchQuery.value) {
      finalizeChip(null);
    }
  }, 200);
};

// typeSearchQuery의 변화를 감지하여 모든 필터가 선택된 경우 초기화
watch(typeSearchQuery, (newValue) => {
  if (allFilterTypes.length === searchLabels.value.length && newValue !== '') {
    // 모든 필터가 선택된 상태에서 새로운 값이 들어오면 무시하고 초기화
    typeSearchQuery.value = '';
  }
});

</script>

<style scoped>
.search-bar-container {
  width: 100%;
  max-width: 1000px;
  /* v-field가 자동으로 스타일을 관리하므로 수동 스타일을 최소화합니다. */
}

:deep(.v-field__field) {
  /* v-field 내부의 flex 컨테이너 스타일 조정 */
  display: flex;
  align-items: center;
  gap: 6px;
  height: auto;
  min-height: 40px;
}

.chips-area {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.type-input, .value-input {
  flex-grow: 1;
  min-width: 120px;
}

.temp-chip {
  pointer-events: none;
}

:deep(.v-field__overlay) {
    background: transparent;
}

:deep(.v-field__input) {
  padding-top: 0;
  padding-bottom: 0;
  align-items: center;
}
</style>


<!--
@file SearchBar.vue
@description
사용자가 필터 조건을 점진적으로 추가하여 검색할 수 있는 복합 검색창 컴포넌트.
'하이브리드 입력 방식'을 사용하여, 하나의 입력창처럼 보이지만 내부적으로는
'타입 선택'과 '값 입력'의 두 단계를 나누어 처리함으로써 복잡한 UI/UX를 구현함.

@ 주요 기능 및 동작 방식
1. **기본 구조 (하이브리드 방식):**
   - 겉보기에는 하나의 텍스트 입력 필드처럼 보이지만, 내부적으로는 두 개의 v-autocomplete가 상태에 따라 전환됨.
   - `activeType` 상태 값의 유무에 따라 '타입 검색 모드'와 '값 입력 모드'로 나뉨.
   - 최종 확정된 필터들은 v-chip 컴포넌트로 표시됨.
   
2. **상태 관리 (State Management):**
   - `searchLabels`: {type, value} 객체 배열. 최종 확정된 필터 칩 목록.
   - `activeType`: 현재 컴포넌트의 핵심 상태. `null`이면 '타입 선택', 값이 있으면(e.g., 'Shot') '값 선택' 단계.
   - `typeSearchQuery`: '타입 선택' v-autocomplete의 입력 모델.
   - `valueSearchQuery`: '값 입력' v-autocomplete의 입력 모델.
   - `isTypeMenuOpen` / `isValueMenuOpen`: 각 메뉴의 열림 상태를 추적하여 특수 상황(e.g., blur, backspace)의 버그를 방지.

3. **사용자 시나리오 (User Workflow):**
   - **1단계: 타입 선택**
     - 사용자가 비어있는 검색창을 클릭하거나 타이핑을 시작.
     - `typeSuggestions`에 의해 사용 가능한 필터 '타입' 목록이 제안됨. (이미 선택된 타입은 제외)
     - 제안 목록은 사용자의 입력값으로 시작하는 항목을 우선하여 정렬됨.
     - 사용자는 목록을 클릭하거나, Enter 키를 눌러 타입을 선택.
     - 모든 타입이 소진되면 입력창은 비활성화되며, 칩을 삭제하면 다시 활성화됨.

   - **2단계: 값 입력**
     - 타입이 선택되면 `activeType`에 해당 타입이 저장되고, UI가 '값 입력' 모드로 전환됨.
     - 화면에 'Shot:' 과 같이 x가 없는 임시 칩이 나타남.
     - 값 입력을 위한 두 번째 v-autocomplete가 활성화되고 포커스를 받음.
     - `valueSuggestions`에 의해 해당 타입에 맞는 '값' 목록이 제안됨.
     - 사용자는 목록을 클릭하거나, Enter 키를 눌러 값을 선택.
     - 목록에 없는 값도 직접 타이핑하여 입력 가능 (Free-solo).
     - 이 단계에서 ESC 키나, 빈 입력창에서 Backspace 키를 누르면 작업이 취소되고 '타입 선택' 단계로 돌아감.

   - **3단계: 칩 확정 및 삭제**
     - 값이 확정되면, {type, value} 형태의 객체가 `searchLabels` 배열에 추가됨.
     - 화면에 x 버튼이 있는 최종 칩이 렌더링됨.
     - 컴포넌트는 다시 `activeType: null` 상태가 되어 다음 필터를 입력받을 준비를 함.
     - 칩의 x 버튼으로 개별 삭제가 가능.
     - 타입 입력창이 비어있을 때 Backspace를 누르면 마지막 칩부터 순서대로 삭제됨.
       (이때, 제안 메뉴가 열려있으면 먼저 닫아서 `ResizeObserver` 에러를 방지)
 -->