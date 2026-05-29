"""
用户画像持久化模块 - Phase 3
基于 SQLite 存储用户体质/病症/忌口/偏好数据
"""

import sqlite3
import hashlib
import uuid
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """用户画像"""
    user_id: str = ""
    name: str = "匿名用户"
    password_hash: str = ""
    token: str = ""
    constitutions: List[str] = field(default_factory=list)  # 体质: ["气虚质", "痰湿质"]
    health_conditions: List[str] = field(default_factory=list)  # 病症: ["糖尿病", "高血压"]
    dietary_restrictions: List[str] = field(default_factory=list)  # 忌口: ["海鲜过敏"]
    cuisine_preferences: List[str] = field(default_factory=list)  # 菜系偏好: ["川菜", "粤菜"]
    caloric_target: int = 0  # 每日热量目标(kcal)，0表示不限
    meal_count: int = 3  # 每日餐数
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'name': self.name,
            'constitutions': ','.join(self.constitutions),
            'health_conditions': ','.join(self.health_conditions),
            'dietary_restrictions': ','.join(self.dietary_restrictions),
            'cuisine_preferences': ','.join(self.cuisine_preferences),
            'caloric_target': self.caloric_target,
            'meal_count': self.meal_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    @classmethod
    def from_row(cls, row: tuple, columns: List[str]) -> 'UserProfile':
        """从 SQLite 行数据构建 UserProfile"""
        data = dict(zip(columns, row))
        # 解析逗号分隔的列表
        for field in ['constitutions', 'health_conditions', 'dietary_restrictions', 'cuisine_preferences']:
            val = data.get(field, '')
            data[field] = [x.strip() for x in val.split(',') if x.strip()] if val else []
        # Remove password_hash and token from data if they're not in the dataclass fields (old tables)
        kwargs = {}
        for k in ['user_id', 'name', 'password_hash', 'token', 'constitutions', 'health_conditions',
                  'dietary_restrictions', 'cuisine_preferences', 'caloric_target', 'meal_count',
                  'created_at', 'updated_at']:
            kwargs[k] = data.get(k, '')
        return cls(**kwargs)


