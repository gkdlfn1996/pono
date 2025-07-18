<!-- frontend/src/components/LoginSection.vue -->
<template>
  <v-container class="login-section">
    <v-card class="pa-5" elevation="2">
      <v-card-title class="text-h5">로그인</v-card-title>
      <v-card-text>
        <v-text-field
          :model-value="username"
          @update:modelValue="emit('update:username', $event)"
          label="ShotGrid ID"
          required
        ></v-text-field>
        <v-text-field
          :model-value="password"
          @update:modelValue="emit('update:password', $event)"
          label="Password"
          type="password"
          @keyup.enter="handleLogin"
          required
        ></v-text-field>
        <v-alert
          v-if="loginError"
          type="error"
          dense
          text
          class="mb-3"
        >{{ loginError }}</v-alert>
        <v-btn color="primary" @click="handleLogin">로그인</v-btn>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>


// 부모 컴포넌트(App.vue)로부터 props를 받습니다.
const props = defineProps({
  username: String,
  password: String,
  loginError: String,
});

// 부모 컴포넌트로 이벤트를 발생시킵니다.
const emit = defineEmits(['update:username', 'update:password', 'login']);

const handleLogin = () => {
  console.log('Login button clicked in LoginSection.vue');
  emit('login');
};
</script>

<style scoped>
/* 필요한 스타일이 있다면 여기에 추가 */
</style>