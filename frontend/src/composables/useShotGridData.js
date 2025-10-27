import { ref, readonly } from 'vue';
import apiClient from '@/plugins/apiClient'; //전역 API 클라이언트 인터셉터 사용
import axios from 'axios';

//================================ 반응형 상태 변수들 (Reactive State Variables) =================================

// 이 섹션에는 useShotGridData 훅이 관리하는 모든 반응형(Reactive) 상태 변수들이 정의됩니다.
// 컴포넌트나 다른 훅에서 이 변수들을 참조하여 UI를 업데이트하거나 데이터를 활용합니다.

const projects = ref([]);
const pipelineSteps = ref([]);
const displayVersions = ref([]); // 화면에 보여줄 버전만 저장할 변수
const selectedProject = ref(null);
const presentEntityTypes = ref([]); // 목록에 존재하는 모든 엔티티 타입
const selectedPipelineStep = ref(null);
let previousSelectedPipelineStep = null; // 이전 스텝을 기억하기 위한 변수
const isVersionsLoading = ref(false); // 로딩 상태 변수 이름 변경
let cancelTokenSource = null; // Axios 취소 토큰 소스를 저장할 변수
const currentPage = ref(1);
const totalPages = ref(1);
const sortBy = ref('created_at'); // 정렬 기준
const sortOrder = ref('desc'); // 정렬 순서 (asc, desc)
const activeFilters = ref([]); // SearchBar로부터 받은 필터 조건
const suggestionSources = ref({}); // SearchBar 제안 목록 데이터
const versionsPerPage = 50; // 페이지 당 버전 수
const linkedNotesCache = ref({}); // 링크 노트 캐시를 위한 객체






//=============================== 메인 Composition API 훅 (Main Composition API Hook) =================================

// useShotGridData 훅의 진입점입니다. 이 함수는 ShotGrid 관련 데이터와 로직을 캡슐화하여
// 다른 Vue 컴포넌트나 훅에서 재사용할 수 있도록 합니다.