class UserProfileManager:
    """基于 SQLite 的用户画像管理器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = None
        return conn

    def _init_db(self):
        """初始化数据库表"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    name TEXT DEFAULT '匿名用户',
                    password_hash TEXT DEFAULT '',
                    token TEXT DEFAULT '',
                    constitutions TEXT DEFAULT '',
                    health_conditions TEXT DEFAULT '',
                    dietary_restrictions TEXT DEFAULT '',
                    cuisine_preferences TEXT DEFAULT '',
                    caloric_target INTEGER DEFAULT 0,
                    meal_count INTEGER DEFAULT 3,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)

            # 兼容旧表：尝试添加新列
            for col in ['password_hash', 'token']:
                try:
                    conn.execute(f"ALTER TABLE user_profiles ADD COLUMN {col} TEXT DEFAULT ''")
                except:
                    pass

            conn.execute("""
                CREATE TABLE IF NOT EXISTS meal_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    meal_type TEXT,
                    recipe_name TEXT,
                    recipe_node_id TEXT,
                    rating INTEGER DEFAULT 0,
                    feedback TEXT DEFAULT '',
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    query TEXT,
                    response TEXT,
                    rating INTEGER DEFAULT 0,
                    feedback_text TEXT DEFAULT '',
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT DEFAULT '新对话',
                    message_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)
            conn.commit()

        logger.info(f"用户画像数据库已初始化: {self.db_path}")

    def create_user(self, user_id: str, name: str = "匿名用户",
                    constitutions: Optional[List[str]] = None,
                    conditions: Optional[List[str]] = None,
                    restrictions: Optional[List[str]] = None,
                    preferences: Optional[List[str]] = None) -> UserProfile:
        """创建用户画像"""
        profile = UserProfile(
            user_id=user_id,
            name=name,
            constitutions=constitutions or [],
            health_conditions=conditions or [],
            dietary_restrictions=restrictions or [],
            cuisine_preferences=preferences or []
        )
        self.save_profile(profile)
        logger.info(f"创建用户画像: {user_id}")
        return profile

    def save_profile(self, profile: UserProfile) -> bool:
        """保存或更新用户画像"""
        profile.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO user_profiles
                        (user_id, name, constitutions, health_conditions,
                         dietary_restrictions, cuisine_preferences,
                         caloric_target, meal_count, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        name=excluded.name,
                        constitutions=excluded.constitutions,
                        health_conditions=excluded.health_conditions,
                        dietary_restrictions=excluded.dietary_restrictions,
                        cuisine_preferences=excluded.cuisine_preferences,
                        caloric_target=excluded.caloric_target,
                        meal_count=excluded.meal_count,
                        updated_at=excluded.updated_at
                """, (
                    profile.user_id, profile.name,
                    ','.join(profile.constitutions),
                    ','.join(profile.health_conditions),
                    ','.join(profile.dietary_restrictions),
                    ','.join(profile.cuisine_preferences),
                    profile.caloric_target, profile.meal_count,
                    profile.created_at, profile.updated_at
                ))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"保存用户画像失败: {e}")
            return False

    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户画像"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)
                )
                columns = [desc[0] for desc in cursor.description]
                row = cursor.fetchone()
                if row:
                    return UserProfile.from_row(row, columns)
        except Exception as e:
            logger.error(f"获取用户画像失败: {e}")
        return None

    def delete_profile(self, user_id: str) -> bool:
        """删除用户画像"""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM user_profiles WHERE user_id = ?", (user_id,))
                conn.execute("DELETE FROM meal_history WHERE user_id = ?", (user_id,))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"删除用户画像失败: {e}")
            return False

    def update_constitutions(self, user_id: str, constitutions: List[str]) -> bool:
        """更新体质"""
        return self._update_field(user_id, 'constitutions', ','.join(constitutions))

    def update_conditions(self, user_id: str, conditions: List[str]) -> bool:
        """更新健康关注"""
        return self._update_field(user_id, 'health_conditions', ','.join(conditions))

    def update_restrictions(self, user_id: str, restrictions: List[str]) -> bool:
        """更新饮食限制"""
        return self._update_field(user_id, 'dietary_restrictions', ','.join(restrictions))

    def _update_field(self, user_id: str, field: str, value: str) -> bool:
        try:
            with self._get_connection() as conn:
                conn.execute(
                    f"UPDATE user_profiles SET {field}=?, updated_at=? WHERE user_id=?",
                    (value, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id)
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"更新字段失败: {e}")
            return False

    # ===== 用餐历史 =====
    def log_meal(self, user_id: str, meal_type: str, recipe_name: str,
                 recipe_node_id: str = "", rating: int = 0) -> int:
        """记录用餐历史，返回记录ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO meal_history (user_id, meal_type, recipe_name, recipe_node_id, rating)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, meal_type, recipe_name, recipe_node_id, rating))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"记录用餐历史失败: {e}")
            return -1

    def get_recent_meals(self, user_id: str, days: int = 7) -> List[Dict]:
        """获取最近的用餐记录"""
        try:
            with self._get_connection() as conn:
                rows = conn.execute("""
                    SELECT meal_type, recipe_name, recipe_node_id, rating, created_at
                    FROM meal_history
                    WHERE user_id = ? AND created_at >= datetime('now', '-' || ? || ' days', 'localtime')
                    ORDER BY created_at DESC
                    LIMIT 50
                """, (user_id, days)).fetchall()
                return [{"meal_type": r[0], "recipe_name": r[1], "recipe_node_id": r[2],
                         "rating": r[3], "created_at": r[4]} for r in rows]
        except Exception as e:
            logger.error(f"获取用餐记录失败: {e}")
            return []

    def get_rated_recipes(self, user_id: str, min_rating: int = 3) -> List[str]:
        """获取用户高评分菜谱列表（用于去重推荐）"""
        try:
            with self._get_connection() as conn:
                rows = conn.execute("""
                    SELECT DISTINCT recipe_name FROM meal_history
                    WHERE user_id = ? AND rating >= ?
                    ORDER BY created_at DESC
                """, (user_id, min_rating)).fetchall()
                return [r[0] for r in rows]
        except Exception as e:
            logger.error(f"获取评分菜谱失败: {e}")
            return []

    # ===== 反馈日志 =====
    def log_feedback(self, user_id: str, query: str, response: str,
                     rating: int = 0, feedback_text: str = "") -> bool:
        """记录用户反馈"""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO feedback_log (user_id, query, response, rating, feedback_text)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, query, response, rating, feedback_text))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"记录反馈失败: {e}")
            return False

    def get_feedback_stats(self, user_id: str) -> Dict:
        """获取用户反馈统计"""
        try:
            with self._get_connection() as conn:
                total = conn.execute(
                    "SELECT COUNT(*) FROM feedback_log WHERE user_id=?", (user_id,)
                ).fetchone()[0]
                avg_rating = conn.execute(
                    "SELECT AVG(rating) FROM feedback_log WHERE user_id=? AND rating>0", (user_id,)
                ).fetchone()[0] or 0
                return {"total_feedbacks": total, "avg_rating": round(avg_rating, 2)}
        except Exception:
            return {"total_feedbacks": 0, "avg_rating": 0}

    # ===== 认证相关 =====
    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(f"dietary_advisor_salt_{password}".encode()).hexdigest()

    @staticmethod
    def _generate_token() -> str:
        return uuid.uuid4().hex

    def register(self, username: str, password: str, name: str = "") -> Dict:
        """注册新用户，返回 {success, user_id, token, error}"""
        user_id = f"user_{username}"
        existing = self.get_profile(user_id)
        if existing:
            return {"success": False, "error": "用户名已存在"}

        pw_hash = self._hash_password(password)
        token = self._generate_token()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO user_profiles (user_id, name, password_hash, token, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, name or username, pw_hash, token, now, now))
                conn.commit()
            logger.info(f"注册用户: {user_id}")
            return {"success": True, "user_id": user_id, "token": token, "name": name or username}
        except Exception as e:
            logger.error(f"注册失败: {e}")
            return {"success": False, "error": str(e)}

    def login(self, username: str, password: str) -> Dict:
        """登录验证，返回 {success, user_id, token, profile, error}"""
        user_id = f"user_{username}"
        try:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT password_hash, name FROM user_profiles WHERE user_id=?",
                    (user_id,)
                ).fetchone()
                if not row:
                    return {"success": False, "error": "用户不存在"}

                stored_hash = row[0]
                expected_hash = self._hash_password(password)

                if stored_hash == expected_hash:
                    token = self._generate_token()
                    conn.execute(
                        "UPDATE user_profiles SET token=?, updated_at=? WHERE user_id=?",
                        (token, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id)
                    )
                    conn.commit()
                    profile = self.get_profile(user_id)
                    logger.info(f"用户登录: {user_id}")
                    return {
                        "success": True, "user_id": user_id,
                        "token": token, "name": row[1],
                        "profile": profile.to_dict() if profile else {}
                    }
                else:
                    return {"success": False, "error": "密码错误"}
        except Exception as e:
            logger.error(f"登录失败: {e}")
            return {"success": False, "error": str(e)}

    def verify_token(self, token: str) -> Optional[str]:
        """验证token，返回user_id或None"""
        if not token:
            return None
        try:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT user_id FROM user_profiles WHERE token=?",
                    (token,)
                ).fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"Token验证失败: {e}")
            return None

    # ===== 会话跟踪 =====
    def save_session(self, session_id: str, user_id: str, message_count: int = 0):
        """保存会话引用到 SQLite"""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO user_sessions (session_id, user_id, message_count, created_at, updated_at)
                    VALUES (?, ?, ?, datetime('now','localtime'), datetime('now','localtime'))
                    ON CONFLICT(session_id) DO UPDATE SET
                        message_count=?,
                        updated_at=datetime('now','localtime')
                """, (session_id, user_id, message_count, message_count))
                conn.commit()
        except Exception as e:
            logger.error(f"保存会话失败: {e}")

    def update_session_title(self, session_id: str, title: str):
        """更新会话标题（自动从首条消息提取）"""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "UPDATE user_sessions SET title=?, updated_at=datetime('now','localtime') WHERE session_id=?",
                    (title[:50], session_id)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"更新会话标题失败: {e}")

    def get_user_sessions(self, user_id: str, limit: int = 20) -> List[Dict]:
        """获取用户的会话列表"""
        try:
            with self._get_connection() as conn:
                rows = conn.execute("""
                    SELECT session_id, title, message_count, created_at, updated_at
                    FROM user_sessions WHERE user_id=?
                    ORDER BY updated_at DESC LIMIT ?
                """, (user_id, limit)).fetchall()
                return [{"session_id": r[0], "title": r[1], "message_count": r[2],
                         "created_at": r[3], "updated_at": r[4]} for r in rows]
        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            return []

    def delete_session(self, session_id: str):
        """删除会话引用"""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM user_sessions WHERE session_id=?", (session_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"删除会话失败: {e}")

    def list_all_users(self) -> List[Dict]:
        """列出所有用户"""
        try:
            with self._get_connection() as conn:
                rows = conn.execute(
                    "SELECT user_id, name, created_at, updated_at FROM user_profiles ORDER BY updated_at DESC"
                ).fetchall()
                return [{"user_id": r[0], "name": r[1], "created_at": r[2], "updated_at": r[3]} for r in rows]
        except Exception as e:
            logger.error(f"列出用户失败: {e}")
            return []
