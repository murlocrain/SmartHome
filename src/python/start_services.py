"""
一键启动所有微服务
用法:
  python start_services.py                    # 启动全部4个服务
  python start_services.py gateway_service    # 仅启动网关服务
  python start_services.py user_service       # 仅启动用户服务
  python start_services.py device_service     # 仅启动设备服务
  python start_services.py scene_service      # 仅启动场景服务
"""
import uvicorn
import multiprocessing
import sys
import os

# 确保从 python/ 目录运行
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 添加 ai/src/ 到 sys.path，以便启动 agent_service
_AI_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ai', 'src'))
if _AI_SRC not in sys.path:
    sys.path.insert(0, _AI_SRC)

from common.config import settings


def run_service(service_name: str, port: int):
    print(f"Starting {service_name} on port {port}...")
    uvicorn.run(
        f"services.{service_name}.main:app" if service_name != "agent_service" else "agent_service.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
    )


def main():
    services = {
        "gateway_service": 8010,
        "user_service": 8011,
        "device_service": 8012,
        "agent_service": 8013,
        "scene_service": 8014,
    }

    if len(sys.argv) > 1:
        service_name = sys.argv[1]
        if service_name in services:
            run_service(service_name, services[service_name])
        else:
            print(f"Unknown service: {service_name}")
            print(f"Available services: {', '.join(services.keys())}")
            sys.exit(1)
    else:
        print("Starting all services...")
        processes = []
        for service_name, port in services.items():
            process = multiprocessing.Process(target=run_service, args=(service_name, port))
            process.start()
            processes.append(process)
            print(f"  [OK] {service_name} started on port {port} (PID: {process.pid})")

        print(f"\nAll {len(processes)} services are running.")
        print("Press Ctrl+C to stop all services.\n")

        try:
            for process in processes:
                process.join()
        except KeyboardInterrupt:
            print("\nStopping all services...")
            for process in processes:
                process.terminate()
                process.join(timeout=5)
            print("All services stopped.")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
