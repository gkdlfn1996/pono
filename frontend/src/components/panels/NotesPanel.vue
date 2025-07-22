<template>
  <v-navigation-drawer
    :model-value="modelValue"
    :width="400"
    :right="true"
    temporary
    fixed
  >
    <v-toolbar flat>
      <v-toolbar-title>Notes Panel</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn icon @click="emit('update:modelValue', false)">
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </v-toolbar>
    <v-card-text>
      <!-- Notes content will go here -->
      <p>Version Notes and Linked Shot Notes will be displayed here.</p>
    </v-card-text>
  </v-navigation-drawer>
</template>

<script setup>


const props = defineProps({
  modelValue: Boolean,
});

const emit = defineEmits(['update:modelValue']);
</script>

<style scoped>
/* Styles for NotesPanel */
</style>