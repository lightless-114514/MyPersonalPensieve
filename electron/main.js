/**
 * MyPersonalPensieve 桌面端 - Electron 主进程
 *
 * 职责：
 * 1. 启动 Python 后端子进程（打包后的 exe 或开发模式下的 python）
 * 2. 等待后端就绪（端口探测）
 * 3. 创建窗口加载前端（开发模式加载 localhost:5173，生产加载本地静态文件）
 * 4. 应用退出时优雅关闭后端
 */
const { app, BrowserWindow, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const net = require('net');

const isDev = process.env.PENSIEVE_DEV === '1';
const SERVER_HOST = '127.0.0.1';
const SERVER_PORT = 8080;

let backendProcess = null;
let mainWindow = null;
let backendReady = false;

// 日志
const log = (...args) => console.log('[main]', ...args);

/**
 * 获取后端可执行文件路径。
 * 生产模式：resourcesPath/pensieve_backend/pensieve_backend.exe
 * 开发模式：直接用 python 启动
 */
function getBackendCommand() {
  if (isDev) {
    return {
      cmd: 'python',
      args: ['-m', 'uvicorn', 'app.main:app', '--host', SERVER_HOST, '--port', String(SERVER_PORT)],
      cwd: path.join(__dirname, '..', 'backend'),
    };
  }
  const exeName = process.platform === 'win32' ? 'pensieve_backend.exe' : 'pensieve_backend';
  const backendDir = path.join(process.resourcesPath, 'pensieve_backend');
  return {
    cmd: path.join(backendDir, exeName),
    args: [],
    cwd: backendDir,
  };
}

/**
 * 获取数据目录（用户文档目录下的 Pensieve）。
 */
function getDataDir() {
  const userDir = app.getPath('userData');
  return path.join(userDir, 'data');
}

/**
 * 启动后端子进程。
 */
function startBackend() {
  const { cmd, args, cwd } = getBackendCommand();
  const dataDir = getDataDir();
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }

  log('启动后端:', cmd, args.join(' '));
  log('工作目录:', cwd);
  log('数据目录:', dataDir);

  const env = {
    ...process.env,
    PENSIEVE_DATA_DIR: dataDir,
    SERVER_HOST,
    SERVER_PORT: String(SERVER_PORT),
    PYTHONUNBUFFERED: '1',
    PYTHONIOENCODING: 'utf-8',
  };

  backendProcess = spawn(cmd, args, { cwd, env, windowsHide: true });

  backendProcess.stdout.on('data', (data) => {
    const text = data.toString();
    process.stdout.write(`[backend] ${text}`);
  });

  backendProcess.stderr.on('data', (data) => {
    const text = data.toString();
    process.stderr.write(`[backend] ${text}`);
  });

  backendProcess.on('exit', (code, signal) => {
    log(`后端进程退出 code=${code} signal=${signal}`);
    backendProcess = null;
  });

  backendProcess.on('error', (err) => {
    log('后端启动失败:', err.message);
  });
}

/**
 * 探测后端端口是否就绪。
 */
function waitForBackend(maxRetries = 60, interval = 500) {
  return new Promise((resolve, reject) => {
    let retries = 0;
    const tryConnect = () => {
      const socket = new net.Socket();
      socket.setTimeout(1000);
      socket.on('connect', () => {
        socket.destroy();
        backendReady = true;
        log('后端就绪');
        resolve();
      });
      socket.on('error', () => {
        socket.destroy();
        retries += 1;
        if (retries >= maxRetries) {
          reject(new Error(`后端启动超时（${maxRetries * interval / 1000}s）`));
        } else {
          setTimeout(tryConnect, interval);
        }
      });
      socket.on('timeout', () => {
        socket.destroy();
        retries += 1;
        if (retries >= maxRetries) {
          reject(new Error(`后端启动超时（${maxRetries * interval / 1000}s）`));
        } else {
          setTimeout(tryConnect, interval);
        }
      });
      socket.connect(SERVER_PORT, SERVER_HOST);
    };
    tryConnect();
  });
}

/**
 * 创建主窗口。
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: 'Pensieve',
    backgroundColor: '#0f172a',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // 外部链接在系统浏览器打开
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http://') || url.startsWith('https://')) {
      shell.openExternal(url);
      return { action: 'deny' };
    }
    return { action: 'allow' };
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    const frontendPath = path.join(process.resourcesPath, 'frontend', 'index.html');
    log('加载前端:', frontendPath);
    mainWindow.loadFile(frontendPath);
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

/**
 * 优雅关闭后端。
 */
function stopBackend() {
  if (!backendProcess) return Promise.resolve();
  return new Promise((resolve) => {
    const proc = backendProcess;
    let exited = false;
    const onExit = () => {
      if (exited) return;
      exited = true;
      resolve();
    };
    proc.on('exit', onExit);
    proc.on('error', onExit);

    // 优先发送 Ctrl-C（SIGINT），让 uvicorn 优雅关闭
    try {
      if (process.platform === 'win32') {
        // Windows 下用 taskkill 强制终止进程树
        spawn('taskkill', ['/pid', String(proc.pid), '/f', '/t']);
      } else {
        proc.kill('SIGTERM');
      }
    } catch (e) {
      log('关闭后端失败:', e.message);
    }

    // 3 秒后强制结束
    setTimeout(() => {
      if (!exited) {
        try { proc.kill('SIGKILL'); } catch (e) { /* ignore */ }
        onExit();
      }
    }, 3000);
  });
}

// ============ 应用生命周期 ============

app.whenReady().then(async () => {
  startBackend();
  try {
    await waitForBackend();
  } catch (err) {
    log(err.message);
    // 即使后端没起来也尝试打开窗口，让用户看到错误
  }
  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    stopBackend().then(() => app.quit());
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', (event) => {
  if (backendProcess) {
    event.preventDefault();
    stopBackend().then(() => app.quit());
  }
});

// 捕获未处理异常，避免静默崩溃
process.on('uncaughtException', (err) => {
  log('未处理异常:', err.stack || err.message);
});
