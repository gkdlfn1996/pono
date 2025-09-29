<template>
  <v-navigation-drawer app
    :model-value="modelValue"
    @update:modelValue="emit('update:modelValue', $event)"
  >
    <v-list>
      <v-list-item link title="Download Template" disabled></v-list-item>
      <v-list-item link title="Import Bulk Notes" disabled></v-list-item>
      <v-list-item link title="Export Sheet Excel" disabled></v-list-item>
      <v-list-item link title="Edit Header & Subject"></v-list-item>
      <v-list-item link title="Publish All Notes"></v-list-item>
    </v-list>
  </v-navigation-drawer>
</template>

<script setup>


const props = defineProps({
  modelValue: Boolean,
});

const emit = defineEmits(['update:modelValue']);
</script>

<style scoped>
/* Styles for AppSidebar */
</style>