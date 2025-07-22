<template>
  <v-speed-dial
    v-model="fab"
    :top="false"
    :right="true"
    :bottom="true"
    :left="false"
    :direction="'top'"
    :open-on-hover="false"
    transition="slide-y-reverse-transition"
  >
    <template v-slot:activator>
      <v-btn v-model="fab" color="blue darken-2" dark fab>
        <v-icon v-if="fab">mdi-close</v-icon>
        <v-icon v-else>mdi-plus</v-icon>
      </v-btn>
    </template>
    <v-btn fab dark small color="green" @click="emit('open-notes-panel')">
      <v-icon>mdi-note-multiple</v-icon>
    </v-btn>
    <v-btn fab dark small color="indigo" @click="emit('open-shot-detail-panel')">
      <v-icon>mdi-details</v-icon>
    </v-btn>
  </v-speed-dial>
</template>

<script setup>
import { ref } from 'vue';

const fab = ref(false);
const emit = defineEmits(['open-notes-panel', 'open-shot-detail-panel']);
</script>

<style scoped>
/* Styles for FloatingMenu */
</style>