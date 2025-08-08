<!-- frontend/src/components/versions/VersionCard.vue -->
<template>
  <v-card class="mb-6" variant="outlined">
    <v-card-title class="bg-grey-darken-3">
      <span class="text-h6">{{ version.code }}</span>
    </v-card-title>

    <v-card-text>
      <v-row>
        <!-- 1단: 정보 영역 -->
        <v-col cols="12" md="3">
          <!-- Thumbnail: Responsive container to enforce 16:9 aspect ratio -->
          <v-responsive :aspect-ratio="16/9" class="mb-4 rounded">
            <v-img
              v-if="version.image"
              :src="version.image"
              class="fill-height"
              cover
            >
              <template v-slot:placeholder>
                <div class="d-flex align-center justify-center fill-height">
                  <v-progress-circular color="grey-lighten-4" indeterminate></v-progress-circular>
                </div>
              </template>
              <template v-slot:error>
                <div class="d-flex align-center justify-center fill-height text-center pa-2 bg-grey-darken-1">
                  <span class="text-white">Error loading thumbnail.</span>
                </div>
              </template>
            </v-img>
            <div
              v-else
              class="d-flex align-center justify-center bg-grey-darken-1"
              style="width: 100%; height: 100%;"
            >
              <v-icon size="48" color="grey-lighten-1">mdi-image-off</v-icon>
            </div>
          </v-responsive>

          <div class="text-body-2">
            <p><strong class="mr-2">Final Due:</strong> {{ version.entity && version.entity.Shot && version.entity.Shot.sg_end_date ? version.entity.Shot.sg_end_date : 'N/A' }}</p>
            <p><strong class="mr-2">2D 마감:</strong> {{ version.sg_task && version.sg_task.Task && version.sg_task.Task.due_date ? version.sg_task.Task.due_date : 'N/A' }}</p>
            <p><strong class="mr-2">Artists:</strong> {{ version.user ? version.user.name : 'N/A' }}</p>
          </div>
          <div class="mt-2">
            <v-chip size="small" class="mr-2">{{ version.sg_status_list || 'N/A' }}</v-chip>
          </div>
        </v-col>

        <!-- 2단: Draft Notes 영역 -->
        <v-col cols="12" md="5">
          <!-- My Draft Note -->
          <div class="mb-4">
            <h4 class="text-subtitle-1 font-weight-bold mb-2">My Draft Note</h4>
            <v-textarea
              label="노트 기능 비활성화"
              rows="4"
              variant="outlined"
              disabled
            ></v-textarea>
            <!-- <v-textarea
              label="여기에 노트를 작성하세요"
              rows="4"
              v-model="localNotesContent[version.id]"
              @input="emit('input-note', version.id, localNotesContent[version.id])"
              @blur="emit('save-note', version.id, localNotesContent[version.id])"
              variant="outlined"
              :class="{ 'saving-note': !!isSaving[version.id] }"
            ></v-textarea> -->
          </div>

          <!-- Other's Draft Notes -->
          <div>
            <div class="d-flex align-center mb-2">
              <h4 class="text-subtitle-1 font-weight-bold">Others Draft Notes</h4>
              <!-- <v-btn
                icon="mdi-refresh"
                size="small"
                variant="text"
                :color="notesComposable.hasNewOtherNotes.value[version.id] ? 'red' : ''" @click="emit('reload-other-notes', version.id)"></v-btn> -->
            </div>
            <v-card variant="outlined" class="notes-container" style="min-height: 150px;">
              <!-- <template v-if="notesComposable.otherNotes.value[version.id] && notesComposable.otherNotes.value[version.id].length">
                <div v-for="(note, index) in notesComposable.otherNotes.value[version.id]" :key="note.id">
                  <div class="d-flex justify-space-between align-center px-2 pb-1">
                    <span class="text-subtitle-2 text-grey-darken-1">{{ note.owner.username }}</span>
                    <span class="text-caption text-right text-grey-darken-1">{{ formatDateTime(note.updated_at) }}</span>
                  </div>
                  <v-card-text class="note-content text-body-2 pa-2">
                    {{ note.content }}
                  </v-card-text>
                  <v-divider v-if="index < notesComposable.otherNotes.value[version.id].length - 1"></v-divider>
                </div>
              </template>
              <v-card-text v-else> -->
                <p class="text-grey pa-4 text-center">다른 사용자의 노트가 없습니다.</p>
              <!-- </v-card-text> -->
            </v-card>
          </div>
        </v-col>

        <!-- 3단: Version Notes 영역 -->
        <v-col cols="12" md="4">
          <h4 class="text-subtitle-1 font-weight-bold mb-2">Version Notes</h4>
          <v-card variant="outlined" class="notes-container" style="min-height: 300px;">
            <p class="text-grey pa-4 text-center">버전 노트가 없습니다.</p>
          </v-card>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  version: {
    type: Object,
    required: true,
  },
  // notes: Object,
  // notesComposable: Object,
  // isSaving: Object,
  // sendMessage: Function,
});



// const emit = defineEmits(['save-note', 'input-note', 'reload-other-notes']);
// const localNotesContent = ref({});

// watch(() => props.notes, (newNotes) => {
//   localNotesContent.value = { ...newNotes };
// }, { immediate: true, deep: true });

const formatDateTime = (isoString) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleString('ko-KR', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false
  }).replace(/\.\s/g, '.').slice(0, -1);
};
</script>

<style scoped>
.notes-container {
  overflow-y: auto;
}
.note-content {
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.4;
}
.text-white {
  color: white !important;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.7);
}
:deep(.v-textarea.saving-note .v-field__field) {
  transition: background-color 0.5s ease-in-out;
  background-color: #E0F2F7;
}
</style>