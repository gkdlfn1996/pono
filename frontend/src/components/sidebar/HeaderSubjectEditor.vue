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
import { ref } from 'vue';

// AppSidebar 컴포넌트로부터 사용자 이름을 받기 위한 props
const props = defineProps({
  username: String,
});

const subject = ref('');
const headerNote = ref('');

const save = () => {
  // TODO: 실제 저장 로직은 추후 구현합니다.
  console.log('Saving:', { subject: subject.value, headerNote: headerNote.value });
};
</script>

<style scoped>
/* 필요한 경우 여기에 스타일 추가 */
</style>
