/**
* useDraftNotes.js
*
* 임시 노트 기능의 모든 상태와 로직을 관리하는 Composition API 훅.
* 사용자 노트, 다른 사용자 노트, 저장 상태, 하이라이트 ID 등을 관리하며,
* 백엔드 API와의 통신 및 웹소켓 메시지 처리를 담당합니다.
*/


import { ref, readonly, watch } from 'vue';
import apiClient from '@/plugins/apiClient'; //전역 API 클라이언트 인터셉터 사용
import _ from 'lodash'; // 디바운스 기능을 위해 lodash 임포트
import { useAuth } from './useAuth';
import { useShotGridData } from './useShotGridData'; // useShotGridData 임포트
import { useWebSocket } from './useWebSocket';


//=================================== 반응형 상태 변수들 (Reactive State Variables) =======================================

// 이 섹션에는 useDraftNotes 훅이 관리하는 모든 반응형(Reactive) 상태 변수들이 정의됩니다.
// 컴포넌트나 다른 훅에서 이 변수들을 참조하여 UI를 업데이트하거나 데이터를 활용합니다.

// isSaved : 노트 저장 완료 상태를 나타내는 객체.
// 각 버전 ID를 키로 가지며, 값이 true이면 해당 버전의 노트 저장이 완료되었음을 의미합니다.
// 주로 시각적 피드백(예: 파란색 깜빡임)을 위해 사용됩니다.

/** @type {import('vue').Ref<Object<string, object>>} */
const myNotes = ref({}); // { versionId: { id, content, owner, attachments: [] }, ... }

/** @type {import('vue').Ref<Object<string, Array<object>>>} */
const otherNotes = ref({}); // { versionId: [ {note}, {note} ], ... }

/** @type {import('vue').Ref<Object<string, boolean>>}*/
const isSaved = ref({}); // { versionId: true/false, ... }

/** @type {import('vue').Ref<Set<number>>} */
const newNoteIds = ref(new Set()); // 새로 받은 노트 ID를 추적하여 하이라이트 효과를 주기 위한 Set





