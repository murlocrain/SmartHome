"""WebSocket 连接管理器。
收到华为云回调数据后，通过 broadcast() 向所有已连接的前端推送实时数据。
"""

from fastapi import WebSocket
from common.config import logger


class _ConnectionManager:
    """简单的 WebSocket 连接管理，不做多实例同步（单进程够用）。"""

    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)
        logger.info(f"WebSocket 客户端已连接，当前连接数: {len(self._connections)}")

    async def disconnect(self, ws: WebSocket) -> None:
        if ws in self._connections:
            self._connections.remove(ws)
        logger.info(f"WebSocket 客户端已断开，当前连接数: {len(self._connections)}")

    async def broadcast(self, message: dict) -> None:
        """向所有已连接客户端广播一条 JSON 消息。"""
        dead: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in self._connections:
                self._connections.remove(ws)
        if dead:
            logger.info(f"清理了 {len(dead)} 个已断开的 WebSocket 连接")

    @property
    def connection_count(self) -> int:
        return len(self._connections)


# 全局单例
manager = _ConnectionManager()
