import { ref, readonly } from 'vue';
import apiClient from '@/plugins/apiClient';
import { useAuth } from './useAuth';

export function useShotGridPublish() {
    const isLoading = ref(false);
    const error = ref(null);
    const { user } = useAuth();

    /**
     * 주어진 버전과 프로젝트 정보를 바탕으로 'To' 및 'CC' 사용자 목록을 계산합니다.
     * @param {object} version - 현재 버전 정보 객체.
     * @param {object} selectedProject - 현재 선택된 프로젝트 정보 객체.
     * @returns {{toUsers: Array, ccUsers: Array}} 'To' 및 'CC' 사용자 목록을 포함하는 객체.
     */
    const getPublishUsers = (version, selectedProject) => {
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
     * 노트를 ShotGrid에 게시합니다.
     * @param {object} publishData - 게시할 데이터
     * @returns {Promise<boolean>} 성공 여부
     */
    // 내부 전용: 단일 노트 게시 로직
    const _publishSingleNote = async (publishData) => {
        if (!user.value) {
            throw new Error("User is not authenticated.");
        }
        const payload = {
            version_id: publishData.version.id,
            project_id: publishData.selectedProject.id,
            subject: publishData.subject,
            content: publishData.content,
            to_users: publishData.to_users.map(u => ({ type: u.type, id: u.id })),
            cc_users: publishData.cc_users.map(u => ({ type: u.type, id: u.id })),
            attachments: publishData.attachments.map(att => ({
                id: att.id,
                file_type: att.file_type,
                path_or_url: att.path_or_url,
                file_name: att.file_name,
            })),
            draft_note_id: publishData.draft_note_id,
            author_id: user.value.id,
            task: publishData.task,
        };
        // API 호출 실패 시, axios 인터셉터가 에러를 throw합니다.
        await apiClient.post('/api/publish/note', payload);
        // 성공 시 draft_note_id 반환
        return publishData.draft_note_id;
    };


    /**
     * (개별용) 노트를 ShotGrid에 게시합니다.
     * @param {object} publishData - 게시할 데이터
     * @returns {Promise<boolean>} 성공 여부
     */
    const publishNote = async (publishData) => {
        isLoading.value = true;
        error.value = null;
        try {
            await _publishSingleNote(publishData);
            return true;
        } catch (e) {
            console.error("Failed to publish note:", e);
            error.value = e.response?.data?.detail || "An unexpected error occurred during publish.";
            return false;
        } finally {
            isLoading.value = false;
        }
    };

    /**
     * (일괄용) 여러 노트를 병렬로 ShotGrid에 게시합니다.
     * @param {Array<object>} notesToPublish - 게시할 노트 데이터 배열
     * @param {Function} onNoteProcessed - 각 노트 처리 완료 시 호출될 콜백
     */
    const publishAllNotes = async (notesToPublish, onNoteProcessed) => {
        const promises = notesToPublish.map(noteData =>
            _publishSingleNote(noteData)
                .then((draft_note_id) => onNoteProcessed({
                    noteId: draft_note_id,
                    status: 'success'
                }))
                .catch(e => onNoteProcessed({
                    noteId: noteData.draft_note_id,
                    status: 'failure',
                    error: e.response?.data?.detail || "An unexpected error occurred."
                }))
        );
        await Promise.allSettled(promises);
    };


    return {
        isLoading: readonly(isLoading),
        error: readonly(error),
        getPublishUsers,
        publishNote,
        publishAllNotes,
    };
}
