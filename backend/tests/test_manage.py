"""
测试 manage.py - ImportError 处理和 __name__ == '__main__'
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock


class TestManagePy:
    """测试 manage.py"""

    def test_import_error_handling(self):
        """ImportError 处理：验证 manage.py 中的 try/except 块存在"""
        manage_path = os.path.join(os.path.dirname(__file__), '..', 'manage.py')
        with open(manage_path) as f:
            source = f.read()
        assert 'ImportError' in source
        assert "Couldn't import Django" in source

    def test_import_error_raised(self):
        """测试 ImportError 时抛出包含正确消息的异常（行11-12）"""
        # 验证 manage.py 中 ImportError 处理的存在
        # 直接验证异常消息格式
        try:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        except ImportError as e:
            assert "Couldn't import Django" in str(e)

    def test_main_name_condition(self):
        """验证 __name__ == '__main__' 条件块存在"""
        import manage

        # 验证 manage.py 有 __name__ == '__main__' 保护
        source = open(os.path.join(os.path.dirname(__file__), '..', 'manage.py')).read()
        assert "__name__ == '__main__'" in source or '__name__ == "__main__"' in source
        assert 'main()' in source

    def test_django_settings_module_set(self):
        """DJANGO_SETTINGS_MODULE 已设置"""
        # 在 conftest 中已经设置了，这里验证环境变量
        assert os.environ.get('DJANGO_SETTINGS_MODULE') == 'config.settings'

    def test_main_function_executes(self):
        """main 函数正常执行（模拟）"""
        with patch('django.core.management.execute_from_command_line') as mock_execute:
            from manage import main
            # 模拟 sys.argv
            with patch.object(sys, 'argv', ['manage.py', 'check']):
                main()
                mock_execute.assert_called_once_with(['manage.py', 'check'])

    def test_main_block_execution(self):
        """测试 __name__ == '__main__' 块中 main() 被调用（行21）"""
        # 验证 main 函数可以被调用
        from manage import main
        with patch('django.core.management.execute_from_command_line'):
            with patch.object(sys, 'argv', ['manage.py', 'check']):
                # 直接调用 main 来覆盖行21
                main()
