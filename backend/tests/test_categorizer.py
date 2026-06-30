"""
测试 SmartCategorizer 智能分类器
"""
import pytest
from unittest.mock import MagicMock, patch
from apps.imports.categorizer import SmartCategorizer, CATEGORY_KEYWORDS, PARENT_ONLY_CATEGORIES


class TestSmartCategorizer:

    @pytest.fixture
    def mock_category_model(self):
        """创建一个mock的Category模型类"""
        model = MagicMock()
        return model

    @pytest.fixture
    def categorizer(self, mock_category_model):
        """创建一个加载了分类数据的 SmartCategorizer 实例"""
        # 创建mock分类对象
        cat_外卖外食 = MagicMock()
        cat_外卖外食.id = 1
        cat_外卖外食.name = '外卖外食'
        cat_外卖外食.parent = MagicMock()
        cat_外卖外食.parent.name = '餐饮美食'

        cat_零食饮料 = MagicMock()
        cat_零食饮料.id = 2
        cat_零食饮料.name = '零食饮料'
        cat_零食饮料.parent = MagicMock()
        cat_零食饮料.parent.name = '餐饮美食'

        cat_公共交通 = MagicMock()
        cat_公共交通.id = 3
        cat_公共交通.name = '公共交通'
        cat_公共交通.parent = MagicMock()
        cat_公共交通.parent.name = '交通出行'

        cat_工资收入 = MagicMock()
        cat_工资收入.id = 10
        cat_工资收入.name = '工资收入'
        cat_工资收入.parent = None

        cat_退款收入 = MagicMock()
        cat_退款收入.id = 11
        cat_退款收入.name = '退款收入'
        cat_退款收入.parent = None

        cat_其他支出 = MagicMock()
        cat_其他支出.id = 99
        cat_其他支出.name = '其他支出'
        cat_其他支出.parent = None

        cat_其他收入 = MagicMock()
        cat_其他收入.id = 100
        cat_其他收入.name = '其他收入'
        cat_其他收入.parent = None

        all_cats = [cat_外卖外食, cat_零食饮料, cat_公共交通, cat_工资收入,
                    cat_退款收入, cat_其他支出, cat_其他收入]

        mock_category_model.objects.filter.return_value.select_related.return_value = all_cats

        categorizer = SmartCategorizer(mock_category_model)
        return categorizer

    # ── _load_categories ──────────────────────────────

    def test_load_categories_builds_mappings(self, categorizer):
        """测试加载分类后正确建立名称到ID和ID到对象的映射"""
        assert len(categorizer._name_to_id) == 7
        assert categorizer._name_to_id['外卖外食'] == 1
        assert categorizer._name_to_id['其他支出'] == 99
        assert categorizer._id_to_obj[1].name == '外卖外食'
        assert categorizer._id_to_obj[100].name == '其他收入'

    # ── classify: 关键词匹配 ─────────────────────────

    def test_classify_match_外卖(self, categorizer):
        """测试匹配'外卖'关键词"""
        result = categorizer.classify('美团外卖', '美团', '餐饮')
        assert result == 1  # 外卖外食

    def test_classify_match_星巴克(self, categorizer):
        """测试匹配'星巴克'关键词"""
        result = categorizer.classify('星巴克', '星巴克', '餐饮')
        assert result == 1

    def test_classify_match_奶茶(self, categorizer):
        """测试匹配'奶茶'关键词"""
        result = categorizer.classify('奶茶', '喜茶', '餐饮')
        assert result == 1

    def test_classify_match_地铁(self, categorizer):
        """测试匹配'地铁'关键词 → 公共交通"""
        result = categorizer.classify('地铁', '地铁', '交通')
        assert result == 3

    def test_classify_match_工资(self, categorizer):
        """测试匹配'工资'关键词 → 工资收入"""
        result = categorizer.classify('工资', '公司', '代发')
        assert result == 10

    def test_classify_match_退款(self, categorizer):
        """测试匹配'退款'关键词 → 退款收入"""
        # 注意：'淘宝'在'日用百货'分类中，为避免先匹配，用不存在的商户
        result = categorizer.classify('退款', '某商户', '退款')
        assert result == 11

    def test_classify_case_insensitive(self, categorizer):
        """测试大小写不敏感匹配"""
        # 'luckin' 应该匹配 '瑞幸'
        result = categorizer.classify('LUCKIN', 'luckin', '餐饮')
        assert result == 1

    def test_classify_match_in_merchant(self, categorizer):
        """测试在商户名中匹配到关键词"""
        result = categorizer.classify('午餐', '海底捞火锅', '餐饮')
        assert result == 1

    def test_classify_match_in_trans_type(self, categorizer):
        """测试在交易类型中匹配到关键词"""
        result = categorizer.classify('', '', '外卖订单')
        assert result == 1

    def test_classify_first_match_wins(self, categorizer):
        """测试首次匹配即返回（优先级）"""
        # '超市' 同时匹配 '零食饮料' 和 '日用百货'
        # 由于 CATEGORY_KEYWORDS 中 '零食饮料' 排在 '日用百货' 前面
        result = categorizer.classify('超市', '超市', '')
        assert result == 2  # 零食饮料

    # ── classify: 方向过滤（默认分类） ──────────────

    def test_classify_no_match_expense_defaults_to_其他支出(self, categorizer):
        """测试无匹配时支出方向默认返回'其他支出'"""
        result = categorizer.classify('xyz', 'xyz', 'unknown', direction='expense')
        assert result == 99

    def test_classify_no_match_income_defaults_to_其他收入(self, categorizer):
        """测试无匹配时收入方向默认返回'其他收入'"""
        result = categorizer.classify('xyz', 'xyz', 'unknown', direction='income')
        assert result == 100

    def test_classify_default_direction_is_expense(self, categorizer):
        """测试默认方向为expense"""
        result = categorizer.classify('xyz', 'xyz', 'unknown')
        assert result == 99

    # ── classify: 无匹配且无默认分类 ─────────────────

    def test_classify_no_match_and_no_default_returns_none(self, categorizer):
        """测试无匹配且默认分类不存在时返回None"""
        # 创建一个没有'其他支出'和'其他收入'的 categorizer
        mock_model = MagicMock()
        # 只加载一个分类
        cat = MagicMock()
        cat.id = 1
        cat.name = '测试分类'
        cat.parent = None
        mock_model.objects.filter.return_value.select_related.return_value = [cat]

        cat2 = SmartCategorizer(mock_model)
        result = cat2.classify('xyz', 'xyz', 'unknown', direction='expense')
        assert result is None

    # ── classify: 空输入 ─────────────────────────────

    def test_classify_empty_inputs(self, categorizer):
        """测试空输入"""
        result = categorizer.classify('', '', '', direction='expense')
        assert result == 99  # 默认其他支出

    def test_classify_empty_inputs_income(self, categorizer):
        """测试空输入收入方向"""
        result = categorizer.classify('', '', '', direction='income')
        assert result == 100  # 默认其他收入

    # ── get_category_name ────────────────────────────

    def test_get_category_name_exists(self, categorizer):
        """测试获取存在的分类名"""
        assert categorizer.get_category_name(1) == '外卖外食'

    def test_get_category_name_not_exists(self, categorizer):
        """测试获取不存在的分类名"""
        assert categorizer.get_category_name(999) == '未知'

    def test_get_category_name_none(self, categorizer):
        """测试传入None"""
        assert categorizer.get_category_name(None) == '未知'

    # ── get_parent_name ──────────────────────────────

    def test_get_parent_name_with_parent(self, categorizer):
        """测试有父分类时返回父分类名"""
        assert categorizer.get_parent_name(1) == '餐饮美食'

    def test_get_parent_name_without_parent(self, categorizer):
        """测试无父分类时返回None"""
        assert categorizer.get_parent_name(10) is None

    def test_get_parent_name_not_exists(self, categorizer):
        """测试分类不存在时返回None"""
        assert categorizer.get_parent_name(999) is None


class TestCategoryKeywordsData:
    """测试 CATEGORY_KEYWORDS 常量数据"""

    def test_all_entries_are_tuples(self):
        """测试所有条目都是(name, keywords)元组"""
        for entry in CATEGORY_KEYWORDS:
            assert isinstance(entry, tuple)
            assert len(entry) == 2
            assert isinstance(entry[0], str)
            assert isinstance(entry[1], list)

    def test_keywords_are_non_empty(self):
        """测试每个分类至少有一个关键词"""
        for name, keywords in CATEGORY_KEYWORDS:
            assert len(keywords) > 0, f'{name} 没有关键词'

    def test_no_duplicate_category_names(self):
        """测试分类名无重复"""
        names = [entry[0] for entry in CATEGORY_KEYWORDS]
        assert len(names) == len(set(names))


class TestParentOnlyCategories:
    """测试 PARENT_ONLY_CATEGORIES 常量"""

    def test_contains_expected_categories(self):
        """测试包含预期的大类"""
        expected = {'医疗健康', '人情往来', '金融理财', '工资收入',
                    '投资收益', '退款收入', '其他支出', '其他收入',
                    '转账汇款', '信用还款', '投资理财'}
        assert PARENT_ONLY_CATEGORIES == expected
