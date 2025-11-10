<template>
  <v-navigation-drawer
    app
    :model-value="modelValue"
    @update:modelValue="emit('update:modelValue', $event)"
  >
    <v-list>
      <v-list-item link title="How to Use" @click="showUserManual"></v-list-item>
      <v-divider></v-divider>
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
import apiClient from '@/plugins/apiClient';
import HeaderSubjectEditor from "../sidebar/HeaderSubjectEditor.vue";

const props = defineProps({
  modelValue: Boolean,
});

const emit = defineEmits(["update:modelValue", "open-publish-all-modal"]);

const { user } = useAuth();

const showUserManual = async () => {
  try {
    const response = await apiClient.get('/api/utils/user-manual');
    const newTab = window.open();
    if (newTab) {
      newTab.document.write(response.data);
      newTab.document.close();
    } else {
      alert("팝업이 차단되었습니다. 팝업을 허용하고 다시 시도해주세요.");
    }
  } catch (error) {
    console.error("Failed to load user manual:", error);
    alert("사용자 매뉴얼을 불러오는 데 실패했습니다.");
  }
};
</script>

<style scoped>
/* Styles for AppSidebar */
</style>