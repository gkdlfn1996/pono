import { ref, readonly, onMounted } from 'vue';

// -----------------------------------------
// 모듈 스코프 변수 (전역 상태 공유)
// -----------------------------------------
// 테마 설정 관련
const THEME_STORAGE_KEY = 'pono-theme-dark';
const isDarkTheme = ref(false);

// Publish 노트 가시성 설정 관련
const PUBLISHED_NOTES_VISIBILITY_KEY = 'pono-show-published-notes';
const showPublishedNotes = ref(false); // 기본값: 숨김 (false)

// 컴포저블 함수
export function useAppSettings() {

  // -----------------------------------------
  // 테마 설정 관련
  // -----------------------------------------
  // 테마 설정 로드
  const loadThemeSetting = () => {
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    if (savedTheme !== null) {
      isDarkTheme.value = JSON.parse(savedTheme);
    } else {
      isDarkTheme.value = window.matchMedia('(prefers-color-scheme: dark)').matches; // 시스템 기본 설정 따름
    }
  };

  // 테마 설정 저장
  const saveThemeSetting = () => {
    localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify(isDarkTheme.value));
  };

  // 테마 토글 함수
  const toggleDarkTheme = () => {
    isDarkTheme.value = !isDarkTheme.value;
    saveThemeSetting();
  };

  // -----------------------------------------
  // Publish 노트 가시성 설정 관련
  // -----------------------------------------
  // Publish 노트 가시성 설정 로드
  const loadPublishedNotesVisibilitySetting = () => {
    const savedPublishedNotesVisibility = localStorage.getItem(PUBLISHED_NOTES_VISIBILITY_KEY);
    if (savedPublishedNotesVisibility !== null) {
      showPublishedNotes.value = JSON.parse(savedPublishedNotesVisibility);
    } else {
      showPublishedNotes.value = false; // 기본값: 숨김 (false)
    }
  };

  // Publish 노트 가시성 설정 저장
  const savePublishedNotesVisibilitySetting = () => {
    localStorage.setItem(PUBLISHED_NOTES_VISIBILITY_KEY, JSON.stringify(showPublishedNotes.value));
  };

  // Publish 노트 가시성 토글 함수
  const togglePublishedNotes = () => {
    showPublishedNotes.value = !showPublishedNotes.value;
    savePublishedNotesVisibilitySetting();
  };

  // Publish 노트 필터링 로직 함수
  const filterPublishedNotes = (notes, showPublished) => {
    if (notes === null || notes === undefined) return []; // notes가 null 또는 undefined일 경우 빈 배열 반환
    if (showPublished) return notes;
    return notes.filter(note => !note.subject || !note.subject.includes('Publish'));
  };

  // -----------------------------------------
  // 초기화 및 반환
  // -----------------------------------------
  onMounted(() => {
    loadThemeSetting();
    loadPublishedNotesVisibilitySetting();
  });

  return { // readonly로 래핑하여 외부에서 직접 값 변경 방지
    isDarkTheme: readonly(isDarkTheme),
    showPublishedNotes: readonly(showPublishedNotes),
    toggleDarkTheme,
    togglePublishedNotes,
    filterPublishedNotes,
  };
}
