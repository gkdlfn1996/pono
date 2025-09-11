/**
* useDraftNotes.js
*
* 임시 노트 기능의 모든 상태와 로직을 관리하는 Composition API 훅.
* 사용자 노트, 다른 사용자 노트, 저장 상태, 하이라이트 ID 등을 관리하며,
* 백엔드 API와의 통신 및 웹소켓 메시지 처리를 담당합니다.
*/


import { ref, readonly } from 'vue';
import apiClient from '@/plugins/apiClient'; //전역 API 클라이언트 인터셉터 사용
import _ from 'lodash'; // 디바운스 기능을 위해 lodash 임포트
import { useAuth } from './useAuth';
import { useShotGridData } from './useShotGridData'; // useShotGridData 임포트


//=================================== 반응형 상태 변수들 (Reactive State Variables) =======================================

// 이 섹션에는 useDraftNotes 훅이 관리하는 모든 반응형(Reactive) 상태 변수들이 정의됩니다.
// 컴포넌트나 다른 훅에서 이 변수들을 참조하여 UI를 업데이트하거나 데이터를 활용합니다.

// isSaved : 노트 저장 완료 상태를 나타내는 객체.
// 각 버전 ID를 키로 가지며, 값이 true이면 해당 버전의 노트 저장이 완료되었음을 의미합니다.
// 주로 시각적 피드백(예: 파란색 깜빡임)을 위해 사용됩니다.

/** @type {import('vue').Ref<Object<string, string>>} */
const myNotes = ref({}); // { versionId: "note content", ... }

/** @type {import('vue').Ref<Object<string, Array<object>>>} */
const otherNotes = ref({}); // { versionId: [ {note}, {note} ], ... }

/** @type {import('vue').Ref<Object<string, boolean>>}*/
const isSaved = ref({}); // { versionId: true/false, ... }

/** @type {import('vue').Ref<Set<number>>} */
const newNoteIds = ref(new Set()); // 새로 받은 노트 ID를 추적하여 하이라이트 효과를 주기 위한 Set





