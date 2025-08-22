import { ref, readonly } from 'vue';
import axios from 'axios';

// 반응형 상태 변수들
const projects = ref([]);
const pipelineSteps = ref([]);
const displayVersions = ref([]); // 화면에 보여줄 버전만 저장할 변수
const selectedProject = ref(null);
const presentEntityTypes = ref([]); // 목록에 존재하는 모든 엔티티 타입
const selectedPipelineStep = ref(null);
const isLoading = ref(false);
const currentPage = ref(1);
const totalPages = ref(1);
const sortBy = ref('created_at'); // 정렬 기준
const sortOrder = ref('desc'); // 정렬 순서 (asc, desc)
const activeFilters = ref([]); // SearchBar로부터 받은 필터 조건
const suggestionSources = ref({}); // SearchBar 제안 목록 데이터
const versionsPerPage = 50; // 페이지 당 버전 수

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
 * ShotGrid 프로젝트 및 파이프라인스텝 데이터를 관리하는 Composition API 훅
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
     * 특정 프로젝트에 속한 파이프라인 스텝 목록을 불러옵니다.
     * @param {number} projectId - 태스크를 불러올 프로젝트의 ID
    //  */
    // const loadTasks = async (projectId) => {
    //     try {
    //         const response = await apiClient.get(`/api/projects/${projectId}/tasks`);
    //         // 백엔드에서 받은 태스크 목록 앞에 'All' 옵션을 추가합니다.
    //         tasks.value = [{ name: 'All' }, ...response.data];
    //         console.log(`Tasks for project ${projectId} loaded:`, tasks.value);
    //     } catch (error) {
    //         console.error(`Failed to load tasks for project ${projectId}:`, error);
    //         // TODO: 사용자에게 에러 메시지를 표시하는 로직 추가
    //     }
    // };
    const loadPipelineSteps = async (projectId) => {
        try{
            const response = await apiClient.get(`/api/projects/${projectId}/pipeline-steps`);
            // 백엔드에서 받은 스텝 목록 앞에 'All'옵션을 추가합니다.
            pipelineSteps.value = [{ name: 'All'}, ...response.data];
            console.log('Pipeline steps for project ${projectID} loaded:', pipelineSteps.value);
        } catch (error) {
            console.error('Failed to load pipeline steps for project ${projectId}:', error);
            // TODO: 사용자에게 에러 메시지를 표시하는 로직 추가
        }
    };

    /**
     * 백엔드에서 정렬/페이지네이션 처리된 버전 목록을 불러옵니다.
     */
    const loadVersions = async (useCache = false) => {
        if (!selectedProject.value || !selectedPipelineStep.value) return;
        isLoading.value = true;
        try {
            const response = await apiClient.get('/api/view/versions/', {
                params: {
                    project_id: selectedProject.value.id,
                    pipeline_step: selectedPipelineStep.value.name,
                    page: currentPage.value,
                    page_size: versionsPerPage,
                    sort_by: sortBy.value,
                    sort_order: sortOrder.value,
                    filters: JSON.stringify(activeFilters.value),
                    use_cache: useCache,
                }
            });
            const data = response.data;
            console.log("### Processed Data from Backend:", data); // 상세 로그 추가
            displayVersions.value = data.versions;
            totalPages.value = data.total_pages;
            presentEntityTypes.value = data.presentEntityTypes;
            suggestionSources.value = data.suggestions || {}; // 제안 목록 데이터 저장
        } catch (error) {
            console.error(`Failed to load versions:`, error);
        } finally {
            isLoading.value = false;
        }
    };


    const changePage = (page) => {
        currentPage.value = page;
        loadVersions(true); // 페이지 이동 시에는 캐시 사용
    };


    /**
     * 선택된 프로젝트를 설정하고 해당 프로젝트의 파이프라인 스텝을 불러옵니다.
     * @param {number} projectId - 선택할 프로젝트의 ID
     */
    const selectProject = async (projectId) => {
        const project = projects.value.find(p => p.id === projectId);
        if (project) {
            selectedProject.value = project;
            selectedPipelineStep.value = null; // 프로젝트 변경 시 스탭 초기화
            await loadPipelineSteps(projectId);
        }
    };

    /**
     * 선택된 파이프라인 스텝을 설정합니다.
     * @param {string} stepName - 선택할 파이프라인 스텝의 이름
     */
    const selectPipelineStep = async (stepName) => {
        console.log('선택된 stepName:', stepName);
        // 'All'을 선택했거나 실제 스텝을 선택한 경우 모두 처리합니다.
        const step = (stepName === 'All')
            ? { name: 'All' }
            : pipelineSteps.value.find(s => s.name === stepName);
        if (step) {
            selectedPipelineStep.value = step;
            // 스텝이 바뀌면 정렬 상태를 기본값으로 초기화하고 1페이지부터 로드
            currentPage.value = 1;
            sortBy.value = 'created_at';
            sortOrder.value = 'desc';
            await loadVersions(false); // 태스크 선택 시에는 새로고침 (캐시 미사용)
        }
    };

    /**
     * SearchBar로부터 받은 필터를 적용하고 버전 목록을 새로고침합니다.
     * @param {Array} newFilters - SearchBar에서 전달된 필터 객체 배열
     */
    const applyFilters = (newFilters) => {
        activeFilters.value = newFilters;
        currentPage.value = 1; // 필터가 변경되면 1페이지부터 다시 시작
        loadVersions(true); // 새 필터 적용 시에도 캐시 사용
    };

    const setSort = (newSortBy) => {
        if (sortBy.value === newSortBy) {
            // 같은 버튼을 누르면 정렬 순서만 변경
            sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
        } else {
            // 새로운 버튼을 누르면 해당 기준으로 오름차순 정렬
            sortBy.value = newSortBy;
            sortOrder.value = 'asc';
        }
        currentPage.value = 1; // 정렬 기준이 바뀌면 항상 1페이지로 이동
        loadVersions(true); // 정렬 시에는 캐시 사용
    };

    return {
        projects: readonly(projects),
        pipelineSteps: readonly(pipelineSteps),
        displayVersions: readonly(displayVersions),
        selectedProject: readonly(selectedProject),
        presentEntityTypes: readonly(presentEntityTypes),
        selectedPipelineStep: readonly(selectedPipelineStep),
        suggestionSources: readonly(suggestionSources),
        isLoading: readonly(isLoading),
        currentPage: readonly(currentPage),
        totalPages: readonly(totalPages),
        sortBy: readonly(sortBy),
        sortOrder: readonly(sortOrder),
        loadProjects,
        loadPipelineSteps,
        loadVersions,
        changePage,
        selectProject,
        selectPipelineStep,
        setSort,
        applyFilters,
    };
}