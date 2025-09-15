import axios from 'axios';

// 1. 동적 API 주소 설정
const hostname = window.location.hostname;
const baseURL = `http://${hostname}:8001`;

// 2. 프로젝트 전체에서 단 하나만 존재할 apiClient 인스턴스 생성
const apiClient = axios.create({
    baseURL: baseURL,
});

// 3. 모든 '요청'을 가로채서 헤더에 토큰 추가
apiClient.interceptors.request.use(config => {
    const token = sessionStorage.getItem('accessToken');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// 4. 응답 에러를 처리할 별도 함수 정의
const handleResponseError = (error) => {
  // 백엔드에서 보낸 에러가 401 (Unauthorized)인지 확인합니다.
  if (error.response && error.response.status === 401) {
    // 단, 이 에러가 로그인 요청 자체에서 발생한 것이 아니어야 합니다.
    if (error.config.url !== '/api/auth/login') {
      console.error('Authentication Error: 401. Logging out...');
      
      // 브라우저 저장소에서 인증 토큰과 사용자 정보를 삭제합니다.
      sessionStorage.removeItem('accessToken');
      sessionStorage.removeItem('user_info');
      
      // 로그인 페이지로 이동시키고, 앱 상태를 초기화합니다.
      window.location.href = '/';
    }
  }
  
  // 다른 모든 에러는 그대로 반환합니다.
  return Promise.reject(error);
};

// 성공 응답을 처리할 함수 (단순히 응답을 그대로 반환)
const handleResponseSuccess = (response) => response;

// 5. 위에서 정의한 함수들을 응답 인터셉터에 '등록'
apiClient.interceptors.response.use(handleResponseSuccess, handleResponseError);

// 6. 다른 파일에서 이 apiClient를 가져다 쓸 수 있도록 export
export default apiClient;
