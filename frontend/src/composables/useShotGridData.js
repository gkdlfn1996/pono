import { ref, readonly } from 'vue';
import axios from 'axios';

// 반응형 상태 변수들
const projects = ref([]);
const tasks = ref([]);
const versions = ref([]);
const selectedProject = ref(null);
const selectedTask = ref(null);
const isLoading = ref(false); // 로딩 상태 변수 추가

// 동적 API 주소 설정 (useAuth.js와 동일하게 설정)
const hostname = window.location.hostname;
const baseURL = `http://${hostname}:8001`;

// API 클라이언트 인스턴스 생성
const apiClient = axios.create({
    baseURL: baseURL,
});

// Axios 요청 인터셉터: 모든 요청에 accessToken을 포함
apiClient.interceptors.request.use(config => {
    const token = sessionStorage.getItem('accessToken');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});




/**
 * ShotGrid 프로젝트 및 태스크 데이터를 관리하는 Composition API 훅
 */
export function useShotGridData() {
    /**
     * ShotGrid에서 프로젝트 목록을 불러옵니다.
     */
    const loadProjects = async () => {
        try {
            const response = await apiClient.get('/api/projects');
            projects.value = response.data;
            console.log('Projects loaded:', projects.value);
        } catch (error) {
            console.error('Failed to load projects:', error);
            // TODO: 사용자에게 에러 메시지를 표시하는 로직 추가
        }
    };

    /**
     * 특정 프로젝트에 속한 태스크 목록을 불러옵니다.
     * @param {number} projectId - 태스크를 불러올 프로젝트의 ID
     */
    const loadTasks = async (projectId) => {
        try {
            const response = await apiClient.get(`/api/projects/${projectId}/tasks`);
            tasks.value = response.data;
            console.log(`Tasks for project ${projectId} loaded:`, tasks.value);
        } catch (error) {
            console.error(`Failed to load tasks for project ${projectId}:`, error);
            // TODO: 사용자에게 에러 메시지를 표시하는 로직 추가
        }
    };


    /**
     * 특정 프로젝트에 속한 태스크 목록을 불러옵니다.
     * @param {number} taskName - 버전을 불러올 테스크의 이름
     */
    const loadVersions = async (taskName) => {
        isLoading.value = true;
        versions.value = [];
        try {
            const response = await apiClient.get(`/api/projects/${selectedProject.value.id}/tasks/${taskName}/versions`);
            versions.value = response.data;
            console.log(`Versions for Task ${taskName} loaded:`, versions.value);
        } catch (error) {
            console.error(`Failed to load versions for Task ${taskName}:`, error);
        } finally {
            isLoading.value = false; // 작업이 끝나면 항상 로딩 상태를 해제합니다.
        }
    };






    /**
     * 선택된 프로젝트를 설정하고 해당 프로젝트의 태스크를 불러옵니다.
     * @param {number} projectId - 선택할 프로젝트의 ID
     */
    const selectProject = async (projectId) => {
        const project = projects.value.find(p => p.id === projectId);
        if (project) {
            selectedProject.value = project;
            selectedTask.value = null; // 프로젝트 변경 시 태스크 초기화
            await loadTasks(projectId);
        }
    };

    /**
     * 선택된 태스크를 설정합니다.
     * @param {number} taskName - 선택할 태스크의 이름
     */
    const selectTask = async (taskName) => {
        const task = tasks.value.find(t => t.name === taskName);
        if (task) {
            selectedTask.value = task;
            // console.log('[useShotGridData] selectTask executed. Central selectedTask is now:', selectedTask.value);
            await loadVersions(taskName)
        }
    };

    return {
        projects: readonly(projects),
        tasks: readonly(tasks),
        versions: readonly(versions),
        selectedProject: readonly(selectedProject),
        selectedTask: readonly(selectedTask),
        isLoading: readonly(isLoading), // 외부에서 읽을 수 있도록 노출
        loadProjects,
        loadTasks,
        loadVersions,
        selectProject,
        selectTask,
    };
}