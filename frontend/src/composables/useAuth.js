// frontend/src/composables/useAuth.js
import { ref } from 'vue';
import { login as apiLogin } from '../api';

const loggedInUser = ref(sessionStorage.getItem('loggedInUser') || null);
const loginError = ref(null);

export function useAuth() {
  const login = async (username, password) => {
    try {
      loginError.value = null;
      const response = await apiLogin(username, password);
      loggedInUser.value = response.username;
      sessionStorage.setItem('loggedInUser', response.username);
      console.log('Login successful:', response);
    } catch (error) {
      console.error('Login failed:', error);
      loginError.value = 'Login failed. Please check your credentials.';
      loggedInUser.value = null;
      sessionStorage.removeItem('loggedInUser');
    }
  };

  const logout = () => {
    loggedInUser.value = null;
    sessionStorage.removeItem('loggedInUser');
  };

  return {
    loggedInUser,
    loginError,
    login,
    logout,
  };
}
