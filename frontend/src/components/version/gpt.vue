<template>
  <!-- 2단: Draft Notes 영역 -->
  <div class="d-flex flex-column h-100">
    <!-- div: HTML 블록 요소 -->
    <!-- class: CSS 클래스 속성 -->
    <!-- d-flex: flex 컨테이너 -->
    <!-- flex-column: 세로 방향 정렬 -->
    <!-- h-100: 높이 100% 채움 -->

    <!-- My Draft Note 섹션 -->
    <div class="my-notes-section mb-4 d-flex flex-column flex-grow-1" style="min-height: 150px;">
      <!-- my-notes-section: 사용자 정의 클래스 -->
      <!-- mb-4: margin-bottom -->
      <!-- d-flex: flex 컨테이너 -->
      <!-- flex-column: 세로정렬 -->
      <!-- flex-grow-1: 공간 채움 -->
      <!-- style: 인라인 CSS -->

      <div class="d-flex align-center mb-2">
        <!-- d-flex: flex 레이아웃 -->
        <!-- align-center: 수직 중앙 정렬 -->
        <!-- mb-2: margin-bottom -->
        <h4 class="text-subtitle-1 font-weight-bold">My Draft Note</h4>
        <!-- h4: 제목 태그 -->
        <!-- text-subtitle-1: Vuetify 글꼴 스타일 -->
        <!-- font-weight-bold: 굵게 -->
        <v-spacer></v-spacer>
        <!-- v-spacer: 남은 공간 채움 -->
        <v-btn
          icon="mdi-paperclip"
          <!-- icon: 버튼 아이콘 -->
          <!-- mdi-paperclip: 아이콘 이름 -->
          variant="text"
          <!-- variant: 버튼 스타일 (텍스트형) -->
          size="small"
          <!-- size: 버튼 크기 -->
          @click="showAttachmentModal = true"
          <!-- @click: 클릭 이벤트 처리기 -->
          <!-- showAttachmentModal: ref 변수 -->
          density="compact"
          <!-- density: 버튼 내부 밀도 -->
        ></v-btn>
      </div>

      <!-- 동적 높이 컨테이너 -->
      <div class="note-input-container flex-grow-1" style="min-height: 150px;">
        <!-- note-input-container: 사용자 정의 클래스 -->
        <!-- flex-grow-1: 부모 공간 채움 -->
        <!-- style: 인라인 최소높이 -->
        <v-textarea
          label="여기에 노트를 작성하세요"
          <!-- label: 입력 필드 라벨 -->
          :model-value="localContent"
          <!-- :model-value: Vue 데이터 바인딩 -->
          <!-- localContent: ref 값 -->
          @update:model-value="onInput"
          <!-- update:model-value 이벤트 -->
          <!-- onInput 함수 실행 -->
          @focus="isFocused = true"
          <!-- focus 시 isFocused true -->
          @blur="onBlur"
          <!-- blur 시 onBlur 실행 -->
          variant="outlined"
          <!-- outlined: 외곽선 스타일 -->
          :class="{ 'saved-note': props.isSaved }"
          <!-- 조건부 클래스 바인딩 -->
          <!-- isSaved true면 saved-note 적용 -->
          no-resize
          <!-- no-resize: 크기 변경 불가 -->
          class="fill-height"
          <!-- fill-height: 높이 100% 채움 -->
        ></v-textarea>
      </div>

      <!-- 내 첨부파일 목록 -->
      <div v-if="myAttachments.length > 0" class="attachments-section mt-2 pa-2 rounded" style="border: 1px solid #E0E0E0;">
        <!-- v-if: myAttachments 있을 때 표시 -->
        <!-- attachments-section: 사용자 정의 클래스 -->
        <!-- mt-2: margin-top -->
        <!-- pa-2: padding -->
        <!-- rounded: 둥근모서리 -->
        <div class="text-caption font-weight-bold mb-1">첨부파일</div>
        <!-- text-caption: 작은 글씨 -->
        <!-- font-weight-bold: 굵게 -->
        <!-- mb-1: margin-bottom -->
        <div v-for="(attachment, index) in myAttachments" :key="index" class="d-flex align-center text-caption">
          <!-- v-for: 반복 렌더링 -->
          <!-- (attachment, index): 아이템과 인덱스 -->
          <!-- :key: 고유 키 -->
          <!-- d-flex: flex 컨테이너 -->
          <!-- align-center: 수직중앙 -->
          <!-- text-caption: 작은 글씨 -->
          <v-icon size="small" class="mr-1">{{ getIconForFile(attachment.name) }}</v-icon>
          <!-- v-icon: 아이콘 -->
          <!-- size="small": 작은 크기 -->
          <!-- mr-1: margin-right -->
          <!-- {{ getIconForFile(...) }}: 확장자에 맞는 아이콘 반환 -->
          <a :href="attachment.url" target="_blank" class="text-decoration-none text-blue-lighten-2">{{ attachment.name }}</a>
          <!-- a: 하이퍼링크 -->
          <!-- :href: 링크 URL 바인딩 -->
          <!-- target="_blank": 새 탭 -->
          <!-- text-decoration-none: 밑줄 제거 -->
          <!-- text-blue-lighten-2: 파란색 -->
          <v-spacer></v-spacer>
          <!-- v-spacer: 오른쪽 공간 확보 -->
          <v-btn icon variant="text" size="x-small" color="grey" @click="deleteMyAttachment(index)">
            <!-- v-btn: 버튼 -->
            <!-- icon: 아이콘형 -->
            <!-- variant="text": 텍스트 버튼 -->
            <!-- size="x-small": 작은 버튼 -->
            <!-- color="grey": 회색 -->
            <!-- @click: 삭제 함수 실행 -->
            <v-icon>mdi-close-circle</v-icon>
            <!-- mdi-close-circle: 닫기 아이콘 -->
          </v-btn>
        </div>
      </div>
    </div>

    <!-- Other's Draft Notes 섹션 -->
    <div class="other-notes-section d-flex flex-column flex-grow-1" style="min-height: 150px;">
      <!-- other-notes-section: 사용자 정의 클래스 -->
      <!-- d-flex: flex -->
      <!-- flex-column: 세로정렬 -->
      <!-- flex-grow-1: 공간 채움 -->
      <!-- style: 인라인 CSS -->
      <div class="d-flex align-center mb-2">
        <!-- d-flex: flex 컨테이너 -->
        <!-- align-center: 수직 중앙 -->
        <!-- mb-2: margin-bottom -->
        <h4 class="text-subtitle-1 font-weight-bold">Others Draft Notes</h4>
        <!-- h4: 제목 -->
        <!-- text-subtitle-1: Vuetify 스타일 -->
        <!-- font-weight-bold: 굵게 -->
      </div>
      <v-card 
        variant="outlined" 
        <!-- variant="outlined": 외곽선 카드 -->
        class="notes-container flex-grow-1"
        <!-- notes-container: 사용자 정의 클래스 -->
        <!-- flex-grow-1: 공간 채움 -->
        style="min-height: 150px; overflow-y: auto;"
        <!-- min-height: 최소 높이 -->
        <!-- overflow-y: 세로 스크롤 -->
        @click="handleInteraction" 
        <!-- @click: 클릭 이벤트 -->
        @scroll.passive="handleInteraction" 
        <!-- @scroll: 스크롤 이벤트 -->
        <!-- passive: 성능 최적화 -->
        :ripple="false"
        <!-- ripple: 리플 효과 비활성화 -->
      >
        <template v-if="props.otherNotes && props.otherNotes.length">
          <!-- v-if: otherNotes 존재 + 길이 1 이상 -->
          <div 
            v-for="(note, index) in props.otherNotes" 
            :key="note.id" 
            :ref="el => noteRefs[note.id] = el"
            :data-note-id="note.id"
            class="note-item"
            :class="{ 'new-note-highlight': props.newNoteIds.has(note.id) }"
            @click="onNoteClick(note)"
          >
            <!-- v-for: 노트 반복 -->
            <!-- :ref: DOM 참조 저장 -->
            <!-- :data-note-id: 커스텀 속성 -->
            <!-- class: note-item -->
            <!-- :class: 조건부 클래스 바인딩 -->
            <!-- @click: 클릭 시 onNoteClick -->

            <!-- 다른 사람 노트 첨부파일 -->
            <div v-if="note.attachments && note.attachments.length > 0" class="attachments-section ma-2 pa-2 rounded" style="border: 1px solid #E0E0E0;">
              <!-- v-if: 첨부파일 존재 -->
              <!-- attachments-section: 사용자 정의 클래스 -->
              <!-- ma-2: margin -->
              <!-- pa-2: padding -->
              <!-- rounded: 둥근 모서리 -->
              <div class="text-caption font-weight-bold mb-1">첨부파일</div>
              <!-- text-caption: 작은 글씨 -->
              <!-- font-weight-bold: 굵게 -->
              <!-- mb-1: margin-bottom -->
              <div v-for="(attachment, attIndex) in note.attachments" :key="attIndex" class="d-flex align-center text-caption">
                <!-- v-for: 첨부파일 반복 -->
                <!-- :key: 인덱스 -->
                <!-- d-flex: flex -->
                <!-- align-center: 수직 중앙 -->
                <!-- text-caption: 작은 글씨 -->
                <v-icon size="small" class="mr-1">mdi-file</v-icon>
                <!-- v-icon: 아이콘 -->
                <!-- size="small": 작은 크기 -->
                <!-- mr-1: margin-right -->
                <!-- mdi-file: 파일 아이콘 -->
                <a :href="attachment.url" target="_blank" class="text-decoration-none text-blue-lighten-2">{{ attachment.name }}</a>
                <!-- a: 링크 -->
                <!-- :href: URL 바인딩 -->
                <!-- target="_blank": 새 탭 -->
                <!-- text-decoration-none: 밑줄 없음 -->
                <!-- text-blue-lighten-2: 파란색 -->
              </div>
            </div>

            <div class="d-flex justify-space-between align-center px-2 pt-2 pb-1">
              <!-- d-flex: flex -->
              <!-- justify-space-between: 좌우 끝 배치 -->
              <!-- align-center: 수직 중앙 -->
              <!-- px-2: 좌우 패딩 -->
              <!-- pt-2: 위 패딩 -->
              <!-- pb-1: 아래 패딩 -->
              <span class="text-subtitle-2 text-grey-darken-1">{{ note.owner.username }} ({{ note.owner.login }})</span>
              <!-- span: 인라인 텍스트 -->
              <!-- text-subtitle-2: Vuetify 작은 서브타이틀 -->
              <!-- text-grey-darken-1: 회색 -->
              <span class="text-caption text-right text-grey-darken-1">{{ formatDateTime(note.updated_at) }}</span>
              <!-- text-caption: 작은 글씨 -->
              <!-- text-right: 오른쪽 정렬 -->
              <!-- text-grey-darken-1: 회색 -->
            </div>

            <v-card-text class="note-content text-body-2 pa-2 pt-0">
              <!-- v-card-text: 카드 본문 -->
              <!-- note-content: 사용자 정의 클래스 -->
              <!-- text-body-2: 본문 스타일 -->
              <!-- pa-2: padding -->
              <!-- pt-0: 위쪽 패딩 없음 -->
              {{ note.content }}
            </v-card-text>

            <v-divider v-if="index < props.otherNotes.length - 1"></v-divider>
            <!-- v-divider: 구분선 -->
            <!-- v-if: 마지막 항목 제외 -->
          </div>
        </template>
        <v-card-text v-else class="d-flex align-center justify-center fill-height">
          <!-- v-else: otherNotes 없을 때 -->
          <!-- d-flex: flex -->
          <!-- align-center: 수직 중앙 -->
          <!-- justify-center: 가로 중앙 -->
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
  /* cursor: default; 기본 화살표 커서 */
  overflow-y: auto;
  /* overflow-y: auto; 세로 스크롤 자동 */
}

.note-content {
  white-space: pre-wrap;
  /* white-space: pre-wrap; 줄바꿈, 공백 유지 */
  word-wrap: break-word;
  /* word-wrap: break-word; 긴 단어 줄바꿈 허용 */
  line-height: 1.4;
  /* line-height: 줄 간격 1.4 */
}

.note-item {
  background-color: transparent;
  /* background-color: 투명 배경 */
  transition: background-color 0.3s ease-in-out;
  /* transition: 배경색 전환 0.3초 ease-in-out */
}

:deep(.v-textarea .v-field__field) {
  transition: background-color 0.3s ease-in-out;
  /* :deep: Vuetify 내부 DOM 접근 */
  /* .v-textarea .v-field__field: 입력 필드 */
  /* transition: 배경색 전환 */
}

:deep(.v-textarea.saved-note .v-field__field) {
  background-color: #E3F2FD;
  /* 저장 완료 시 배경색 (연한 파랑) */
}

.new-note-highlight {
  background-color: #FFF9C4;
  /* 새 노트 강조 배경색 (연한 노랑) */
}
</style>
