"""
基于图数据库的RAG系统配置文件 - 智能膳食健康顾问
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class GraphRAGConfig:
    """基于图数据库的RAG系统配置类"""

    # Neo4j数据库配置
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "all-in-rag"
    neo4j_database: str = "neo4j"

    # Milvus配置
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection_name: str = "cooking_knowledge"
    milvus_dimension: int = 512

    # 模型配置
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    llm_model: str = "kimi-k2-0711-preview"

    # 检索配置
    top_k: int = 5

    # 生成配置
    temperature: float = 0.1
    max_tokens: int = 2048

    # 图数据处理配置
    chunk_size: int = 500
    chunk_overlap: int = 50
    max_graph_depth: int = 2

    # ============ 新增：持久化与多轮对话配置 ============
    # SQLite 配置
    sqlite_db_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "user_data.db")

    # Redis 配置
    redis_host: str = "localhost"
    redis_port: int = 16379  # 避免与Windows预留端口冲突
    redis_db: int = 0
    session_ttl: int = 3600  # 会话过期时间（秒），默认1小时

    # 膳食健康知识库路径
    dietary_knowledge_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "dietary_knowledge.json")

    # 多轮对话配置
    max_chat_history: int = 20  # 保留最近N轮对话

    def __post_init__(self):
        """初始化后的处理"""
        from pathlib import Path
        # 确保数据目录存在
        data_dir = os.path.dirname(self.sqlite_db_path)
        Path(data_dir).mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'GraphRAGConfig':
        """从字典创建配置对象"""
        return cls(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'neo4j_uri': self.neo4j_uri,
            'neo4j_user': self.neo4j_user,
            'neo4j_password': self.neo4j_password,
            'neo4j_database': self.neo4j_database,
            'milvus_host': self.milvus_host,
            'milvus_port': self.milvus_port,
            'milvus_collection_name': self.milvus_collection_name,
            'milvus_dimension': self.milvus_dimension,
            'embedding_model': self.embedding_model,
            'llm_model': self.llm_model,
            'top_k': self.top_k,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'max_graph_depth': self.max_graph_depth,
            'sqlite_db_path': self.sqlite_db_path,
            'redis_host': self.redis_host,
            'redis_port': self.redis_port,
            'session_ttl': self.session_ttl,
            'max_chat_history': self.max_chat_history,
        }

# 默认配置实例
DEFAULT_CONFIG = GraphRAGConfig() 