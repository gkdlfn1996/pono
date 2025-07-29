// frontend/src/composables/useShotGridData.js
import { ref, readonly } from 'vue';
import { fetchProjects, fetchTasksForProject, fetchVersionsForTask } from '../api'; // fetchVersionsForTask 추가

export default function useShotGridData() {
  // --- State ---
  // 컴포저블 외부에서 상태를 직접 수정하는 것을 방지하기 위해 내부 상태로 관리합니다.
  const _projects = ref([]);
  const _tasks = ref([]);
  const _versions = ref([]);
  const _selectedProject = ref(null);
  const _selectedTask = ref(null);
  const _isLoading = ref(false);

  // --- Getters ---
  // 외부에서는 이 readonly 버전의 상태들을 사용하게 하여, 의도치 않은 변경을 막습니다.
  const projects = readonly(_projects);
  const tasks = readonly(_tasks);
  const versions = readonly(_versions);
  const selectedProject = readonly(_selectedProject);
  const selectedTask = readonly(_selectedTask);
  const isLoading = readonly(_isLoading);

  // --- Actions ---
  async function loadProjects() {
    _isLoading.value = true;
    try {
      const projData = await fetchProjects();
      _projects.value = projData.projects || [];
      console.log('Loaded projects:', _projects.value);
    } catch (error) {
      console.error('프로젝트 목록 불러오기 실패:', error);
      _projects.value = [];
    } finally {
      _isLoading.value = false;
    }
  }

  async function selectProject(projectId) {
    if (_selectedProject.value?.id === projectId) return;

    _selectedProject.value = _projects.value.find(p => p.id === projectId) || null;
    _selectedTask.value = null;
    _tasks.value = [];
    _versions.value = [];

    if (!_selectedProject.value) return;

    _isLoading.value = true;
    try {
      const data = await fetchTasksForProject(_selectedProject.value.id);
      _tasks.value = data.tasks || [];
      console.log('Loaded tasks:', _tasks.value);
    } catch (error) {
      console.error('Task 목록 불러오기 실패:', error);
      _tasks.value = [];
    } finally {
      _isLoading.value = false;
    }
  }

  async function selectTask(taskId) {
    if (_selectedTask.value?.id === taskId) return;

    _selectedTask.value = _tasks.value.find(t => t.id === taskId) || null;
    _versions.value = [];

    if (!_selectedTask.value) return;

    _isLoading.value = true;
    try {
      // 백엔드 API는 taskId만 요구하므로, selectedTask의 id만 전달합니다.
      const data = await fetchVersionsForTask(_selectedTask.value.id);
      // 백엔드가 { versions: [...] } 형태가 아닌, [...] 배열 자체를 반환하므로 data를 직접 할당합니다.
      _versions.value = data || [];
      console.log('Loaded versions:', _versions.value);
    } catch (error) {
      console.error('Version 목록 불러오기 실패:', error);
      _versions.value = [];
    } finally {
      _isLoading.value = false;
    }
  }

  return {
    projects,
    tasks,
    versions,
    selectedProject,
    selectedTask,
    isLoading,
    loadProjects,
    selectProject,
    selectTask,
  };
}
