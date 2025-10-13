<template>
  <div>
    <v-divider></v-divider>
    <div class="pa-4">
      <div class="d-flex align-baseline mb-4">
        <div class="text-body-2 mr-2 mt-6">Author :</div>
        <div class="text-subtitle-1 font-weight-medium">{{ username }}</div>
      </div>

      <div class="mb-4">
        <div class="text-body-2 mb-2">Subject :</div>
        <v-text-field
          v-model="subject"
          variant="outlined"
          density="compact"
          hide-details
          placeholder="Enter subject"
        ></v-text-field>
      </div>

      <div class="mb-4">
        <div class="text-body-2 mb-2">Header Note :</div>
        <v-textarea
          v-model="headerNote"
          variant="outlined"
          rows="5"
          no-resize
          hide-details
          placeholder="Enter header note"
        ></v-textarea>
      </div>

      <v-btn color="primary" block @click="save" class="mb-6">Save</v-btn>
    </div>
    <v-divider></v-divider>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useAuth } from "../../composables/useAuth";

// AppSidebar 컴포넌트로부터 사용자 이름을 받기 위한 props
const props = defineProps({
  username: String,
});

const STORAGE_KEY = "pono-global-header";
const { user } = useAuth();

const userSpecificStorageKey = computed(() => {
  if (user.value && user.value.login) {
    return `pono-header-${user.value.login}`;
  }
  return STORAGE_KEY; // Fallback or initial key if user not logged in yet
});

const subject = ref("");
const headerNote = ref("");

// 컴포넌트가 마운트될 때 localStorage에서 데이터를 불러옵니다.
onMounted(() => {
  const savedData = localStorage.getItem(userSpecificStorageKey.value);
  if (savedData) {
    const { subject: savedSubject, headerNote: savedHeaderNote } =
      JSON.parse(savedData);
    subject.value = savedSubject || "";
    headerNote.value = savedHeaderNote || "";
  }
});

const save = () => {
  const subjectValue = subject.value.trim();
  const headerNoteValue = headerNote.value.trim();

  if (!subjectValue && !headerNoteValue) {
    // 두 필드가 모두 비어있으면 localStorage에서 해당 사용자 항목을 제거합니다.
    localStorage.removeItem(userSpecificStorageKey.value);
  } else {
    // 그렇지 않으면, 데이터를 객체로 묶어 localStorage에 저장합니다.
    const dataToSave = {
      subject: subjectValue,
      headerNote: headerNoteValue,
    };
    localStorage.setItem(userSpecificStorageKey.value, JSON.stringify(dataToSave));
  }

  // 다른 컴포넌트에게 데이터가 변경되었음을 알리는 이벤트를 발생시킵니다.
  window.dispatchEvent(new CustomEvent("pono-header-updated"));
};
</script>

<style scoped>
/* 필요한 경우 여기에 스타일 추가 */
</style>
