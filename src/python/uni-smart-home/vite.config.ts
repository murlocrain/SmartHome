import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

export default defineConfig({
  plugins: [uni()],
  server: {
    port: 5177,
    proxy: {
      // 用户服务代理 - 端口8011
      '/api/v1/auth': {
        target: 'http://localhost:8011',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/v1\/auth/, '/api/v1/auth')
      },
      // 家庭管理代理
      '/api/v1/family': {
        target: 'http://localhost:8011',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/v1\/family/, '/api/v1/family')
      },
      // 设备服务代理 - 端口8012
      '/api/v1/devices': {
        target: 'http://localhost:8012',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/v1\/devices/, '/api/v1/devices')
      },
      // 设备控制代理 - 端口8012
      '/api/v1/control': {
        target: 'http://localhost:8012',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/v1\/control/, '/api/v1/control')
      },
      // 设备数据查询代理 - 端口8012
      '/api/v1/data': {
        target: 'http://localhost:8012',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/v1\/data/, '/api/v1/data')
      },
      // 场景服务代理 - 端口8014
      '/api/v1/scenes': {
        target: 'http://localhost:8014',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/v1\/scenes/, '/api/v1/scenes')
      },
      // 网关服务代理 - 端口8010
      '/connections': {
        target: 'http://localhost:8010',
        changeOrigin: true
      },
      '/health': {
        target: 'http://localhost:8010',
        changeOrigin: true
      },
      '/ready': {
        target: 'http://localhost:8010',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:8010',
        changeOrigin: true,
        ws: true
      }
    }
  }
})