// 메인 Composition API 훅 (Main Composition API Hook) 
export function useDraftNotes() {
    const { user } = useAuth(); // 현재 로그인한 사용자 정보를 가져오기 위함
    const { selectedProject, selectedPipelineStep, displayVersions } = useShotGridData(); // displayVersions 추가

    // --- WebSocket Connection Manager ---
    const ws = useWebSocket();

    //=============================== 웹소켓 관리 (WebSocket Management) ==================================

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
                    newMyNotes[verId] = note; // 노트 객체 전체를 저장
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
            // 웹소켓을 통해 최종 데이터가 들어오므로 여기서는 상태를 직접 바꾸지 않습니다.
            // 데이터 흐름의 일관성을 위해 웹소켓 응답(handleIncomingNote)이 상태를 업데이트하도록 합니다.
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
     * 특정 노트에 파일을 업로드합니다. 노트가 없으면 먼저 생성합니다.
     * @param {object} version - 현재 버전 객체
     * @param {object} uploadData - { files: [], urls: [] }
     */
    const uploadAttachments = async (version, uploadData) => {
        if (!user.value) return;
        
        // FormData 생성 및 데이터 추가
        const formData = new FormData();
        uploadData.files.forEach(file => formData.append('files', file));
        uploadData.urls.forEach(url => formData.append('urls', url));
        formData.append('owner_id', user.value.id);
      
        // 버전 메타데이터 추가 (백엔드에서 version_id의 존재를 확인/생성하기 위함)
        const versionMeta = {
            id: version.id,
            name: version.code,
            step_name: version['sg_task.Task.step']?.name, 
            project_id: selectedProject.value.id
        };
        formData.append('version_meta_json', JSON.stringify(versionMeta));

        // 백엔드 API 호출
        try {
            await apiClient.post(`/api/versions/${version.id}/attachments`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            // 성공 시, 백엔드가 웹소켓으로 변경사항을 브로드캐스트하므로
            // 프론트엔드에서 별도로 상태를 변경할 필요가 없습니다.
        } catch (error) {
            console.error("Failed to upload attachments:", error);
        }
    };

    /**
     * 특정 첨부파일을 삭제합니다.
     * @param {number} attachmentId - 삭제할 첨부파일의 ID
     */
    const deleteAttachment = async (attachmentId) => {
        if (!user.value) return;
        try {
            await apiClient.delete(`/api/attachments/${attachmentId}?owner_id=${user.value.id}`);
        } catch (error) {
            console.error("Failed to delete attachment:", error);
        }
    };

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
                const newMyNotes = { ...myNotes.value };
                // id가 0인 노트는 '삭제' 신호로 간주
                if (note.id === 0) {
                    delete newMyNotes[verId];
                } else {
                    newMyNotes[verId] = note;
                }
                myNotes.value = newMyNotes; // 새 객체로 교체하여 반응성 보장

            } else { // 다른 사람의 노트일 경우
                const newOtherNotes = { ...otherNotes.value };
                const oldNotesForVersion = newOtherNotes[verId] || [];
                const newNotesForVersion = [...oldNotesForVersion];

                const noteIndex = newNotesForVersion.findIndex(n => n.owner.id === note.owner.id);

                // id가 0인 노트는 '삭제' 신호로 간주
                if (note.id === 0) {
                    if (noteIndex > -1) newNotesForVersion.splice(noteIndex, 1);
                } else {
                    // 노트 추가 또는 업데이트 (내용이 비어있어도 id가 0이 아니면 업데이트/추가 대상)
                    if (noteIndex > -1) {
                        newNotesForVersion[noteIndex] = note;
                    } else {
                        newNotesForVersion.push(note);
                    }
                }

                // 실시간으로 노트를 받으면, 항상 updated_at 기준으로 다시 정렬하여 최신순을 유지합니다.
                newNotesForVersion.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
                
                if (newNotesForVersion.length > 0) {
                    newOtherNotes[verId] = newNotesForVersion;
                } else {
                    delete newOtherNotes[verId]; // 해당 버전에 노트가 더 없으면 키를 삭제
                }
                otherNotes.value = newOtherNotes; // 새 객체로 교체하여 반응성 보장

                // 새 노트 ID를 Set에 추가하여 하이라이트 준비
                if (note.id !== 0) {
                    newNoteIds.value.add(note.id);
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

    //==================================== 웹소켓 자동 관리 (WebSocket Auto-Management) ===================================

    watch(displayVersions, async (newVersions, oldVersions) => {
        // 로그인 상태가 아니면 아무 작업도 하지 않음
        if (!user.value) return;

        const newVersionIds = new Set(newVersions.map(v => v.id));
        const oldVersionIds = new Set((oldVersions || []).map(v => v.id));

        // 새로 연결할 웹소켓 식별
        const versionsToConnect = newVersions.filter(v => !oldVersionIds.has(v.id) && !ws.isConnected(v.id));
        
        // 연결 해제할 웹소켓 식별
        const versionIdsToDisconnect = [...oldVersionIds].filter(id => !newVersionIds.has(id));

        // 새로 추가된 버전에 대해 연결 생성
        if (versionsToConnect.length > 0) {
            const connectionPromises = versionsToConnect.map(version => {
                const wsUrl = `ws://${window.location.hostname}:8001/api/notes/ws/${version.id}`;
                return ws.connect(version.id, wsUrl, handleIncomingNote)
                         .then(() => ({ status: 'fulfilled', id: version.id }))
                         .catch(() => ({ status: 'rejected', id: version.id }));
            });

            const results = await Promise.allSettled(connectionPromises);
            
            const successful = results.filter(r => r.value.status === 'fulfilled').length;
            const failed = results.filter(r => r.value.status === 'rejected');
            if (failed.length > 0) {
                const failedIds = failed.map(r => r.value.id);
                console.log(`[useDraftNotes] WebSocket connection summary: ${successful} successful, ${failed.length} failed (IDs: ${failedIds.join(', ')})`);
            }
        }

        // 화면에서 사라진 버전에 대해 연결 해제
        if (versionIdsToDisconnect.length > 0) {
            versionIdsToDisconnect.forEach(id => ws.disconnect(id));
        }
    }, { deep: true });

    /**
     * 모든 활성 웹소켓 연결을 해제합니다.
     * @returns {void}
     */
    const disconnectAllNotes = () => {
        ws.disconnectAll();
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
        disconnectAllNotes(); // 모든 웹소켓 연결 해제
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
        uploadAttachments,
        deleteAttachment,
        handleIncomingNote,
        clearNewNoteFlag,
        clearDraftNotesState,
        disconnectAllNotes,
    };
}