// 메인 Composition API 훅 (Main Composition API Hook) 
export function useDraftNotes() {
    const { user } = useAuth(); // 현재 로그인한 사용자 정보를 가져오기 위함
    const { selectedProject, selectedPipelineStep } = useShotGridData(); // 선택된 프로젝트와 파이프라인 스텝 가져오기


    //=============================== 데이터 로딩 및 저장 함수 (Data Loading & Saving Functions) ==================================

    // 이 그룹의 함수들은 백엔드 API로부터 노트를 불러오거나 저장하는 역할을 합니다.

    /**
     * 특정 스텝에 속한 모든 노트를 서버에서 가져와 상태를 채웁니다.
     * @param {number} projectId 
     * @param {string} stepName 
     * @returns {Promise<void>} 노트 로딩 완료 시 resolve되는 Promise
     */
    const fetchNotesByStep = async (projectId, stepName) => {
        if (!projectId || !stepName) 
            return;
        try {
            const response = await apiClient.get('/api/notes/by_step', {
                params: { project_id: projectId, step_name: stepName }
            });

            console.log(`[useDraftNotes] fetchNotesByStep: API response received. Data:`, response.data);
            
            const myId = user.value?.id;
            const newMyNotes = {};
            const newOtherNotes = {};

            response.data.forEach(note => {
                const verId = note.version_id;
                if (note.owner.id === myId) {
                    newMyNotes[verId] = note.content;
                } 
                else {
                    if (!newOtherNotes[verId]) newOtherNotes[verId] = [];
                    newOtherNotes[verId].push(note);
                }
            });

            myNotes.value = newMyNotes;
            otherNotes.value = newOtherNotes;
        } catch (error) {
            console.error("[useDraftNotes] Failed to fetch draft notes:", error);
            myNotes.value = {};
            otherNotes.value = {};
        }
    };

    /**
     * 내 노트를 서버에 저장/업데이트합니다. (UPSERT)
     * @param {object} version - 현재 버전 객체
     * @param {string} content - 노트 내용
     * @returns {Promise<void>} 노트 저장 완료 시 resolve되는 Promise
     */
    const saveMyNote = async (version, content) => {
        if (!version || !user.value || !selectedProject.value || !selectedPipelineStep.value) return;
        
        const versionId = version.id;
        console.log('[useDraftNotes] saveMyNote: user.value:', user.value); // user.value 객체 전체 출력
        
        const noteData = {
            version_id: versionId,
            content: content,
            owner_id: user.value.id,
            version_meta: {
                id: version.id,
                name: version.code,
                step_name: version['sg_task.Task.step']?.name, 
                project_id: selectedProject.value.id
            }
        };

        console.log('[useDraftNotes] saveMyNote: Attempting to save note. noteData:', noteData);
        try {
            await apiClient.post('/api/notes/', noteData);
            myNotes.value[versionId] = content;
            isSaved.value[versionId] = true;
        } catch (error) {
            console.error(`[useDraftNotes] Failed to save note for version ${versionId}:`, error);
        } finally {
            setTimeout(() => { isSaved.value[versionId] = false; }, 500);
        }
    };
    
    /**
     * 500ms 디바운스가 적용된 노트 저장 함수.
     * 사용자가 타이핑을 멈추거나 포커스를 잃었을 때 자동으로 노트를 저장합니다.
     * @param {object} version - 현재 버전 객체
     * @param {string} content - 노트 내용
     * @returns {void}
     * @private
     */
    const debouncedSave = _.debounce(saveMyNote, 500);

    /**
     * 웹소켓으로 들어온 실시간 노트 메시지를 처리합니다.
     * @param {string} message - 웹소켓 서버로부터 받은 JSON 문자열
     * @returns {void}
     * @description
     * 이 함수는 웹소켓을 통해 다른 사용자의 노트 변경 사항을 수신하고, 이를 UI에 반영합니다.
     */
    const handleIncomingNote = (message) => {
        try {
            const note = JSON.parse(message);
            const verId = note.version_id;
            const myId = user.value?.id;

            if (note.owner.id === myId) {
                // 내가 다른 브라우저에서 수정한 내용이 실시간으로 올 경우.
                // 내가 빈 노트를 저장하여 삭제한 경우, 내 노트 목록에서도 제거합니다.
                if (note.content === "") {
                    delete myNotes.value[verId];
                } else {
                    myNotes.value[verId] = note.content;
                }
            } 
            else { // 다른 사람의 노트일 경우
                if (!otherNotes.value[verId]) otherNotes.value[verId] = [];

                const noteIndex = otherNotes.value[verId].findIndex(n => n.owner.id === note.owner.id);

                // 내용이 없는 노트는 '삭제' 신호로 간주하고 목록에서 제거합니다.
                if (note.content === "" && noteIndex > -1) {
                    otherNotes.value[verId].splice(noteIndex, 1);
                    console.log(`[useDraftNotes] handleIncomingNote: Other user's note for version ${verId} DELETED.`);
                } 
                // 내용이 있는 노트만 추가/업데이트/정렬을 수행합니다.
                else if (note.content) {
                    if (noteIndex > -1) {
                        // 기존 노트 업데이트
                        console.log(`[useDraftNotes] handleIncomingNote: Other user\'s note for version ${verId} updated (existing).`);
                        otherNotes.value[verId][noteIndex] = note;
                    } else {
                        // 새 노트 추가
                        console.log(`[useDraftNotes] handleIncomingNote: Other user\'s note for version ${verId} added (new).`);
                        otherNotes.value[verId].push(note);
                    }
                    // 실시간으로 노트를 받으면, 항상 updated_at 기준으로 다시 정렬하여 최신순을 유지합니다.
                    otherNotes.value[verId].sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
                    
                    // 새 노트 ID를 Set에 추가하여 하이라이트 준비
                    newNoteIds.value.add(note.id);
                    console.log("[useDraftNotes] handleIncomingNote: newNoteIds after update:", newNoteIds.value);
                }
            }
        } catch (error) {
            console.error("Error processing incoming note:", error);
        }
    };

    /**
     * 하이라이트 표시를 제거하기 위해 `newNoteIds` Set에서 노트 ID를 삭제합니다.
     * `newNoteIds` 반응형 변수를 업데이트합니다.
     * @param {number} noteId - 하이라이트를 제거할 노트의 ID
     * @returns {void}
     */
    const clearNewNoteFlag = (noteId) => {
        newNoteIds.value.delete(noteId);
    };



    //==================================== 상태 초기화 함수 (State Clearing Function) ====================================
    
    // 이 함수는 useDraftNotes 훅이 관리하는 모든 반응형 상태 변수들을 초기 값으로 되돌립니다.
    // 주로 로그아웃과 같이 애플리케이션의 상태를 완전히 리셋해야 할 때 호출됩니다.

    /**
     * 모든 노트 관련 상태를 초기화합니다.
     * 로그아웃 시 호출됩니다.
     * @returns {void}
     */
    const clearDraftNotesState = () => {
        myNotes.value = {};
        otherNotes.value = {};
        isSaved.value = {};
        newNoteIds.value = new Set();
    };



    //=================================== 내보내기 인터페이스 (Exported Interface) ===================================

    return {
        myNotes: readonly(myNotes),
        otherNotes: readonly(otherNotes),
        isSaved: readonly(isSaved),
        newNoteIds: readonly(newNoteIds),
        fetchNotesByStep,
        saveMyNote,
        debouncedSave,
        handleIncomingNote,
        clearNewNoteFlag,
        clearDraftNotesState,
    };
}