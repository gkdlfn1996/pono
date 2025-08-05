import { ref, readonly } from 'vue';
import axios from 'axios';




// --- 상태 관리 ---
const isAuthenticated = ref(false);
const user = ref(null);
const loginError = ref(null);

// --- 동적 API 주소 설정 ---
const hostname = window.location.hostname;
const baseURL = `http://${hostname}:8001`;

const apiClient = axios.create({
    baseURL: baseURL,
});

// --- Axios 요청 인터셉터 ---
apiClient.interceptors.request.use(config => {
    const token = sessionStorage.getItem('accessToken');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// --- 핵심 인증 함수들 ---

export function useAuth() {

    // 모든 인증 정보와 상태를 깨끗하게 초기화하는 함수
    const clearAllAuthData = () => {
        sessionStorage.removeItem('accessToken');
        sessionStorage.removeItem('refreshToken');
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        isAuthenticated.value = false;
        user.value = null;
    };

    // 앱 시작 시, 토큰 유효성을 검증하는 함수
    const checkAuthStatus = async () => {
        const token = sessionStorage.getItem('accessToken');
        if (!token) {
            clearAllAuthData();
            return;
        }
        try {
            const response = await apiClient.get('/api/me');
            if (response.data && response.data.username) {
                isAuthenticated.value = true;
                user.value = response.data;
            } else {
                clearAllAuthData();
            }
        } catch (error) {
            console.error('Authentication check failed:', error);
            clearAllAuthData();
        }
    };

    // 로그인 함수
    const login = async (username, password) => {
        loginError.value = null;

        try {
            const params = new URLSearchParams();
            params.append('username', username);
            params.append('password', password);

            const response = await apiClient.post('/api/auth/login', params, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });

            const { session_token, user_info } = response.data;
            sessionStorage.setItem('accessToken', session_token);
            isAuthenticated.value = true;
            user.value = user_info;

        } catch (error) {
            console.error('Login failed:', error);
            // 4. 로그인 API 요청 실패 시, 모든 것을 깨끗하게 정리합니다.
            clearAllAuthData(); 
            if (error.response && error.response.status === 401) {
                loginError.value = '아이디 또는 비밀번호가 올바르지 않습니다.';
            } else {
                loginError.value = '로그인 중 오류가 발생했습니다.';
            }
        }
    };

    // 로그아웃 함수
    const logout = () => {
        clearAllAuthData();
        // 로그아웃 후, 페이지를 새로고침하여 모든 상태를 완벽하게 초기화합니다.
        window.location.reload();
    };

    return {
        isAuthenticated: readonly(isAuthenticated),
        user: readonly(user),
        loginError: readonly(loginError),
        login,
        logout,
        checkAuthStatus,
    };
}