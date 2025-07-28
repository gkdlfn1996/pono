// frontend/src/composables/useShotGridData.js
import { ref } from 'vue';
import { fetchProjects, fetchTasksForProject } from '../api'; // api.js에서 함수 임포트

export default function useShotGridData() {
  const projectName = ref('');
  const projects = ref([]);
  const tasks = ref([]); // 샷 대신 Task 목록을 저장
  const selectedTaskName = ref(''); // 선택된 Task 이름
  const versions = ref([]);

  // 프로젝트 목록 불러오기
  const loadProjects = async () => {
    try {
      const projData = await fetchProjects();
      projects.value = projData.projects || [];
      console.log('Loaded projects:', projects.value);
    } catch (error) {
      console.error('프로젝트 목록 불러오기 실패:', error);
    }
  };

  // 프로젝트 선택 시 해당 프로젝트의 샷 목록을 불러오는 함수
  const onProjectSelected = async (newProjectName) => {
    

    projectName.value = newProjectName; // 선택된 프로젝트 이름 업데이트
    selectedTaskName.value = ''; // 프로젝트 변경 시 Task 선택 초기화
    versions.value = []; // 프로젝트 변경 시 버전 목록 초기화
    tasks.value = []; // Task 목록 초기화

    if (newProjectName) {
      
      try {
        const selectedProject = projects.value.find(p => p.name === newProjectName);
        console.log('Selected project:', selectedProject);
        if (!selectedProject) {
          console.error('Selected project not found in projects list.');
          return; // 프로젝트를 찾지 못했으므로 여기서 함수 종료
        }
        const data = await fetchTasksForProject(selectedProject.id);
        tasks.value = data.tasks || []; // 백엔드에서 이미 처리된 태스크 목록을 직접 할당
        console.log('Loaded tasks:', tasks.value);
      } catch (error) {
        console.error('Task 목록 불러오기 실패:', error);
        tasks.value = [];
      }
    } else {
      tasks.value = [];
    }
  };

  // 외부에서 버전 목록을 로드할 수 있도록 노출 (App.vue에서 호출)
  // 이 함수는 App.vue의 loadVersions 함수에서 호출될 예정이므로,
  // 여기서는 버전 목록만 관리하고 노트 로딩은 useNotes에서 담당합니다。
  const setVersions = (newVersions) => {
    versions.value = newVersions;
  };

  const setSelectedTaskName = (newTaskName) => {
    selectedTaskName.value = newTaskName;
  };

  return {
    projectName,
    projects,
    tasks,
    selectedTaskName,
    versions,
    loadProjects,
    onProjectSelected,
    setVersions, // 외부에서 버전 목록을 설정할 수 있도록 노출
    setSelectedTaskName, // 새로 추가
  };
}