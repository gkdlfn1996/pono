<template>
  <div>
    <div class="d-flex align-center mb-2">
      <div class="text-body-2 font-weight-bold" style="width: 40px;">To:</div>
      <v-chip v-if="currentToUser" size="small" color="primary" variant="tonal">
        {{ currentToUser.name }}
      </v-chip>
    </div>
    <div class="d-flex">
      <div class="text-body-2 font-weight-bold" style="width: 40px;">CC:</div>
      <div class="cc-autocomplete-wrapper flex-grow-1">
      <v-autocomplete
        v-model="currentCcUsers"
        v-model:search="newCcSearchQuery"
        :items="filteredSuggestions"
        :loading="isLoadingCcList"
        no-filter
        label=""
        variant="outlined"
        density="compact"
        hide-details
        clearable
        return-object
        @blur="handleAutocompleteBlur"
        @keydown.enter.prevent="handleAutocompleteEnter"
        multiple
        chips
        closable-chips
      >
        <!-- 칩의 표시 형식을 제어하는 슬롯 -->
        <template v-slot:chip="{ props, item }">
          <v-chip 
            v-bind="props" 
            :prepend-icon="item.raw.type === 'Group' ? 'mdi-account-multiple' : 'mdi-account'"
            :text="item.raw.type === 'Group' ? item.raw.code : item.raw.name"
          ></v-chip>
        </template>
        <!-- 드롭다운 목록의 표시 형식을 제어하는 슬롯 -->
        <template v-slot:item="{ props, item }">
          <v-list-item 
            v-bind="props" 
            :prepend-icon="item.raw.type === 'Group' ? 'mdi-account-multiple' : 'mdi-account'"
            :title="item.raw.type === 'Group' ? item.raw.code : `${item.raw.name} (${item.raw.login})`"
          ></v-list-item>
        </template>
      </v-autocomplete>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue';
import { useShotGridData } from '@/composables/useShotGridData';

const props = defineProps({
  toUser: {
    type: Object,
    required: true,
  },
  ccUsers: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(['update:ccUsers']);

const {
  allCcList,
  isLoadingCcList,
  loadAllCcList,
} = useShotGridData();

const currentToUser = ref(props.toUser);
const currentCcUsers = ref([]);
const newCcSearchQuery = ref('');

/**
 * 부모로부터 받은 ccUsers prop을 내부 상태(currentCcUsers)와 동기화합니다.
 */
watch(() => props.ccUsers, (newCc) => {
  currentCcUsers.value = [...newCc];
}, { immediate: true });

/**
 * 부모로부터 받은 toUser prop이 변경될 때 내부 상태(currentToUser)를 업데이트합니다.
 */
watch(() => props.toUser, (newToUser) => {
  currentToUser.value = newToUser;
}, { deep: true });

/**
 * v-autocomplete의 v-model(currentCcUsers)이 변경될 때 부모 컴포넌트에 변경사항을 알립니다.
 * @param {Array} newSelectedUsers - v-autocomplete에 의해 업데이트된 CC 사용자 목록.
 */
watch(currentCcUsers, (newSelectedUsers) => {
  emit('update:ccUsers', newSelectedUsers);
}, { deep: true });  



/**
 * 컴포넌트가 마운트될 때, 모든 CC 목록을 비동기적으로 불러옵니다.
 */ 
onMounted(() => {
  loadAllCcList(); // 필요 시 모든 CC 목록 정보 로드 시작
});  

/**
 * 자동 완성 제안 목록을 계산하는 computed 속성.
 * 검색어와 일치하고, 이미 'To' 또는 'CC'에 없는 사용자만 필터링합니다.
 */ 
const filteredSuggestions = computed(() => {
  if (!allCcList.value) return [];
  // 검색어가 null 또는 undefined일 경우를 대비하여 안전하게 처리합니다.
  const lowerCaseQuery = (newCcSearchQuery.value || '').toLowerCase();

  // 이미 'To' 또는 'CC'에 있는 사용자는 제외
  const existingUserIds = new Set([
    currentToUser.value.id,
    ...currentCcUsers.value.map(u => u.id)
  ]);  

  return allCcList.value.filter(item => {
    const name = (item.type === 'Group' ? item.code : item.name) || '';
    const login = (item.login || '');
    return !existingUserIds.has(item.id) &&
           (name.toLowerCase().includes(lowerCaseQuery) || login.toLowerCase().includes(lowerCaseQuery));
  });         
});  

/**
 * v-autocomplete 입력창에서 포커스가 벗어났을 때 호출되는 핸들러.
 */ 
const handleAutocompleteBlur = () => {
  // 포커스가 벗어날 때 검색어를 비웁니다.
  newCcSearchQuery.value = null;
};  

/**
 * v-autocomplete 입력창에서 Enter 키를 눌렀을 때 호출되는 핸들러.
 */ 
const handleAutocompleteEnter = (event) => {
  event.preventDefault(); // Enter 키 입력 시 기본 폼 제출 동작을 방지합니다.
  if (newCcSearchQuery.value && filteredSuggestions.value.length > 0) {
    const itemToAdd = filteredSuggestions.value[0];
    if (!currentCcUsers.value.some(u => u.id === itemToAdd.id)) {
      currentCcUsers.value.push(itemToAdd);
    }  
    newCcSearchQuery.value = null; // 검색어 초기화 (입력창 비우기)
  }  
};  


</script>

<style scoped>
.cc-autocomplete-wrapper {
    flex: 1 1 0;
    min-width: 0;
}

</style>