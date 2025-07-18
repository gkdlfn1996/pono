import 'vuetify/styles'                              // Vuetify 글로벌 스타일
import { createVuetify } from 'vuetify'               // Vuetify 인스턴스 생성기
import * as components from 'vuetify/components'     // 모든 컴포넌트
import * as directives from 'vuetify/directives'     // 모든 디렉티브
import '@mdi/font/css/materialdesignicons.css'       // (옵션) 아이콘 폰트

export default createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',  // mdi를 기본 아이콘 세트로 설정 (설치했을 경우)
  },
})