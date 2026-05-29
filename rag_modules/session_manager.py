"""
多轮对话会话管理模块 - Phase 3
基于 Redis 存储会话上下文，支持多轮对话和历史记忆
"""

import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Redis 为可选依赖，提供降级方案
try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    logger.warning("redis 未安装，将使用内存存储作为降级方案")


class SessionManager:
    """多轮对话会话管理器（Redis 主，内存降级）"""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0,
                 ttl: int = 3600, max_history: int = 20):
        self.ttl = ttl
        self.max_history = max_history
        self._use_redis = False
        self._client = None
        self._memory_store: Dict[str, Dict] = {}  # 内存降级存储

        if HAS_REDIS:
            try:
                self._client = redis.Redis(host=host, port=port, db=db,
                                           socket_connect_timeout=3, decode_responses=True)
                self._client.ping()
                self._use_redis = True
                logger.info(f"Redis 会话管理器已连接: {host}:{port}")
            except Exception as e:
                logger.warning(f"Redis 连接失败: {e}，降级为内存存储")
                self._client = None
        else:
            logger.warning("Redis 不可用，使用内存存储（重启后数据丢失）")

    def _key(self, session_id: str) -> str:
        return f"session:{session_id}"

    def create_session(self, session_id: str, user_id: str = "",
                       user_profile: Optional[Dict] = None) -> Dict:
        """创建新会话"""
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "user_profile": user_profile or {},
            "chat_history": [],
            "context": {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        self._save(session_id, session_data)
        logger.info(f"创建会话: {session_id}")
        return session_data

    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话"""
        return self._load(session_id)

    def add_message(self, session_id: str, role: str, content: str,
                    metadata: Optional[Dict] = None) -> bool:
        """添加一条消息到会话"""
        session = self._load(session_id)
        if session is None:
            logger.warning(f"会话不存在: {session_id}")
            return False

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        session["chat_history"].append(message)

        # 保留最近 N 轮
        if len(session["chat_history"]) > self.max_history * 2:  # user + assistant = 1轮
            session["chat_history"] = session["chat_history"][-self.max_history * 2:]

        session["updated_at"] = datetime.now().isoformat()
        self._save(session_id, session)
        return True

    def get_chat_history(self, session_id: str, recent_n: int = 10) -> List[Dict]:
        """获取最近的对话历史"""
        session = self._load(session_id)
        if session is None:
            return []
        history = session.get("chat_history", [])
        return history[-recent_n:] if recent_n > 0 else history

    def set_context(self, session_id: str, key: str, value: Any) -> bool:
        """设置会话上下文"""
        session = self._load(session_id)
        if session is None:
            return False
        session["context"][key] = value
        session["updated_at"] = datetime.now().isoformat()
        self._save(session_id, session)
        return True

    def get_context(self, session_id: str, key: str, default: Any = None) -> Any:
        """获取会话上下文"""
        session = self._load(session_id)
        if session is None:
            return default
        return session.get("context", {}).get(key, default)

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if self._use_redis and self._client:
            self._client.delete(self._key(session_id))
        else:
            self._memory_store.pop(session_id, None)
        return True

    def extend_ttl(self, session_id: str) -> bool:
        """延长会话过期时间"""
        if self._use_redis and self._client:
            return self._client.expire(self._key(session_id), self.ttl)
        return True  # 内存模式无需操作

    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        if self._use_redis and self._client:
            return self._client.exists(self._key(session_id)) > 0
        return session_id in self._memory_store

    def list_active_sessions(self) -> List[str]:
        """列出活跃会话"""
        if self._use_redis and self._client:
            keys = self._client.keys("session:*")
            return [k.decode() if isinstance(k, bytes) else k for k in keys]
        return list(self._memory_store.keys())

    def _save(self, session_id: str, data: Dict):
        """保存会话"""
        serialized = json.dumps(data, ensure_ascii=False)
        if self._use_redis and self._client:
            self._client.setex(self._key(session_id), self.ttl, serialized)
        else:
            self._memory_store[session_id] = data

    def _load(self, session_id: str) -> Optional[Dict]:
        """加载会话"""
        if self._use_redis and self._client:
            raw = self._client.get(self._key(session_id))
            if raw:
                return json.loads(raw)
        else:
            return self._memory_store.get(session_id)
        return None

    def close(self):
        """关闭连接"""
        if self._use_redis and self._client:
            self._client.close()
            logger.info("Redis 会话连接已关闭")
