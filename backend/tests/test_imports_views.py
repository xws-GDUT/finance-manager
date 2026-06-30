"""
测试 imports.views - 流水导入 API
"""
import pytest
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from apps.imports.models import ImportLog


@pytest.mark.django_db
class TestImportFile:
    """测试 import_file"""

    def test_no_file_returns_error(self):
        """无文件上传返回错误"""
        client = APIClient()
        resp = client.post('/api/import/upload')
        assert resp.status_code == 400
        assert 'error' in resp.data

    def test_file_upload_success(self, mocker):
        """文件上传成功"""
        # Mock ImportService 避免实际导入逻辑
        mock_service = mocker.patch('apps.imports.views.ImportService')
        mock_instance = mock_service.return_value
        mock_instance.import_file.return_value = {
            'imported_rows': 10,
            'skipped_rows': 2,
            'error_rows': 0,
        }

        csv_content = b'date,amount,description\n2024-01-01,100,test\n'
        file = SimpleUploadedFile('test.csv', csv_content, content_type='text/csv')

        client = APIClient()
        resp = client.post('/api/import/upload', {'file': file}, format='multipart')
        assert resp.status_code == 200
        assert resp.data['imported_rows'] == 10
        assert resp.data['skipped_rows'] == 2

    def test_file_upload_with_source_hint(self, mocker):
        """带 source 提示的文件上传"""
        mock_service = mocker.patch('apps.imports.views.ImportService')
        mock_instance = mock_service.return_value
        mock_instance.import_file.return_value = {'imported_rows': 5}

        csv_content = b'date,amount,description\n2024-01-01,100,test\n'
        file = SimpleUploadedFile('test.csv', csv_content, content_type='text/csv')

        client = APIClient()
        resp = client.post('/api/import/upload', {
            'file': file,
            'source': 'alipay',
        }, format='multipart')
        assert resp.status_code == 200
        mock_instance.import_file.assert_called_once()


@pytest.mark.django_db
class TestImportBatch:
    """测试 import_batch"""

    def test_no_files_returns_error(self):
        """无文件返回错误"""
        client = APIClient()
        resp = client.post('/api/import/batch')
        assert resp.status_code == 400
        assert 'error' in resp.data

    def test_batch_upload(self, mocker):
        """批量上传"""
        mock_service = mocker.patch('apps.imports.views.ImportService')
        mock_instance = mock_service.return_value
        mock_instance.import_file.return_value = {
            'imported_rows': 5,
            'skipped_rows': 1,
            'error_rows': 0,
        }

        csv1 = SimpleUploadedFile('file1.csv', b'a,b,c\n', content_type='text/csv')
        csv2 = SimpleUploadedFile('file2.csv', b'd,e,f\n', content_type='text/csv')

        client = APIClient()
        resp = client.post('/api/import/batch', {'files': [csv1, csv2]}, format='multipart')
        assert resp.status_code == 200
        assert len(resp.data['files']) == 2
        assert resp.data['summary']['total_files'] == 2
        assert resp.data['summary']['total_imported'] == 10


@pytest.mark.django_db
class TestImportHistory:
    """测试 import_history"""

    def test_empty_history(self):
        """空历史"""
        client = APIClient()
        resp = client.get('/api/import/history')
        assert resp.status_code == 200
        assert resp.data == []

    def test_with_history(self):
        """有历史记录"""
        ImportLog.objects.create(
            source='alipay', source_file='test.csv',
            file_size=1024, total_rows=100, imported_rows=90,
            skipped_rows=5, error_rows=5, status='success',
        )
        ImportLog.objects.create(
            source='wechat', source_file='test2.csv',
            file_size=2048, total_rows=50, imported_rows=48,
            skipped_rows=0, error_rows=2, status='partial',
        )

        client = APIClient()
        resp = client.get('/api/import/history')
        assert resp.status_code == 200
        assert len(resp.data) == 2
        # 按 created_at 降序排列，最新的在前
        sources = [r['source'] for r in resp.data]
        assert 'alipay' in sources
        assert 'wechat' in sources
