<template>
  <v-navigation-drawer
    app
    :model-value="modelValue"
    @update:modelValue="emit('update:modelValue', $event)"
  >
    <v-list>
      <v-list-item link title="Download Template" disabled></v-list-item>
      <v-list-item link title="Import Bulk Notes" disabled></v-list-item>
      <v-list-item link title="Export Sheet Excel" disabled></v-list-item>

      <v-list-group>
        <template v-slot:activator="{ props }">
          <v-list-item
            v-bind="props"
            title="Edit Header & Subject"
          ></v-list-item>
        </template>
        <HeaderSubjectEditor :username="user?.name" />
      </v-list-group>

      <v-list-item link title="Publish All Notes" @click="emit('open-publish-all-modal')"></v-list-item>
    </v-list>
  </v-navigation-drawer>
</template>

<script setup>
import { useAuth } from "../../composables/useAuth";
import HeaderSubjectEditor from "../sidebar/HeaderSubjectEditor.vue";

const props = defineProps({
  modelValue: Boolean,
});

const emit = defineEmits(["update:modelValue", "open-publish-all-modal"]);

const { user } = useAuth();
</script>

<style scoped>
/* Styles for AppSidebar */
</style>