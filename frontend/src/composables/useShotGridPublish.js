import { ref, readonly, computed } from 'vue';
import apiClient from '@/plugins/apiClient';
import { useAuth } from './useAuth';
import { useShotGridData } from './useShotGridData';

export function useShotGridPublish() {
    // --- 상태 (State) ---
    const { user: currentUser } = useAuth();
    const { selectedProject } = useShotGridData();

    const isProcessing = ref(false);
    const publishResults = ref([]); // { status, noteId, error?, version? }

    // --- 파생 상태 (Computed) ---
    /** @type {import('vue').ComputedRef<Array>} 성공한 게시 작업 결과 목록 */
    const successfulNotes = computed(() => publishResults.value.filter(r => r.status === 'success'));

    /** @type {import('vue').ComputedRef<Array>} 실패한 게시 작업 결과 목록 */
    const failedNotes = computed(() => publishResults.value.filter(r => r.status === 'failure'));

    /** @type {import('vue').ComputedRef<string>} 게시 작업 결과에 대한 요약 메시지 */
    const summaryMessage = computed(() => {
        if (publishResults.value.length === 0) return '';
        return `Publish complete. Success: ${successfulNotes.value.length}, Failed: ${failedNotes.value.length}`;
    });

    /**
     * 저장된 모든 게시 작업 결과를 초기화합니다.
     */
    const clearPublishResults = () => {
        publishResults.value = [];
    };

    /**
     * 주어진 버전과 프로젝트 정보를 바탕으로 'To' 및 'CC' 사용자 목록을 계산합니다.
     * @param {object} version - 현재 버전 정보 객체.
     * @param {object} selectedProject - 현재 선택된 프로젝트 정보 객체.
     * @returns {{toUsers: Array, ccUsers: Array}} 'To' 및 'CC' 사용자 목록을 포함하는 객체.
     */
    const getInitialPublishUsers = (version, selectedProject) => {
        const toUsers = [];
        const ccUsers = new Map(); // 중복 제거를 위해 Map 사용

        // 1. 'To' 사용자 설정 (버전의 아티스트)
        if (version && version.user) {
            toUsers.push(version.user);
        }

        // 2. 'CC' 사용자 추가: 그룹 리더
        if (version && version.group_leaders) {
            for (const leader of version.group_leaders) {
                if (leader && leader.id) {
                    ccUsers.set(leader.id, leader);
                }
            }
        }

        // 3. 'CC' 사용자 추가: 프로젝트 담당자 (슈퍼바이저 등)
        if (selectedProject) {
            const supervisorFields = ['sg_sup', 'sg_cg_sup', 'sg_pd', 'sg_pm', 'sg_pa'];
            for (const field of supervisorFields) {
                const supervisorArray = selectedProject[field];
                if (supervisorArray && supervisorArray.length > 0) {
                    const supervisor = supervisorArray[0];
                    if (supervisor && supervisor.id) {
                        ccUsers.set(supervisor.id, supervisor);
                    }
                }
            }
        }
        // 'To' 사용자가 'CC'에 포함되어 있다면 제거
        if (toUsers.length > 0 && ccUsers.has(toUsers[0].id)) {
            ccUsers.delete(toUsers[0].id);
        }

        return { toUsers, ccUsers: Array.from(ccUsers.values()) };
    };

    /**
     * localStorage에서 현재 사용자의 글로벌 설정을 읽고,
     * 버전 정보와 조합하여 포매팅된 헤더를 생성합니다.
     * @param {object} version - 헤더 포매팅에 필요한 버전 객체.
     * @returns {{subject: string, headerNote: string, formattedHeader: string}} 글로벌 서브젝트, 원본 헤더, 포매팅된 헤더.
     */
    const getGlobalNotes = (version) => {
        if (!currentUser.value) return { subject: '', headerNote: '', formattedHeader: '' };

        const userSpecificStorageKey = `pono-header-${currentUser.value.login}`;
        const savedData = localStorage.getItem(userSpecificStorageKey);
        const { subject: currentSubject, headerNote: currentHeaderNote } = savedData ? JSON.parse(savedData) : { subject: '', headerNote: '' };

        let formattedHeader = '';
        if (currentHeaderNote) {
            // const parts = version?.code?.split('_');
            // if (parts && parts.length >= 4) {
            //     formattedHeader = `${currentHeaderNote}_${parts[2]}_${parts[3]}_`;
            const versionName = version?.code
            const entityName = version?.entity?.name;
            const prefixToRemove = `${entityName}_`;

            // 1. 버전 이름과 엔티티 이름이 모두 있고,
            // 2. 버전 이름이 '엔티티이름_' 으로 시작하는 경우
            if (versionName && entityName && versionName.startsWith(prefixToRemove)) {
                const suffix = versionName.replace(prefixToRemove, '');
                formattedHeader = `${currentHeaderNote}_${suffix}_`;
            } else {
                // 그 외의 모든 경우에는 기존처럼 헤더노트 뒤에 _만 붙임
                formattedHeader = `${currentHeaderNote}_`;
            }
        }
        return { subject: currentSubject, headerNote: currentHeaderNote, formattedHeader };
    };

    /**
     * 게시할 노트의 원본 데이터('재료')를 받아, API에 전송할 최종 Payload 객체를 생성합니다.
     * @param {object} rawNoteData - { version, noteContent, attachments, draftNoteId }
     * @returns {object} ShotGrid API에 전송될 최종 데이터 객체.
     */
    const createPublishPayload = (rawNoteData) => {
        if (!currentUser.value || !selectedProject.value) {
            throw new Error("User or Project is not set.");
        }

        const { subject, formattedHeader } = getGlobalNotes(rawNoteData.version);
        // const { toUsers, ccUsers } = getPublishUsers(rawNoteData.version, selectedProject.value);
        const finalContent = `${formattedHeader}${rawNoteData.noteContent}`;

        // 4. 최종 Payload 조립
        return {
            version_id: rawNoteData.version.id,
            project_id: selectedProject.value.id,
            subject: subject,
            content: finalContent,
            // to_users: toUsers.map(u => ({ type: u.type, id: u.id })),
            // cc_users: ccUsers.map(u => ({ type: u.type, id: u.id })),
            to_users: rawNoteData.toUsers.map(u => ({ type: u.type, id: u.id })),
            cc_users: rawNoteData.ccUsers.map(u => ({ type: u.type, id: u.id })),
            attachments: (rawNoteData.attachments || []).map(att => ({
                id: att.id,
                file_type: att.file_type,
                path_or_url: att.path_or_url,
                file_name: att.file_name,
            })),
            draft_note_id: rawNoteData.draftNoteId,
            author_id: currentUser.value.id,
            task: rawNoteData.version.sg_task,
        };
    };

    /**
     * 단일 노트를 ShotGrid에 게시하는 내부 API 호출 함수.
     */
    const _publishSingleNote = async (publishData) => {
        if (!currentUser.value) {
            throw new Error("User is not authenticated.");
        }
        const payload = {
            ...publishData
        };
        await apiClient.post('/api/publish/note', payload);
        return publishData.draft_note_id;
    };

    /**
     * 게시할 노트 목록을 받아 API 호출을 실행하는 공통 함수.
     * @param {Array<object>} notesToPublish - 게시할 노트의 '재료' 데이터 배열.
     */
    const publishNotes = async (notesToPublish) => {
        clearPublishResults();
        isProcessing.value = true;

        const promises = notesToPublish.map(noteData => {
            const finalPayload = createPublishPayload(noteData);
            // return _publishSingleNote(finalPayload)
            return _publishSingleNote({
                ...finalPayload
            })
                .then(draftNoteId => publishResults.value.push({
                    noteId: draftNoteId,
                    status: 'success'
                }))
                .catch(e => publishResults.value.push({
                    noteId: noteData.draftNoteId,
                    status: 'failure',
                    error: e.response?.data?.detail || "An unexpected error occurred.",
                    version: noteData.version // 실패 시 버전 정보 포함
                }));
        });

        await Promise.allSettled(promises);
        isProcessing.value = false;
    };

    return {
        isProcessing: readonly(isProcessing),
        publishResults: readonly(publishResults),
        summaryMessage: readonly(summaryMessage),
        failedNotes: readonly(failedNotes),
        successfulNotes: readonly(successfulNotes),
        getInitialPublishUsers,
        getGlobalNotes,
        clearPublishResults,
        publishNotes,
    };
}
