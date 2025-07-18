// frontend/src/composables/useShotGridData.js
import { ref } from 'vue';
import { fetchProjects, fetchShots, fetchVersionsForShot } from '../api'; // api.js에서 함수 임포트

export default function useShotGridData() {
  const projectName = ref('');
  const projects = ref([]);
  const shots = ref([]);
  const selectedShotName = ref('');
  const versions = ref([]);

  // 프로젝트 목록 불러오기
  const loadProjects = async () => {
    try {
      const projData = await fetchProjects();
      projects.value = projData.projects || [];
    } catch (error) {
      console.error('프로젝트 목록 불러오기 실패:', error);
    }
  };

  // 프로젝트 선택 시 해당 프로젝트의 샷 목록을 불러오는 함수
  const onProjectSelected = async () => {
    selectedShotName.value = ''; // 프로젝트 변경 시 샷 선택 초기화
    versions.value = []; // 프로젝트 변경 시 버전 목록 초기화
    if (projectName.value) {
      try {
        const data = await fetchShots(projectName.value);
        shots.value = data.shots || [];
      } catch (error) {
        console.error('샷 목록 불러오기 실패:', error);
        shots.value = [];
      }
    } else {
      shots.value = [];
    }
  };

  // 외부에서 버전 목록을 로드할 수 있도록 노출 (App.vue에서 호출)
  // 이 함수는 App.vue의 loadVersions 함수에서 호출될 예정이므로,
  // 여기서는 버전 목록만 관리하고 노트 로딩은 useNotes에서 담당합니다.
  const setVersions = (newVersions) => {
    versions.value = newVersions;
  };

  return {
    projectName,
    projects,
    shots,
    selectedShotName,
    versions,
    loadProjects,
    onProjectSelected,
    setVersions, // 외부에서 버전 목록을 설정할 수 있도록 노출
  };
}