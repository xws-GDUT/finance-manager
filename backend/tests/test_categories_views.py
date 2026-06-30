"""
测试 categories.views - 分类列表 API
"""
import pytest
from rest_framework.test import APIClient
from apps.categories.models import Category


@pytest.mark.django_db
class TestCategoryList:
    """测试 category_list 视图"""

    def test_no_parent_categories(self):
        """无父分类：返回空数组"""
        client = APIClient()
        resp = client.get('/api/categories')
        assert resp.status_code == 200
        assert resp.data == []

    def test_parent_without_children(self):
        """有父分类无子分类"""
        Category.objects.create(name='餐饮', type='expense', sort_order=1)
        Category.objects.create(name='交通', type='expense', sort_order=2)

        client = APIClient()
        resp = client.get('/api/categories')
        assert resp.status_code == 200
        assert len(resp.data) == 2
        assert resp.data[0]['name'] == '餐饮'
        assert resp.data[0]['children'] == []
        assert resp.data[1]['name'] == '交通'
        assert resp.data[1]['children'] == []

    def test_parent_with_children(self):
        """有父分类有子分类"""
        parent = Category.objects.create(name='餐饮', type='expense', sort_order=1)
        Category.objects.create(name='早餐', type='expense', parent=parent)
        Category.objects.create(name='午餐', type='expense', parent=parent)

        client = APIClient()
        resp = client.get('/api/categories')
        assert resp.status_code == 200
        assert len(resp.data) == 1
        assert resp.data[0]['name'] == '餐饮'
        assert len(resp.data[0]['children']) == 2
        child_names = [c['name'] for c in resp.data[0]['children']]
        assert '早餐' in child_names
        assert '午餐' in child_names

    def test_inactive_category_not_shown(self):
        """非活跃分类不出现"""
        Category.objects.create(name='餐饮', type='expense', is_active=True)
        Category.objects.create(name='交通', type='expense', is_active=False)

        client = APIClient()
        resp = client.get('/api/categories')
        assert resp.status_code == 200
        assert len(resp.data) == 1
        assert resp.data[0]['name'] == '餐饮'

    def test_inactive_parent_with_active_children(self):
        """非活跃父分类不出现（即使有活跃子分类）"""
        parent = Category.objects.create(name='隐藏分类', type='expense', is_active=False)
        Category.objects.create(name='子分类', type='expense', parent=parent, is_active=True)

        client = APIClient()
        resp = client.get('/api/categories')
        assert resp.status_code == 200
        assert len(resp.data) == 0

    def test_inactive_child_not_in_children(self):
        """非活跃子分类不出现在 children 中"""
        parent = Category.objects.create(name='餐饮', type='expense', is_active=True)
        Category.objects.create(name='活跃子分类', type='expense', parent=parent, is_active=True)
        Category.objects.create(name='禁用子分类', type='expense', parent=parent, is_active=False)

        client = APIClient()
        resp = client.get('/api/categories')
        assert resp.status_code == 200
        assert len(resp.data[0]['children']) == 1
        assert resp.data[0]['children'][0]['name'] == '活跃子分类'
