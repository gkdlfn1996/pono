<template>
  <!-- 2단: Draft Notes 영역 -->
  <div class="d-flex flex-column h-100">
    <!-- d-flex: flexbox 컨테이너 -->
    <!-- flex-column: 세로 방향 정렬 -->
    <!-- h-100: 부모 높이를 100% 채움 -->

    <!-- My Draft Note 섹션 -->
    <div class="my-notes-section mb-4">
      <!-- my-notes-section: 사용자 정의 클래스 -->
      <!-- mb-4: margin-bottom -->
      <div class="d-flex align-center mb-2">
        <!-- d-flex: flexbox 컨테이너 -->
        <!-- align-center: 수직 중앙 정렬 -->
        <!-- mb-2: margin-bottom -->
        <h4 class="text-subtitle-1 font-weight-bold">My Draft Note</h4>
        <!-- h4: 제목 태그 -->
        <!-- text-subtitle-1: Vuetify 제공 소제목 스타일 -->
        <!-- font-weight-bold: 굵게 표시 -->
        <v-spacer></v-spacer>
        <!-- v-spacer: 남는 공간 채움 -->
        <v-btn
          icon="mdi-paperclip"
          <!-- icon: 버튼 아이콘 -->
          <!-- mdi-paperclip: 클립 모양 아이콘 -->
          variant="text"
          <!-- variant: 버튼 스타일 (텍스트 전용) -->
          size="small"
          <!-- size: 버튼 크기 -->
          @click="showAttachmentModal = true"
          <!-- @click: 클릭 이벤트 (모달 열기) -->
          density="compact"
          <!-- density: 내부 여백을 줄여 컴팩트하게 -->
        ></v-btn>
      </div>

      <!-- 고정 높이 컨테이너 -->
      <div class="note-input-container" style="height: 150px;">
        <!-- note-input-container: 사용자 정의 클래스 -->
        <!-- style: 높이를 150px로 고정 -->
        <v-textarea
          label="여기에 노트를 작성하세요"
          <!-- label: 입력창 안내 문구 -->
          :model-value="localContent"
          <!-- :model-value: Vue 반응형 데이터 바인딩 -->
          @update:model-value="onInput"
          <!-- 값 변경 시 onInput 실행 -->
          @focus="isFocused = true"
          <!-- focus 이벤트 발생 시 isFocused true 설정 -->
          @blur="onBlur"
          <!-- blur 이벤트 발생 시 onBlur 실행 -->
          variant="outlined"
          <!-- variant: 외곽선 스타일 -->
          :class="{ 'saved-note': props.isSaved }"
          <!-- 조건부 클래스 바인딩: 저장 시 saved-note 클래스 적용 -->
          no-resize
          <!-- no-resize: 사용자가 크기 조절 불가 -->
          class="fill-height"
          <!-- fill-height: 부모 높이 채움 -->
        ></v-textarea>
      </div>

      <!-- 내 첨부파일 목록 -->
      <div v-if="myAttachments.length > 0" class="attachments-section mt-2 pa-2 rounded" style="border: 1px solid #E0E0E0;">
        <!-- v-if: myAttachments 배열에 항목이 있을 때만 표시 -->
        <!-- attachments-section: 사용자 정의 클래스 -->
        <!-- mt-2: margin-top -->
        <!-- pa-2: padding -->
        <!-- rounded: 모서리 둥글게 -->
        <div class="text-caption font-weight-bold mb-1">첨부파일</div>
        <!-- text-caption: 작은 글씨 -->
        <!-- font-weight-bold: 굵게 -->
        <!-- mb-1: margin-bottom -->
        <div v-for="(attachment, index) in myAttachments" :key="index" class="d-flex align-center text-caption">
          <!-- v-for: 배열 반복 렌더링 -->
          <!-- :key="index": Vue 성능 최적화를 위한 고유 키 -->
          <!-- d-flex: flexbox -->
          <!-- align-center: 수직 중앙 정렬 -->
          <!-- text-caption: 작은 글씨 -->
          <v-icon size="small" class="mr-1">{{ getIconForFile(attachment.name) }}</v-icon>
          <!-- v-icon: 아이콘 표시 -->
          <!-- size="small": 작은 크기 -->
          <!-- mr-1: margin-right -->
          <!-- getIconForFile: 파일 확장자에 따라 아이콘 결정 -->
          <a :href="attachment.url" target="_blank" class="text-decoration-none text-blue-lighten-2">{{ attachment.name }}</a>
          <!-- a: 하이퍼링크 태그 -->
          <!-- :href: 첨부파일 URL -->
          <!-- target="_blank": 새 탭에서 열기 -->
          <!-- text-decoration-none: 밑줄 제거 -->
          <!-- text-blue-lighten-2: 파란색 텍스트 -->
          <v-spacer></v-spacer>
          <!-- v-spacer: 남은 공간 차지 -->
          <v-btn icon variant="text" size="x-small" color="grey" @click="deleteMyAttachment(index)">
            <!-- v-btn: 버튼 -->
            <!-- icon: 아이콘 버튼 -->
            <!-- variant="text": 텍스트 전용 버튼 -->
            <!-- size="x-small": 매우 작은 버튼 -->
            <!-- color="grey": 회색 -->
            <!-- @click: 첨부파일 삭제 -->
            <v-icon>mdi-close-circle</v-icon>
            <!-- mdi-close-circle: 닫기 아이콘 -->
          </v-btn>
        </div>
      </div>
    </div>

    <!-- Other's Draft Notes 섹션 -->
    <div class="other-notes-section">
      <!-- other-notes-section: 사용자 정의 클래스 -->
      <div class="d-flex align-center mb-2">
        <!-- d-flex: flexbox -->
        <!-- align-center: 수직 중앙 정렬 -->
        <!-- mb-2: margin-bottom -->
        <h4 class="text-subtitle-1 font-weight-bold">Others Draft Notes</h4>
        <!-- h4: 제목 -->
        <!-- text-subtitle-1: Vuetify 스타일 -->
        <!-- font-weight-bold: 굵게 -->
      </div>
      <v-card 
        variant="outlined" 
        <!-- variant: 외곽선 카드 -->
        class="notes-container"
        <!-- notes-container: 사용자 정의 클래스 -->
        style="height: 150px; overflow-y: auto;"
        <!-- height: 고정 높이 150px -->
        <!-- overflow-y: 세로 스크롤 허용 -->
        @click="handleInteraction" 
        <!-- @click: 카드 클릭 시 handleInteraction 실행 -->
        @scroll.passive="handleInteraction" 
        <!-- @scroll: 스크롤 이벤트 발생 시 handleInteraction 실행 -->
        <!-- passive: 성능 최적화 -->
        :ripple="false"
        <!-- ripple: 클릭 시 파동효과 비활성화 -->
      >
        <template v-if="props.otherNotes && props.otherNotes.length">
          <!-- v-if: otherNotes 배열 존재 및 길이 > 0일 때 -->
          <div 
            v-for="(note, index) in props.otherNotes" 
            :key="note.id" 
            :ref="el => noteRefs[note.id] = el"
            :data-note-id="note.id"
            class="note-item"
            :class="{ 'new-note-highlight': props.newNoteIds.has(note.id) }"
            @click="onNoteClick(note)"
          >
            <!-- v-for: 반복 렌더링 -->
            <!-- :ref: DOM 참조 저장 -->
            <!-- :data-note-id: 커스텀 데이터 속성 -->
            <!-- class: note-item 사용자 정의 클래스 -->
            <!-- :class: 조건부 클래스 바인딩 (새 노트 하이라이트) -->
            <!-- @click: 노트 클릭 시 onNoteClick 실행 -->

            <!-- 다른 사람 노트의 첨부파일 목록 -->
            <div v-if="note.attachments && note.attachments.length > 0" class="attachments-section ma-2 pa-2 rounded" style="border: 1px solid #E0E0E0;">
              <!-- v-if: 첨부파일 존재 시 표시 -->
              <!-- ma-2: margin -->
              <!-- pa-2: padding -->
              <!-- rounded: 모서리 둥글게 -->
              <div class="text-caption font-weight-bold mb-1">첨부파일</div>
              <!-- text-caption: 작은 글씨 -->
              <!-- font-weight-bold: 굵게 -->
              <!-- mb-1: margin-bottom -->
              <div v-for="(attachment, attIndex) in note.attachments" :key="attIndex" class="d-flex align-center text-caption">
                <!-- v-for: 첨부파일 반복 렌더링 -->
                <!-- :key: 고유 키 -->
                <!-- d-flex: flexbox -->
                <!-- align-center: 수직 중앙 정렬 -->
                <!-- text-caption: 작은 글씨 -->
                <v-icon size="small" class="mr-1">mdi-file</v-icon>
                <!-- v-icon: 아이콘 -->
                <!-- size="small": 작은 크기 -->
                <!-- mr-1: margin-right -->
                <!-- mdi-file: 파일 아이콘 -->
                <a :href="attachment.url" target="_blank" class="text-decoration-none text-blue-lighten-2">{{ attachment.name }}</a>
                <!-- a: 링크 태그 -->
                <!-- :href: 첨부파일 URL -->
                <!-- target="_blank": 새 탭 -->
                <!-- text-decoration-none: 밑줄 제거 -->
                <!-- text-blue-lighten-2: 파란색 -->
              </div>
            </div>

            <div class="d-flex justify-space-between align-center px-2 pt-2 pb-1">
              <!-- d-flex: flexbox -->
              <!-- justify-space-between: 좌우 양쪽 배치 -->
              <!-- align-center: 수직 중앙 정렬 -->
              <!-- px-2: 좌우 패딩 -->
              <!-- pt-2: 위쪽 패딩 -->
              <!-- pb-1: 아래쪽 패딩 -->
              <span class="text-subtitle-2 text-grey-darken-1">{{ note.owner.username }} ({{ note.owner.login }})</span>
              <!-- text-subtitle-2: 소제목 글씨 -->
              <!-- text-grey-darken-1: 회색 글씨 -->
              <span class="text-caption text-right text-grey-darken-1">{{ formatDateTime(note.updated_at) }}</span>
              <!-- text-caption: 작은 글씨 -->
              <!-- text-right: 오른쪽 정렬 -->
              <!-- text-grey-darken-1: 회색 글씨 -->
            </div>

            <v-card-text class="note-content text-body-2 pa-2 pt-0">
              <!-- v-card-text: 카드 본문 -->
              <!-- note-content: 사용자 정의 클래스 -->
              <!-- text-body-2: 본문 텍스트 스타일 -->
              <!-- pa-2: 패딩 -->
              <!-- pt-0: 위쪽 패딩 없음 -->
              {{ note.content }}
            </v-card-text>

            <div v-if="index === 0" class="attachments-section ma-2 pa-2 rounded" style="border: 1px solid #E0E0E0;">
              <!-- index===0일 때 예시 첨부파일 표시 -->
              <div class="text-caption font-weight-bold mb-1">첨부파일 (예시)</div>
              <div class="d-flex align-center text-caption">
                <v-icon size="small" class="mr-1">mdi-image</v-icon>
                <a href="#" target="_blank" class="text-decoration-none text-blue-lighten-2">design_reference_v01.jpg</a>
              </div>
            </div>

            <v-divider v-if="index < props.otherNotes.length - 1"></v-divider>
            <!-- v-divider: 구분선 -->
            <!-- v-if: 마지막 항목은 제외 -->
          </div>
        </template>
        <v-card-text v-else class="d-flex align-center justify-center fill-height">
          <!-- v-else: otherNotes가 비어있을 때 -->
          <!-- d-flex: flexbox -->
          <!-- align-center: 수직 중앙 정렬 -->
          <!-- justify-center: 중앙 배치 -->
          <!-- fill-height: 높이 채움 -->
          <p class="text-grey">다른 사용자의 노트가 없습니다.</p>
          <!-- p: 문단 -->
          <!-- text-grey: 회색 글씨 -->
        </v-card-text>
      </v-card>
    </div>

    <!-- AttachmentModal 컴포넌트 -->
    <AttachmentModal
      v-model="showAttachmentModal"
      <!-- v-model: 양방향 데이터 바인딩 -->
      @upload="handleUploadFiles"
      <!-- @upload: 업로드 이벤트 -->
    />
  </div>
</template>

<style scoped>
.notes-container {
  cursor: default;
  /* 기본 커서 모양 */
  overflow-y: auto;
  /* 세로 스크롤 자동 */
}

.note-content {
  white-space: pre-wrap;
  /* 줄바꿈 및 공백 유지 */
  word-wrap: break-word;
  /* 긴 단어 줄바꿈 허용 */
  line-height: 1.4;
  /* 줄 간격 */
}

.note-item {
  background-color: transparent;
  /* 투명 배경 */
  transition: background-color 0.3s ease-in-out;
  /* 배경색 부드럽게 전환 */
}

:deep(.v-textarea .v-field__field) {
  transition: background-color 0.3s ease-in-out;
  /* Vuetify 내부 필드에 전환 효과 적용 */
}

:deep(.v-textarea.saved-note .v-field__field) {
  background-color: #E3F2FD;
  /* 저장 완료 시 연한 파란색 배경 */
}

.new-note-highlight {
  background-color: #FFF9C4;
  /* 새 노트 강조 색상 (연한 노랑) */
}
</style>