import { ref, readonly } from 'vue';
import apiClient from '@/plugins/apiClient';
import { useAuth } from './useAuth';

export function useShotGridPublish() {
    const isLoading = ref(false);
    const error = ref(null);
    const { user } = useAuth();

    /**
     * 노트를 ShotGrid에 게시합니다.
     * @param {object} publishData - 게시할 데이터
     * @returns {Promise<boolean>} 성공 여부
     */
    const publishNote = async (publishData) => {
        isLoading.value = true;
        error.value = null;

        if (!user.value) {
            error.value = "User is not authenticated.";
            isLoading.value = false;
            return false;
        }

        try {
            // 1. 백엔드에 보낼 Payload 구성
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
                author_id: user.value.id, // 현재 로그인한 사용자 ID 추가
                task: publishData.task, // Task 정보 추가
            };

            // 2. API 호출
            await apiClient.post('/api/publish/note', payload);

            isLoading.value = false;
            return true; // 성공

        } catch (e) {
            console.error("Failed to publish note:", e);
            error.value = e.response?.data?.detail || "An unexpected error occurred during publish.";
            isLoading.value = false;
            return false; // 실패
        }
    };

    return {
        isLoading: readonly(isLoading),
        error: readonly(error),
        publishNote,
    };
}
