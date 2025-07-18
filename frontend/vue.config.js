module.exports = {
  transpileDependencies: ['vuetify'],
  publicPath: process.env.NODE_ENV === 'production' ? '/static/' : '/',
  devServer: {
    host: '0.0.0.0',
    port: 8081,               // 프론트엔드가 실제 띄워진 포트
  }
}

