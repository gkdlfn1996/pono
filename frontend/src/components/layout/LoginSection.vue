<!-- frontend/src/components/LoginSection.vue -->
<template>
  <v-container class="fill-height">
    <v-row justify="center">
      <v-card class="pa-5 login-card" elevation="2">
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
               label="ShotGrid Password"
               :type="passwordVisible ? 'text' : 'password'"
               @keyup.enter="handleLogin"
               :append-inner-icon="passwordVisible ? 'mdi-eye-off' : 'mdi-eye'"
               @click:append-inner="togglePasswordVisibility"
               required
             ></v-text-field>
             <v-alert
               v-if="loginError"
               type="error"
               dense
               text
               class="mb-3"
             >{{ loginError }}</v-alert>
            <v-btn color="primary" @click="handleLogin">Login</v-btn>
           </v-card-text>
         </v-card>
     </v-row>
   </v-container>
 </template>
 
 <script setup>
 import { ref } from 'vue';
 
 const props = defineProps({
   username: String,
   password: String,
   loginError: String,
 });
 
 const emit = defineEmits(['update:username', 'update:password', 'login']);
 
 const handleLogin = () => {
   console.log('Login button clicked in LoginSection.vue');
   emit('login');
 };
 
 const passwordVisible = ref(false);
 const togglePasswordVisibility = () => {
   passwordVisible.value = !passwordVisible.value;
 };
 </script>
 
 <style scoped>
 .login-card {
   max-width: 700px; /* 최대 너비 설정 */
   width: 100%; /* 부모 요소에 맞춰 너비 조절 */
   margin-top: -10vh; /* 화면 중앙보다 살짝 위로 올리기 */
 }
 </style>