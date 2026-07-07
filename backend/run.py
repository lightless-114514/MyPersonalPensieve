"""PyInstaller 打包入口脚本。

Electron 启动时会以子进程方式运行此可执行文件。
启动后通过 stdout 输出 `PENSIEVE_READY` 表示服务就绪。
"""
import os
import sys
import socket


def _wait_port_ready(host: str, port: int) -> bool:
    """检查端口是否可连。"""
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except OSError:
        return False


def main():
    # 打包后修复 sys.path（PyInstaller 临时目录）
    if getattr(sys, "frozen", False):
        os.environ.setdefault("PYTHONPATH", sys._MEIPASS)  # type: ignore[attr-defined]

    # 读取环境变量配置（由 Electron 注入）
    host = os.environ.get("SERVER_HOST", "127.0.0.1")
    port = int(os.environ.get("SERVER_PORT", "8000"))

    # 输出启动信号（Electron 据此判断后端已启动）
    print(f"PENSIEVE_STARTING host={host} port={port}", flush=True)

    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        log_level="info",
        access_log=False,
    )


if __name__ == "__main__":
    main()
