// frontend/src/composables/useAuth.js
import { ref } from 'vue';
import { login as apiLogin } from '../api'; // api.js에서 login 함수를 apiLogin으로 임포트

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
      const response = await apiLogin(username.value, password.value); // apiLogin은 이미 response.data를 반환
      if (response.user) { // response.data.user 대신 response.user로 직접 접근
        loggedInUser.value = response.user.name;
        loggedInUserId.value = response.user.id;
        sessionStorage.setItem('loggedInUser', JSON.stringify(response.user)); // response.data.user 대신 response.user 저장
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