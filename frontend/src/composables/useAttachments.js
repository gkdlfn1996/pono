/**
 * @file useAttachments.js
 * @description 첨부파일 관련 UI 상호작용 및 상태 관리를 위한 Composition API 훅.
 *              모달 제어, 클립보드 복사, 아이콘 결정 등 첨부파일과 관련된 공통 로직을 제공합니다.
 */
import { ref } from 'vue';

/**
 * 첨부파일 관련 상태와 함수를 제공하는 composable.
 * @returns {object} 첨부파일 UI 관리에 필요한 상태와 메서드를 담은 객체.
 */
export function useAttachments() {
  /** @type {import('vue').Ref<boolean>} */
  const showAttachmentModal = ref(false);

  /** @type {import('vue').Ref<{path: string|null, show: boolean}>} */
  const copiedPath = ref({ path: null, show: false });

  /**
   * 첨부파일 객체를 기반으로 적절한 아이콘 이름을 반환합니다.
   * @param {object} attachment - 파일 정보를 담은 첨부파일 객체.
   * @returns {string} MDI 아이콘 클래스 이름.
   */
  const getIconForFile = (attachment) => {
    if (attachment.file_type === 'url') {
      return 'mdi-link-variant';
    }
    const fileName = attachment.file_name || attachment.path_or_url;
    if (!fileName) return 'mdi-file';
    const extension = fileName.split('.').pop().toLowerCase();
    if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(extension)) return 'mdi-image';
    if (['mov', 'mp4', 'avi', 'mkv'].includes(extension)) return 'mdi-filmstrip';
    if (['pdf'].includes(extension)) return 'mdi-file-pdf-box';
    if (['doc', 'docx'].includes(extension)) return 'mdi-file-word';
    if (['xls', 'xlsx'].includes(extension)) return 'mdi-file-excel';
    return 'mdi-file';
  };

  /**
   * navigator.clipboard.writeText API를 사용할 수 없을 때, document.execCommand를 이용한 클립보드 복사 폴백 함수.
   * @param {string} text - 클립보드에 복사할 텍스트.
   */
  const fallbackCopyToClipboard = (text) => {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.select();
    try {
      const successful = document.execCommand('copy');
      if (successful) {
        copiedPath.value = { path: text, show: true };
        setTimeout(() => { copiedPath.value = { path: null, show: false }; }, 1000);
      }
    } catch (err) {
      console.error("Fallback copy failed:", err);
    }
    document.body.removeChild(textarea);
  };

  /**
   * 첨부파일 클릭 이벤트를 처리합니다.
   * 파일 종류(URL 또는 로컬 경로)에 따라 새 탭에서 열거나, 경로를 클립보드에 복사합니다.
   * @param {object} attachment - 클릭된 첨부파일 객체.
   */
  const handleAttachmentClick = (attachment) => {
    const hostname = window.location.hostname;
    if (attachment.file_type === 'file' && attachment.file_name) {
      const safeFileName = encodeURIComponent(attachment.file_name.replace(/ /g, '_'));
      const previewUrl = `http://${hostname}:8001/api/attachments/${attachment.id}/${safeFileName}`;
      window.open(previewUrl, '_blank');
    } else if (attachment.file_type === 'url') {
      const path = attachment.path_or_url;
      if (path.startsWith('http://') || path.startsWith('https://')) {
        window.open(path, '_blank');
      } else {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(path).then(() => {
            copiedPath.value = { path: path, show: true };
            setTimeout(() => { copiedPath.value = { path: null, show: false }; }, 1000);
          }).catch(err => fallbackCopyToClipboard(path));
        } else {
          fallbackCopyToClipboard(path);
        }
      }
    }
  };

  return {
    showAttachmentModal,
    copiedPath,
    getIconForFile,
    handleAttachmentClick,
  };
}