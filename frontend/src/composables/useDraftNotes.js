/**
 * useDraftNotes.js
 *
 * 임시 노트 기능의 모든 상태와 로직을 관리하는 핵심 '두뇌' 모듈.
 */
import { ref, readonly } from 'vue';
import axios from 'axios';
import { useAuth } from './useAuth';
import _ from 'lodash'; // 디바운스 기능을 위해 lodash 임포트
import { useShotGridData } from './useShotGridData'; // useShotGridData 임포트

// --- API 클라이언트 설정 ---
const hostname = window.location.hostname;
const baseURL = `http://${hostname}:8001`;
const apiClient = axios.create({ baseURL });

// 모든 API 요청에 인증 토큰을 자동으로 추가하는 인터셉터
apiClient.interceptors.request.use(config => {
    const token = sessionStorage.getItem('accessToken');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

// --- 모듈 스코프 상태 변수 ---

/** @type {import('vue').Ref<Object<string, string>>} */
const myNotes = ref({}); // { versionId: "note content", ... }

/** @type {import('vue').Ref<Object<string, Array<object>>>} */
const otherNotes = ref({}); // { versionId: [ {note}, {note} ], ... }

/** @type {import('vue').Ref<Object<string, boolean>>} */
const isSaved = ref({}); // { versionId: true/false, ... }

/** @type {import('vue').Ref<Set<number>>} */
const newNoteIds = ref(new Set()); // 새로 받은 노트 ID를 추적하여 하이라이트 효과를 주기 위한 Set

export function useDraftNotes() {
    const { user } = useAuth(); // 현재 로그인한 사용자 정보를 가져오기 위함
    const { selectedProject, selectedPipelineStep } = useShotGridData(); // 선택된 프로젝트와 파이프라인 스텝 가져오기

    /**
     * 특정 스텝에 속한 모든 노트를 서버에서 가져와 상태를 채웁니다.
     * @param {number} projectId 
     * @param {string} stepName 
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
                step_name: selectedPipelineStep.value.name, 
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
     */
    const debouncedSave = _.debounce(saveMyNote, 500);

    /**
     * 웹소켓으로 들어온 실시간 노트 메시지를 처리합니다.
     * @param {string} message - 웹소켓 서버로부터 받은 JSON 문자열
     */
    const handleIncomingNote = (message) => {
        try {
            const note = JSON.parse(message);
            const verId = note.version_id;
            const myId = user.value?.id;

            if (note.owner.id === myId) {
                // 내가 다른 브라우저에서 수정한 내용이 실시간으로 올 경우
                console.log(`[useDraftNotes] handleIncomingNote: My note for version ${verId} updated.`);
                myNotes.value[verId] = note.content;
            } 
            else {
                if (!otherNotes.value[verId]) otherNotes.value[verId] = [];
                const noteIndex = otherNotes.value[verId].findIndex(n => n.id === note.id);
                if (noteIndex > -1) {
                    // 기존 노트 업데이트
                    console.log(`[useDraftNotes] handleIncomingNote: Other user's note for version ${verId} updated (existing).`);
                    otherNotes.value[verId][noteIndex] = note;
                } else {
                    // 새 노트 추가
                    console.log(`[useDraftNotes] handleIncomingNote: Other user's note for version ${verId} added (new).`);
                    otherNotes.value[verId].push(note);
                }
                // 새 노트 ID를 Set에 추가하여 하이라이트 준비
                newNoteIds.value.add(note.id);
                console.log("[useDraftNotes] handleIncomingNote: newNoteIds after update:", newNoteIds.value);
            }
        } catch (error) {
            console.error("Error processing incoming note:", error);
        }
    };

    /**
     * 하이라이트 표시를 제거하기 위해 Set에서 노트 ID를 삭제합니다.
     * @param {number} noteId 
     */
    const clearNewNoteFlag = (noteId) => {
        newNoteIds.value.delete(noteId);
    };

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
    };
}
