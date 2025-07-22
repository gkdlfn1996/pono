<template>
  <v-navigation-drawer
    :model-value="modelValue"
    :width="600"
    :right="true"
    temporary
    fixed
  >
    <v-toolbar flat>
      <v-toolbar-title>Shot Detail Panel</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn icon @click="emit('update:modelValue', false)">
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </v-toolbar>
    <v-card-text>
      <!-- Shot Detail content will go here -->
      <p>Shot thumbnail, metadata, and ShotGrid data will be displayed here.</p>
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
/* Styles for ShotDetailPanel */
</style>