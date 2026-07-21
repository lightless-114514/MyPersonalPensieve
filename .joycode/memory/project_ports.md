---
name: project_ports
description: 前后端服务端口配置信息
type: project
---

前端 Vue 应用运行在端口 5173，后端服务运行在端口 8000。

**Why:** 项目采用前后端分离架构，前端和后端分别在不同端口启动，开发时需要同时运行两个服务。

**How to apply:** 当需要启动项目、调试接口、配置代理或处理跨域问题时，使用这些端口号。前端开发服务器地址为 http://localhost:5173，后端API地址为 http://localhost:8000。