export function useShotGridData() {
    /**
     * ShotGrid에서 프로젝트 목록을 불러옵니다.
     * `projects` 반응형 변수를 업데이트합니다.
     * @returns {Promise<void>} 프로젝트 로딩 완료 시 resolve되는 Promise
     */
    const loadProjects = async () => {
        try {
            const response = await apiClient.get('/api/data/projects');
            projects.value = response.data;
        } catch (error) {
            console.error('Failed to load projects:', error);
            // TODO: 사용자에게 에러 메시지를 표시하는 로직 추가
        }
    };


    /**
    * 특정 프로젝트의 파이프라인 스텝 목록을 불러옵니다.
    * `pipelineSteps` 반응형 변수를 업데이트합니다.
    * @param {number} projectId - 파이프라인 스텝을 불러올 프로젝트의 ID
    * @returns {Promise<void>} 파이프라인 스텝 로딩 완료 시 resolve되는 Promise
    */
    const loadPipelineSteps = async (projectId) => {
        try{
            const response = await apiClient.get(`/api/data/projects/${projectId}/pipeline-steps`);
            // 백엔드에서 받은 스텝 목록 앞에 'All'옵션을 추가합니다.
            pipelineSteps.value = ['All', ...response.data];
        } catch (error) {
            console.error('Failed to load pipeline steps for project ${projectId}:', error);
            // TODO: 사용자에게 에러 메시지를 표시하는 로직 추가
        }
    };

    /**
     * '가벼운' 버전 목록을 받은 후, 해당 버전들의 '무거운' 데이터(썸네일, 노트)를
     * 별도의 API로 요청하여 가져오는 함수입니다.
     * 가져온 데이터는 이미 화면에 표시된 displayVersions 배열에 합쳐집니다.
     * @param {Array} versions - '가벼운' 버전 정보 객체들의 배열
     */
    const loadHeavyDetails = async (versions) => {
        if (!versions || versions.length === 0) return;

        const versionIds = versions.map(v => v.id);

        try {
            const response = await apiClient.post('/api/data/heavy-version-data', versionIds, {
                params: {
                    project_id: selectedProject.value.id,
                    pipeline_step: selectedPipelineStep.value,
                }
            });
            const heavyData = response.data;

            // 받은 무거운 데이터를 기존 displayVersions에 효율적으로 합치기
            const versionMap = new Map(displayVersions.value.map(v => [v.id, v]));
            
            // 썸네일 정보 합치기
            heavyData.thumbnails.forEach(thumb => {
                if (versionMap.has(thumb.id)) versionMap.get(thumb.id).image = thumb.image;
            });
            // 노트 정보 합치기
            Object.entries(heavyData.notes).forEach(([versionId, notes]) => {
                if (versionMap.has(parseInt(versionId))) versionMap.get(parseInt(versionId)).notes = notes;
            });

        } catch (error) {
            console.error("Failed to load heavy details:", error);
            // 에러 발생 시, 해당 버전들의 썸네일과 노트를 null로 설정하여 로딩 스피너를 멈추고 '데이터 없음' 상태를 표시
            displayVersions.value.forEach(version => {
                version.image = null;
                version.notes = null;
            });
        }
    };

    /**
     * 백엔드에서 정렬/페이지네이션 처리된 버전 목록을 불러옵니다.
     * `displayVersions`, `totalPages`, `presentEntityTypes`, `suggestionSources`를 업데이트합니다.
     * @param {boolean} useCache - 캐시 사용 여부 (true: 사용, false: 새로고침)
     * @returns {Promise<void>} 버전 목록 로딩 완료 시 resolve되는 Promise
     */
    const loadVersions = async (useCache = false) => {
        if (isVersionsLoading.value) {
            // 이미 로딩 중이면 중복 실행 방지
            return;
        }
        if (!selectedProject.value || !selectedPipelineStep.value) return;
        
        isVersionsLoading.value = true;

        // 모듈 변수에 새로운 취소 토큰 소스를 바로 할당합니다.
        cancelTokenSource = axios.CancelToken.source();

        try {
            const response = await apiClient.get('/api/data/versions', {
                params: {
                    project_id: selectedProject.value.id,
                    pipeline_step: selectedPipelineStep.value,
                    page: currentPage.value,
                    page_size: versionsPerPage,
                    sort_by: sortBy.value,
                    sort_order: sortOrder.value,
                    filters: JSON.stringify(activeFilters.value),
                    use_cache: useCache,
                },
                // 할당된 모듈 변수에서 토큰을 가져와 사용합니다.
                cancelToken: cancelTokenSource.token,
            });
            const data = response.data;
            console.log("### Processed Data from Backend:", data); // 상세 로그 추가
            displayVersions.value = data.versions;
            totalPages.value = data.total_pages;
            presentEntityTypes.value = data.presentEntityTypes;
            suggestionSources.value = data.suggestions || {}; // 제안 목록 데이터 저장
            
            // 가벼운 데이터 로딩 성공 후, 무거운 데이터 로딩을 즉시 시작
            loadHeavyDetails(data.versions);

        } catch (error) {
            if (axios.isCancel(error)) {
                // 취소 시, 선택된 파이프라인 스텝을 이전 상태로 롤백합니다.
                selectedPipelineStep.value = previousSelectedPipelineStep;
                console.log('Version loading cancelled by user.')
            } else {
                console.error('Failed to load versions:', error);
            }
        } finally {
            isVersionsLoading.value = false;
            cancelTokenSource = null; // 작업 완료 후 토큰 소스 초기화
        }
    };

    /**
     * publish all notes 모달용: 필터링/정렬된 전체 버전 목록과 모든 썸네일을 가져와 반환합니다.
     */
    const getCachedVersionsForPub = async () => {
        if (!selectedProject.value || !selectedPipelineStep.value) return [];

        try {
            const response = await apiClient.get('/api/data/all-cached-versions', {
                params: {
                    project_id: selectedProject.value.id,
                    pipeline_step: selectedPipelineStep.value,
                    sort_by: sortBy.value,
                    sort_order: sortOrder.value,
                    filters: JSON.stringify(activeFilters.value),
                    use_cache: true, // 최신 캐시를 우선적으로 활용
                }
            });
            return response.data || [];
        } catch (error) {
            console.error("Failed to get cached versions for Pub modal:", error);
            return [];
        }
    };

    /**
     * Publish All Notes 모달용 2단계: 버전 목록을 받아, 누락된 썸네일을 추가로 요청하여 채워넣습니다.
     * @param {Array} versions - 썸네일을 채워넣을 버전 객체 배열
     */
    const fetchThumbnailsForPub = async (versions) => {
        console.log('%c[fetchThumbnailsForPub] 함수 시작', 'color: #4CAF50; font-weight: bold;');
        console.log('1. 입력받은 `versions` 데이터:', versions);

        if (!versions || versions.length === 0) {
            console.log('%c[fetchThumbnailsForPub] `versions`가 비어있어 함수를 종료합니다.', 'color: #EF5350;');
            return;
        }

        const versionMap = new Map(versions.map(v => [v.id, v]));
        console.log('2. 생성된 `versionMap`:', versionMap);

        const idsToFetch = versions.filter(v => v.image === undefined).map(v => v.id);
        console.log('3. 썸네일이 없어 요청이 필요한 ID 목록 (`idsToFetch`):', idsToFetch);

        if (idsToFetch.length === 0) {
            console.log('%c[fetchThumbnailsForPub] 추가로 요청할 썸네일이 없어 함수를 종료합니다.', 'color: #66BB6A;');
            return;
        }
        
        try {
            console.log(`%c[fetchThumbnailsForPub] API 요청 시작: /api/data/heavy-version-data, IDs: [${idsToFetch.join(', ')}]`, 'color: #29B6F6;');
            const response = await apiClient.post('/api/data/heavy-version-data', idsToFetch, {
                params: { project_id: selectedProject.value.id, pipeline_step: selectedPipelineStep.value }
            });
            console.log('4. API 응답 데이터 (`response`):', response);

            response.data.thumbnails.forEach(thumb => {
                if (versionMap.has(thumb.id)) {
                    versionMap.get(thumb.id).image = thumb.image;
                }
            });
            console.log('5. 썸네일 정보가 업데이트된 후의 `versionMap`:', versionMap);

        } catch (error) {
            console.error("Failed to fetch thumbnails for Pub modal:", error);
        }
        console.log('%c[fetchThumbnailsForPub] 함수 종료', 'color: #4CAF50; font-weight: bold;');
    };

    /**
     * 연결된 엔티티(샷/에셋)의 노트를 불러옵니다.
     * 한 번 불러온 노트는 linkedNotesCache에 저장하여 재사용합니다.
     * @param {object} entity - {id, type} 정보를 가진 엔티티 객체
     * @returns {Promise<Array>} 노트 목록 Promise
     */
    const loadLinkedNotes = async (entity) => {
        if (!entity || !entity.id) return [];

        // 1. 캐시 확인
        if (linkedNotesCache.value[entity.id]) {
            return linkedNotesCache.value[entity.id];
        }

        // 2. 캐시 없으면 API 호출
        try {
            const response = await apiClient.get('/api/data/linked-entity-notes', {
                params: { entity_type: entity.type, entity_id: entity.id }
            });
            linkedNotesCache.value[entity.id] = response.data; // 3. 결과 캐시
            return response.data;
        } catch (error) {
            console.error(`Failed to load linked notes for entity ${entity.id}:`, error);
            return []; // 에러 발생 시 빈 배열 반환
        }
    };



    //============================== 데이터 선택 및 조작 함수 (Data Selection & Manipulation Functions) ================================

    // 이 그룹의 함수들은 사용자 인터랙션에 따라 데이터를 선택하거나, 필터링, 정렬, 페이지네이션 등을 통해
    // 표시되는 데이터의 형태를 변경하는 역할을 합니다.
    
    /**
      * 현재 페이지를 변경하고 해당 페이지의 버전 목록을 불러옵니다.
      * `currentPage`를 업데이트하고 `loadVersions`를 호출합니다.
      * @param {number} page - 이동할 페이지 번호
      * @returns {void}
      */
    const changePage = (page) => {
        currentPage.value = page;
        loadVersions(true); // 페이지 이동 시에는 캐시 사용
    };

    /**
     * 선택된 프로젝트를 설정하고 해당 프로젝트의 파이프라인 스텝을 불러옵니다.
     * `selectedProject`와 `pipelineSteps`를 업데이트합니다.
     * @param {number} projectId - 선택할 프로젝트의 ID
     */
    const selectProject = async (projectId) => {
        const project = projects.value.find(p => p.id === projectId);
        if (project) {
            selectedProject.value = project;
            console.log('선택된 project:', project);
            selectedPipelineStep.value = null; // 프로젝트 변경 시 스탭 초기화
            await loadPipelineSteps(projectId);
        }
    };

    /**
     * 선택된 파이프라인 스텝을 설정합니다.
     * `selectedPipelineStep`, `currentPage`, `sortBy`, `sortOrder`를 업데이트하고 `loadVersions`를 호출합니다.
     * @param {string} stepName - 선택할 파이프라인 스텝의 이름
     * @returns {Promise<void>} 파이프라인 스텝 선택 및 버전 로딩 완료 시 resolve되는 Promise
     */
    const selectPipelineStep = async (stepName) => {
        // 새로운 스텝을 선택하면, 현재 스텝을 "이전 스텝"으로 백업합니다.
        previousSelectedPipelineStep = selectedPipelineStep.value;
        console.log('선택된 stepName:', stepName);
        // 'All'을 선택했거나 실제 스텝을 선택한 경우 모두 처리합니다.
        const step = (stepName === 'All')
            ? 'All'
            : pipelineSteps.value.find(s => s === stepName);
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
     * `activeFilters`를 업데이트하고 `loadVersions`를 호출합니다.
     * @param {Array} newFilters - SearchBar에서 전달된 필터 객체 배열
     * @returns {void}
     */
    const applyFilters = (newFilters) => {
        activeFilters.value = newFilters;
        currentPage.value = 1; // 필터가 변경되면 1페이지부터 다시 시작
        loadVersions(true); // 새 필터 적용 시에도 캐시 사용
    };

    /**
     * 버전 목록의 정렬 기준 및 순서를 설정합니다.
     * `sortBy`와 `sortOrder`를 업데이트하고 `loadVersions`를 호출합니다.
     * @param {string} newSortBy - 새로운 정렬 기준 (예: 'created_at', 'version_name')
     * @returns {void}
     */
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



    //============================== 유틸리티 함수 (Utility Functions) ==================================

    // 이 그룹의 함수들은 주요 데이터 로딩이나 조작 외의 보조적인 역할을 수행합니다.

    /**
     * 현재 진행 중인 버전 로딩 작업을 취소합니다. 
     * `cancelTokenSource`를 사용하여 진행 중인 Axios 요청을 취소합니다.
     * @returns {void}
     */
    const cancelLoadVersions = () => {
        if (cancelTokenSource) {
            cancelTokenSource.cancel(`Operation canceled by the user.`)
        }
    }



    //================================ 상태 초기화 함수 (State Clearing Function) =================================

    // 이 함수는 useShotGridData 훅이 관리하는 모든 반응형 상태 변수들을 초기 값으로 되돌립니다.
    // 주로 로그아웃과 같이 애플리케이션의 상태를 완전히 리셋해야 할 때 호출됩니다.

    /**
     * 모든 ShotGrid 관련 상태를 초기화합니다.
     * 로그아웃 시 호출됩니다.
     * @returns {void}
     */
    const clearShotGridDataState = () => {
        projects.value = [];
        pipelineSteps.value = [];
        displayVersions.value = [];
        selectedProject.value = null;
        presentEntityTypes.value = [];
        selectedPipelineStep.value = null;
        isVersionsLoading.value = false;
        currentPage.value = 1;
        totalPages.value = 1;
        sortBy.value = 'created_at';
        sortOrder.value = 'desc';
        activeFilters.value = [];
        suggestionSources.value = {};
    };



    //=================================== 내보내기 인터페이스 (Exported Interface) ===================================

    return {
        projects: readonly(projects),
        pipelineSteps: readonly(pipelineSteps),
        displayVersions: readonly(displayVersions),
        selectedProject: readonly(selectedProject),
        presentEntityTypes: readonly(presentEntityTypes),
        selectedPipelineStep: readonly(selectedPipelineStep),
        suggestionSources: readonly(suggestionSources),
        isVersionsLoading: readonly(isVersionsLoading), // 변경된 이름으로 내보내기
        currentPage: readonly(currentPage),
        totalPages: readonly(totalPages),
        sortBy: readonly(sortBy),
        sortOrder: readonly(sortOrder),
        loadProjects,
        loadPipelineSteps,
        loadLinkedNotes,
        getCachedVersionsForPub,
        fetchThumbnailsForPub,
        loadVersions,
        changePage,
        selectProject,
        selectPipelineStep,
        setSort,
        applyFilters,
        cancelLoadVersions, // 취소 함수 내보내기
        clearShotGridDataState,
    };
}