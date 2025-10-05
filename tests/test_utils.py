"""
测试工具模块
"""
import unittest
import tempfile
import json
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.database import DatabaseManager
from src.utils.logger import setup_logger, get_logger


class TestDatabaseManager(unittest.TestCase):
    """测试数据库管理器"""

    def setUp(self):
        """设置测试环境"""
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        self.temp_file.close()
        self.db_manager = DatabaseManager("json", self.temp_file.name)

    def tearDown(self):
        """清理测试环境"""
        Path(self.temp_file.name).unlink(missing_ok=True)

    def test_save_and_load_json_data(self):
        """测试JSON数据保存和加载"""
        test_data = [
            {
                "id": "test1",
                "repo_url": "https://github.com/owner/repo1",
                "owner": "owner",
                "repo_name": "repo1"
            },
            {
                "id": "test2",
                "repo_url": "https://github.com/owner/repo2",
                "owner": "owner",
                "repo_name": "repo2"
            }
        ]

        self.db_manager.save_data(test_data)
        loaded_data = self.db_manager.load_data()

        self.assertEqual(len(loaded_data), 2)
        self.assertEqual(loaded_data[0]["id"], "test1")
        self.assertEqual(loaded_data[1]["repo_name"], "repo2")


class TestLogger(unittest.TestCase):
    """测试日志工具"""

    def test_logger_setup(self):
        """测试日志器设置"""
        logger = setup_logger("DEBUG")
        self.assertEqual(logger.name, "github_sentinel")

        child_logger = get_logger("test_module")
        self.assertEqual(child_logger.name, "github_sentinel.test_module")


if __name__ == '__main__':
    unittest.main()
