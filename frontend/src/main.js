import 'vuetify/styles'
import { createApp } from 'vue'
import App from './App.vue'
import './assets/styles.css'


import vuetify from './plugins/vuetify'


const app = createApp(App)

app.use(vuetify)
app.mount('#app')

// const debounce = (callback, delay) => {
//   let tid;
//   return function (...args) {
//     const ctx = self;
//     tid && clearTimeout(tid);
//     tid = setTimeout(() => {
//       callback.apply(ctx, args);
//     }, delay);
//   };
// };

// if (typeof window !== 'undefined') {
//   const _ = window.ResizeObserver;
//   window.ResizeObserver = class ResizeObserver extends _ {
//     constructor(callback) {
//       callback = debounce(callback, 20); // 20ms 딜레이 적용
//       super(callback);
//     }
//   };
// }
