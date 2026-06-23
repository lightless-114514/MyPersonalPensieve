/**
 * 预加载脚本 - 在渲染进程的隔离世界运行。
 * 通过 contextBridge 暴露安全的 API 给前端使用。
 */
const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('pensieve', {
  /** 返回桌面端运行环境信息 */
  getEnv: () => ({
    isDesktop: true,
    apiBase: 'http://127.0.0.1:8080/api',
    version: process.env.npm_package_version || '2.0.0',
  }),
});
