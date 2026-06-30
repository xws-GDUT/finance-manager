"""
测试 rules.views - ValidRuleViewSet 和 InvalidRuleViewSet
"""
import pytest
from rest_framework.test import APIClient
from apps.rules.models import ValidRule, InvalidRule


@pytest.mark.django_db
class TestValidRuleViewSet:
    """测试 ValidRule CRUD"""

    def test_list(self):
        """列表"""
        ValidRule.objects.create(name='规则1', priority=100)
        ValidRule.objects.create(name='规则2', priority=50, is_active=False)

        client = APIClient()
        resp = client.get('/api/valid-rules/')
        assert resp.status_code == 200
        # DRF router 返回 list
        assert isinstance(resp.data, list) or 'results' in resp.data

    def test_create(self):
        """创建"""
        client = APIClient()
        data = {
            'name': '新规则',
            'priority': 80,
            'sources': 'alipay',
            'directions': 'expense',
            'keywords': '测试',
            'is_active': True,
        }
        resp = client.post('/api/valid-rules/', data, format='json')
        assert resp.status_code == 201
        assert resp.data['name'] == '新规则'
        assert ValidRule.objects.filter(name='新规则').exists()

    def test_retrieve(self):
        """获取单个"""
        rule = ValidRule.objects.create(name='规则', priority=50)

        client = APIClient()
        resp = client.get(f'/api/valid-rules/{rule.id}/')
        assert resp.status_code == 200
        assert resp.data['name'] == '规则'

    def test_update(self):
        """全量更新"""
        rule = ValidRule.objects.create(name='旧名称', priority=50)

        client = APIClient()
        data = {
            'name': '新名称',
            'priority': 90,
            'sources': '',
            'trans_types': '',
            'directions': '',
            'categories': '',
            'payment_channels': '',
            'keywords': '',
            'keyword_exclude': '',
            'merchants': '',
            'amount_min': None,
            'amount_max': None,
            'is_active': True,
        }
        resp = client.put(f'/api/valid-rules/{rule.id}/', data, format='json')
        assert resp.status_code == 200
        assert resp.data['name'] == '新名称'

    def test_partial_update(self):
        """部分更新"""
        rule = ValidRule.objects.create(name='规则', priority=50)

        client = APIClient()
        resp = client.patch(f'/api/valid-rules/{rule.id}/', {'priority': 99}, format='json')
        assert resp.status_code == 200
        assert resp.data['priority'] == 99

    def test_destroy(self):
        """删除"""
        rule = ValidRule.objects.create(name='规则', priority=50)

        client = APIClient()
        resp = client.delete(f'/api/valid-rules/{rule.id}/')
        assert resp.status_code == 204
        assert not ValidRule.objects.filter(id=rule.id).exists()

    def test_create_defaults(self):
        """创建默认规则"""
        client = APIClient()
        resp = client.post('/api/valid-rules/create_defaults/')
        assert resp.status_code == 200
        assert resp.data['created'] > 0
        assert ValidRule.objects.count() == resp.data['created']

    def test_create_defaults_idempotent(self):
        """创建默认规则幂等性"""
        client = APIClient()
        # 第一次
        resp1 = client.post('/api/valid-rules/create_defaults/')
        created1 = resp1.data['created']
        # 第二次
        resp2 = client.post('/api/valid-rules/create_defaults/')
        assert resp2.data['created'] == 0
        assert resp2.data['skipped'] == created1


@pytest.mark.django_db
class TestInvalidRuleViewSet:
    """测试 InvalidRule CRUD"""

    def test_list(self):
        """列表"""
        InvalidRule.objects.create(name='无效规则1', priority=100)

        client = APIClient()
        resp = client.get('/api/invalid-rules/')
        assert resp.status_code == 200

    def test_create(self):
        """创建"""
        client = APIClient()
        data = {
            'name': '新无效规则',
            'priority': 80,
            'sources': 'alipay',
            'keywords': '测试',
            'counterparties': '张三',
            'is_active': True,
        }
        resp = client.post('/api/invalid-rules/', data, format='json')
        assert resp.status_code == 201
        assert InvalidRule.objects.filter(name='新无效规则').exists()

    def test_retrieve(self):
        """获取单个"""
        rule = InvalidRule.objects.create(name='规则', priority=50)

        client = APIClient()
        resp = client.get(f'/api/invalid-rules/{rule.id}/')
        assert resp.status_code == 200

    def test_update(self):
        """全量更新"""
        rule = InvalidRule.objects.create(name='旧名称', priority=50)

        client = APIClient()
        data = {
            'name': '新名称',
            'priority': 90,
            'sources': '',
            'trans_types': '',
            'directions': '',
            'categories': '',
            'payment_channels': '',
            'keywords': '',
            'keyword_exclude': '',
            'merchants': '',
            'counterparties': '',
            'amount_min': None,
            'amount_max': None,
            'is_active': True,
        }
        resp = client.put(f'/api/invalid-rules/{rule.id}/', data, format='json')
        assert resp.status_code == 200

    def test_destroy(self):
        """删除"""
        rule = InvalidRule.objects.create(name='规则', priority=50)

        client = APIClient()
        resp = client.delete(f'/api/invalid-rules/{rule.id}/')
        assert resp.status_code == 204

    def test_create_defaults(self):
        """创建默认规则"""
        client = APIClient()
        resp = client.post('/api/invalid-rules/create_defaults/')
        assert resp.status_code == 200
        assert resp.data['created'] > 0
        assert InvalidRule.objects.count() == resp.data['created']

    def test_create_defaults_idempotent(self):
        """创建默认规则幂等性"""
        client = APIClient()
        resp1 = client.post('/api/invalid-rules/create_defaults/')
        created1 = resp1.data['created']
        resp2 = client.post('/api/invalid-rules/create_defaults/')
        assert resp2.data['created'] == 0
        assert resp2.data['skipped'] == created1
