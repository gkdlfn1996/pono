<template>
  <!-- 3단: Version Notes 영역 -->
  <div>
    <h4 class="text-subtitle-1 font-weight-bold mb-2">Version Notes</h4>
    <v-card variant="outlined" class="notes-container" style="min-height: 300px;">
      <p class="text-grey pa-4 text-center">버전 노트가 없습니다.</p>
    </v-card>
  </div>
</template>

<script setup>
const props = defineProps({
  version: {
    type: Object,
    required: true,
  },
});
</script>

<style scoped>
.notes-container {
  overflow-y: auto;
}
</style>