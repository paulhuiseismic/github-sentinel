"""
数据库管理工具
"""
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_type: str = "json", db_path: str = "data/subscriptions.json"):
        self.db_type = db_type
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """确保数据库文件存在"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        if self.db_type == "json" and not self.db_path.exists():
            self._save_json_data([])
        elif self.db_type == "sqlite":
            self._init_sqlite_db()

    def _save_json_data(self, data: List[Dict[str, Any]]):
        """保存JSON数据"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存JSON数据失败: {e}")
            raise

    def _load_json_data(self) -> List[Dict[str, Any]]:
        """加载JSON数据"""
        try:
            if not self.db_path.exists():
                return []
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载JSON数据失败: {e}")
            return []

    def _init_sqlite_db(self):
        """初始化SQLite数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS subscriptions (
                        id TEXT PRIMARY KEY,
                        repo_url TEXT NOT NULL,
                        owner TEXT NOT NULL,
                        repo_name TEXT NOT NULL,
                        notification_types TEXT NOT NULL,
                        frequency TEXT NOT NULL,
                        update_types TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        last_checked TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        filters TEXT,
                        notification_config TEXT
                    )
                ''')
                conn.commit()
        except Exception as e:
            self.logger.error(f"初始化SQLite数据库失败: {e}")
            raise

    def save_data(self, data: List[Dict[str, Any]]):
        """保存数据"""
        if self.db_type == "json":
            self._save_json_data(data)
        elif self.db_type == "sqlite":
            self._save_sqlite_data(data)

    def load_data(self) -> List[Dict[str, Any]]:
        """加载数据"""
        if self.db_type == "json":
            return self._load_json_data()
        elif self.db_type == "sqlite":
            return self._load_sqlite_data()
        return []

    def _save_sqlite_data(self, data: List[Dict[str, Any]]):
        """保存SQLite数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 清空现有数据
                conn.execute("DELETE FROM subscriptions")

                # 插入新数据
                for item in data:
                    conn.execute('''
                        INSERT INTO subscriptions 
                        (id, repo_url, owner, repo_name, notification_types, frequency, 
                         update_types, created_at, last_checked, is_active, filters, notification_config)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        item['id'], item['repo_url'], item['owner'], item['repo_name'],
                        json.dumps(item['notification_types']), item['frequency'],
                        json.dumps(item['update_types']), item['created_at'],
                        item.get('last_checked'), item.get('is_active', True),
                        json.dumps(item.get('filters')) if item.get('filters') else None,
                        json.dumps(item.get('notification_config')) if item.get('notification_config') else None
                    ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"保存SQLite数据失败: {e}")
            raise

    def _load_sqlite_data(self) -> List[Dict[str, Any]]:
        """加载SQLite数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM subscriptions")
                rows = cursor.fetchall()

                data = []
                for row in rows:
                    item = dict(row)
                    # 解析JSON字段
                    item['notification_types'] = json.loads(item['notification_types'])
                    item['update_types'] = json.loads(item['update_types'])
                    if item['filters']:
                        item['filters'] = json.loads(item['filters'])
                    if item['notification_config']:
                        item['notification_config'] = json.loads(item['notification_config'])
                    data.append(item)

                return data
        except Exception as e:
            self.logger.error(f"加载SQLite数据失败: {e}")
            return []
