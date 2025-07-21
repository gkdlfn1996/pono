// API 호출을 모듈화

// VUE_APP_API_BASE_URL이 .env.development에 정의되어 있으면 그 값을 사용하고,
// 그렇지 않으면 현재 호스트 이름을 기반으로 동적으로 API URL을 생성합니다.
const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || `http://${window.location.hostname}:8001`;

export async function fetchShots(projectName) {
    const res = await fetch(`${API_BASE_URL}/api/project/${projectName}/shots`);
    return res.json();
}

export async function fetchProjects() {
    const res = await fetch(`${API_BASE_URL}/api/projects`)
    return res.json()
}

export async function fetchVersionsForShot(shotId) {
    const res = await fetch(`${API_BASE_URL}/api/shot/${shotId}/versions`);
    return res.json();
}

export async function fetchNoteForVersionAndUser(versionId, ownerId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/notes/${versionId}/${ownerId}`);
        // 404 Not Found와 같은 HTTP 에러를 명시적으로 확인
        if (!response.ok) {
            // 노트가 없는 경우(404) 등 에러 발생 시 null을 포함한 객체 반환
            return { note: null };
        }
        return await response.json(); // 성공적인 응답(200 OK)만 JSON으로 파싱
    } catch (error) {
        console.error(`Failed to fetch note for version ${versionId}:`, error);
        return { note: null }; // 네트워크 에러 등 예외 발생 시
    }
}

export async function fetchAllNotesForVersion(versionId) {
    const res = await fetch(`${API_BASE_URL}/api/notes/${versionId}`);
    return res.json();
}
