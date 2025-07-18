// frontend/src/composables/useNotes.js
import { ref } from 'vue';
import axios from 'axios';
import { fetchNoteForVersionAndUser, fetchAllNotesForVersion } from '../api'; // fetchAllNotesForVersion 추가

// Simple debounce utility function
function debounce(func, delay) {
  let timeoutId;
  const debounced = function(...args) {
    const context = this;
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(context, args), delay);
  };
  debounced.cancel = () => {
    clearTimeout(timeoutId);
  };
  return debounced;
}

export default function useNotes(loggedInUserIdRef) { // loggedInUserId를 ref로 받음
  const notesContent = ref({}); // 각 버전별 노트 내용을 저장할 객체
  const otherNotes = ref({}); // 다른 사용자들의 노트를 저장할 객체
  const hasNewOtherNotes = ref({}); // 각 버전별로 새로운 다른 노트가 있는지 여부
  const isSaving = ref({}); // 저장 상태를 버전 ID별로 관리하는 객체로 초기화

  // 모든 버전에 대한 노트 내용을 불러오는 함수
  const loadVersionNotes = async (versionsToLoad) => {
    if (!loggedInUserIdRef.value) {
      console.warn('로그인되지 않은 사용자입니다. 노트를 불러올 수 없습니다.');
      return;
    }

    try {
      // 1. 현재 사용자의 노트를 병렬로 가져옵니다.
      const myNotePromises = versionsToLoad.map(version =>
        fetchNoteForVersionAndUser(version.id, loggedInUserIdRef.value)
      );
      const myNoteResults = await Promise.all(myNotePromises);

      // 2. 모든 사용자의 노트를 병렬로 가져옵니다.
      const allNotesPromises = versionsToLoad.map(version =>
        fetchAllNotesForVersion(version.id)
      );
      const allNotesResults = await Promise.all(allNotesPromises);

      // 가져온 노트 정보로 notesContent와 otherNotes 객체를 만듭니다.
      const newNotesContent = {};
      const newOtherNotes = {};

      myNoteResults.forEach((result, index) => {
        const versionId = versionsToLoad[index].id;
        newNotesContent[versionId] = result.note ? result.note.content : '';
      });

      allNotesResults.forEach((notes, index) => {
        const versionId = versionsToLoad[index].id;
        // 다른 사용자들의 노트만 필터링
        newOtherNotes[versionId] = notes.filter(note => note.owner.id !== loggedInUserIdRef.value);
      });

      notesContent.value = newNotesContent; // 반응성을 위해 객체 자체를 교체
      otherNotes.value = newOtherNotes;
    } catch (error) {
      console.error('노트 불러오기 실패:', error);
    }
  };

  // 실제 백엔드에 노트를 저장하는 내부 함수
  const _performSave = async (versionId, content) => {
    if (!loggedInUserIdRef.value) {
      console.warn('로그인되지 않은 사용자입니다. 노트를 저장할 수 없습니다.');
      return;
    }
    // 반응형 객체를 직접 수정하여 특정 버전의 저장 상태를 true로 설정
    isSaving.value[versionId] = true;
    const startTime = Date.now();

    try {
      await axios.post(`${process.env.VUE_APP_API_BASE_URL}/api/notes`, { // 환경 변수 사용
        version_id: versionId,
        owner_id: loggedInUserIdRef.value,
        content: content,
      });
      console.log(`Note for version ${versionId} saved successfully.`);
    } catch (error) {
      console.error(`Note for version ${versionId} save failed:`, error);
    } finally {
      const elapsedTime = Date.now() - startTime;
      const remainingTime = 500 - elapsedTime; // 최소 500ms 유지

      const finishSaving = () => {
        // 저장이 완료되면 해당 버전 ID의 키를 객체에서 삭제
        delete isSaving.value[versionId];
      };

      if (remainingTime > 0) {
        setTimeout(finishSaving, remainingTime);
      } else {
        finishSaving();
      }
    }
  };

  // 특정 버전의 다른 사용자 노트를 새로고침하는 함수
  const reloadOtherNotesForVersion = async (versionId) => {
    if (!loggedInUserIdRef.value) {
      console.warn('로그인되지 않은 사용자입니다. 다른 사용자 노트를 새로고침할 수 없습니다.');
      return;
    }
    try {
      const notes = await fetchAllNotesForVersion(versionId);
      // 다른 사용자들의 노트만 필터링하여 업데이트
      otherNotes.value[versionId] = notes.filter(note => note.owner.id !== loggedInUserIdRef.value);
      console.log(`Other notes for version ${versionId} reloaded successfully.`);
      // 새로고침 버튼을 눌렀으므로, 새로운 노트 알림 플래그를 false로 설정
      hasNewOtherNotes.value[versionId] = false;
      console.log(`hasNewOtherNotes for version ${versionId} set to false after reload.`);
    } catch (error) {
      console.error(`Failed to reload other notes for version ${versionId}:`, error);
    }
  };

  // 특정 버전의 새로운 다른 노트 알림 플래그를 설정하는 함수
  const setNewOtherNotesFlag = (versionId, value) => {
    hasNewOtherNotes.value[versionId] = value;
    console.log(`hasNewOtherNotes for version ${versionId} set to ${value}.`);
  };

  // 디바운싱된 노트 저장 함수 (입력 중 사용)
  const debouncedSave = debounce(_performSave, 1000); // 1초 디바운스

  // 즉시 저장 함수 (블러 이벤트 등에서 사용)
  const saveImmediately = _performSave;

  return {
    notesContent,
    otherNotes, // 다른 사용자 노트 데이터 노출
    loadVersionNotes,
    debouncedSave, // 외부에는 디바운싱된 함수를 노출
    saveImmediately, // 즉시 저장 함수 노출
    reloadOtherNotesForVersion, // 새로고침 함수 노출
    hasNewOtherNotes, // 새로운 노트 알림 플래그 노출
    setNewOtherNotesFlag, // 새로운 노트 알림 플래그 설정 함수 노출
    isSaving, // 저장 상태 노출
  };
}