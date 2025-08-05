
<template>
  <!-- 1. 중앙 정렬 레이아웃 적용 -->
  <v-container class="fill-height d-flex align-center justify-center">
    <v-card class="pa-5" elevation="2" max-width="600" width="100%">
      <v-card-title class="text-h5">Login</v-card-title>
      <v-card-text>
        <!-- 4. 현재 스크립트 구조와 연동 -->
        <v-form @submit.prevent="submitLogin">
          <v-text-field
            v-model="username"
            label="ShotGrid ID"
            required
          ></v-text-field>
          
          <!-- 3. 눈 아이콘 기능 및 타입 바인딩 추가 -->
          <v-text-field
            v-model="password"
            label="Password"
            :type="isPasswordVisible ? 'text' : 'password'"
            :append-inner-icon="isPasswordVisible ? 'mdi-eye-off' : 'mdi-eye'"
            @click:append-inner="isPasswordVisible = !isPasswordVisible"
            required
            @keyup.enter="submitLogin"
          ></v-text-field>

          <v-alert v-if="loginError" type="error" dense text class="mb-3">
            {{ loginError }}
          </v-alert>
          
          <!-- 4. 현재 스크립트 구조와 연동 -->
          <v-row class="mt-3" justify="end">
            <v-col cols="auto">
              <v-btn color="secondary" @click="developerLogin">개발자용</v-btn>
            </v-col>
            <v-col cols="auto">
              <v-btn color="primary" @click="submitLogin">Login</v-btn>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script>
import { ref } from 'vue';

export default {
  props: {
    loginError: String,
  },
  emits: ['login'],
  setup(props, { emit }) {
    const username = ref('');
    const password = ref('');
    // 3. '눈' 아이콘 기능을 위한 상태 변수 추가
    const isPasswordVisible = ref(false);

    const submitLogin = () => {
      if (!username.value || !password.value) return;
      emit('login', { username: username.value, password: password.value });
    };

    const developerLogin = () => {
      emit('login', { username: 'ideatd', password: 'fnxmdkagh1!' });
    };

    return {
      username,
      password,
      isPasswordVisible,
      submitLogin,
      developerLogin,
    };
  },
};
</script>

<style scoped>
/* 필요한 스타일이 있다면 여기에 추가 */
</style>
