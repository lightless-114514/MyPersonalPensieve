/**
 * 一键构建脚本 - 构建完整的桌面端安装包
 *
 * 流程：
 * 1. 构建前端（Vue → 静态文件）
 * 2. 打包 Python 后端（PyInstaller → pensieve_backend.exe）
 * 3. 打包 Electron 应用（electron-builder → 安装包/便携版）
 *
 * 用法：
 *   node scripts/build.js           # 完整构建
 *   node scripts/build.js --skip-frontend
 *   node scripts/build.js --skip-backend
 *   node scripts/build.js --skip-electron
 */
const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const ROOT = path.join(__dirname, '..');
const FRONTEND = path.join(ROOT, 'frontend');
const BACKEND = path.join(ROOT, 'backend');
const ELECTRON = path.join(ROOT, 'electron');

const args = process.argv.slice(2);
const skipFrontend = args.includes('--skip-frontend');
const skipBackend = args.includes('--skip-backend');
const skipElectron = args.includes('--skip-electron');

function log(msg) {
  console.log(`\n\x1b[36m[build]\x1b[0m ${msg}`);
}

function run(cmd, opts = {}) {
  console.log(`\x1b[90m$ ${cmd}\x1b[0m`);
  execSync(cmd, { stdio: 'inherit', shell: true, ...opts });
}

function checkDir(dir, name) {
  if (!fs.existsSync(dir)) {
    console.error(`\x1b[31m错误：${name} 目录不存在: ${dir}\x1b[0m`);
    process.exit(1);
  }
}

async function main() {
  log('=== MyPersonalPensieve 桌面端构建 ===');
  log(`Root: ${ROOT}`);

  // ---------- 1. 构建前端 ----------
  if (!skipFrontend) {
    log('步骤 1/3: 构建前端 (Vue + Vite)');
    checkDir(FRONTEND, 'frontend');
    run('npm install', { cwd: FRONTEND });
    run('npm run build', { cwd: FRONTEND });

    const distDir = path.join(FRONTEND, 'dist');
    if (!fs.existsSync(distDir)) {
      console.error('\x1b[31m前端构建失败：dist 目录不存在\x1b[0m');
      process.exit(1);
    }
    log(`前端构建完成: ${distDir}`);
  } else {
    log('跳过前端构建');
  }

  // ---------- 2. 打包 Python 后端 ----------
  if (!skipBackend) {
    log('步骤 2/3: 打包 Python 后端 (PyInstaller)');
    checkDir(BACKEND, 'backend');

    // 检查 pyinstaller 是否安装
    try {
      run('python -m PyInstaller --version', { cwd: BACKEND });
    } catch (e) {
      log('PyInstaller 未安装，正在安装...');
      run('python -m pip install pyinstaller', { cwd: BACKEND });
    }

    // 清理旧的构建
    const specFile = path.join(BACKEND, 'pensieve_backend.spec');
    if (!fs.existsSync(specFile)) {
      console.error('\x1b[31m错误：pensieve_backend.spec 不存在\x1b[0m');
      process.exit(1);
    }

    run('python -m PyInstaller pensieve_backend.spec --noconfirm --clean', { cwd: BACKEND });

    const backendDist = path.join(BACKEND, 'dist', 'pensieve_backend');
    if (!fs.existsSync(backendDist)) {
      console.error('\x1b[31m后端打包失败：dist/pensieve_backend 目录不存在\x1b[0m');
      process.exit(1);
    }
    log(`后端打包完成: ${backendDist}`);
  } else {
    log('跳过后端打包');
  }

  // ---------- 3. 打包 Electron 应用 ----------
  if (!skipElectron) {
    log('步骤 3/3: 打包 Electron 应用 (electron-builder)');
    checkDir(ELECTRON, 'electron');

    // 检查前置产物
    const frontendDist = path.join(FRONTEND, 'dist');
    const backendDist = path.join(BACKEND, 'dist', 'pensieve_backend');
    if (!fs.existsSync(frontendDist)) {
      console.error('\x1b[31m错误：前端未构建，请先运行 --skip-electron 或去掉 --skip-frontend\x1b[0m');
      process.exit(1);
    }
    if (!fs.existsSync(backendDist)) {
      console.error('\x1b[31m错误：后端未打包，请先运行 --skip-electron 或去掉 --skip-backend\x1b[0m');
      process.exit(1);
    }

    run('npm install', { cwd: ELECTRON });
    run('npm run dist', { cwd: ELECTRON });

    const releaseDir = path.join(ELECTRON, 'release');
    if (fs.existsSync(releaseDir)) {
      const files = fs.readdirSync(releaseDir).filter(f => f.endsWith('.exe'));
      log('构建产物：');
      files.forEach(f => console.log(`  - ${path.join(releaseDir, f)}`));
    }
  } else {
    log('跳过 Electron 打包');
  }

  log('=== 构建完成 ===');
  console.log('\n\x1b[32m输出目录：electron/release/\x1b[0m');
  console.log('  - Pensieve-x.x.x-x64.exe (NSIS 安装包)');
  console.log('  - Pensieve-x.x.x-portable.exe (便携版，双击即用)\n');
}

main().catch((err) => {
  console.error('\x1b[31m构建失败：\x1b[0m', err.message);
  process.exit(1);
});
