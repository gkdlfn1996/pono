// frontend/src/composables/useAuth.js
import { ref } from 'vue';
import axios from 'axios';

export default function useAuth() {
  const username = ref('');
  const password = ref('');
  const loggedInUser = ref(null);
  const loggedInUserId = ref(null);
  const loginError = ref(null);

  const login = async () => {
    loginError.value = null;
    console.log(`Attempting login for user: ${username.value}`);
    try {
      const response = await axios.post(`${process.env.VUE_APP_API_BASE_URL}/api/auth/login`, { // 환경 변수 사용
        username: username.value,
        password: password.value,
      });
      if (response.data.user) {
        loggedInUser.value = response.data.user.name;
        loggedInUserId.value = response.data.user.id;
        sessionStorage.setItem('loggedInUser', JSON.stringify(response.data.user));
        // 로그인 성공 후 추가적인 로직이 필요하면 여기서 처리하거나,
        // 이 composable을 사용하는 컴포넌트에서 콜백으로 처리할 수 있습니다.
      }
    } catch (error) {
      console.error('로그인 실패:', error);
      loginError.value = '아이디 또는 비밀번호를 다시 확인해주세요.';
      loggedInUser.value = null;
      loggedInUserId.value = null;
    }
  };

  // 로그인 상태를 외부에서 감지할 수 있도록 노출
  const isLoggedIn = ref(false);
  // onMounted에서 sessionStorage를 확인하는 로직은 App.vue에서 처리하도록 남겨둡니다.
  // 왜냐하면 App.vue가 전체 앱의 초기화와 관련된 책임을 가지기 때문입니다.

  return {
    username,
    password,
    loggedInUser,
    loggedInUserId,
    loginError,
    login,
    isLoggedIn // App.vue에서 로그인 상태를 판단하는 데 사용
  };
}