"""
预置数据迁移 — 分类、账户、有效规则、无效规则

基于需求文档：
- 17 个父分类 + 14 个子分类
- 8 个预置账户
- 11 条有效规则
- 16+ 条无效规则
"""
from django.db import migrations


# ── 预置分类数据 ────────────────────────────────────────

CATEGORIES = [
    # 支出大类
    {'name': '餐饮美食', 'icon': '🍽️', 'type': 'expense', 'sort_order': 1, 'children': [
        {'name': '外卖外食', 'icon': '🥡', 'type': 'expense'},
        {'name': '零食饮料', 'icon': '🥤', 'type': 'expense'},
        {'name': '买菜做饭', 'icon': '🥬', 'type': 'expense'},
    ]},
    {'name': '交通出行', 'icon': '🚗', 'type': 'expense', 'sort_order': 2, 'children': [
        {'name': '公共交通', 'icon': '🚌', 'type': 'expense'},
        {'name': '火车高铁', 'icon': '🚄', 'type': 'expense'},
        {'name': '打车出行', 'icon': '🚕', 'type': 'expense'},
    ]},
    {'name': '购物消费', 'icon': '🛒', 'type': 'expense', 'sort_order': 3, 'children': [
        {'name': '日用百货', 'icon': '📦', 'type': 'expense'},
        {'name': '数码电器', 'icon': '📱', 'type': 'expense'},
        {'name': '服饰美妆', 'icon': '👗', 'type': 'expense'},
    ]},
    {'name': '居住生活', 'icon': '🏠', 'type': 'expense', 'sort_order': 4, 'children': [
        {'name': '水电网费', 'icon': '💡', 'type': 'expense'},
        {'name': '房租物业', 'icon': '🔑', 'type': 'expense'},
    ]},
    {'name': '文化休闲', 'icon': '🎮', 'type': 'expense', 'sort_order': 5, 'children': [
        {'name': '游戏娱乐', 'icon': '🕹️', 'type': 'expense'},
        {'name': '运动健身', 'icon': '⚽', 'type': 'expense'},
    ]},
    {'name': '充值缴费', 'icon': '📱', 'type': 'expense', 'sort_order': 6, 'children': [
        {'name': '话费宽带', 'icon': '📞', 'type': 'expense'},
    ]},
    {'name': '医疗健康', 'icon': '💊', 'type': 'expense', 'sort_order': 7, 'children': []},
    {'name': '人情往来', 'icon': '🎁', 'type': 'expense', 'sort_order': 8, 'children': []},
    {'name': '金融理财', 'icon': '💰', 'type': 'expense', 'sort_order': 9, 'children': []},
    {'name': '其他支出', 'icon': '📌', 'type': 'expense', 'sort_order': 10, 'children': []},
    # 收入大类
    {'name': '工资收入', 'icon': '💼', 'type': 'income', 'sort_order': 11, 'children': []},
    {'name': '投资收益', 'icon': '📈', 'type': 'income', 'sort_order': 12, 'children': []},
    {'name': '退款收入', 'icon': '↩️', 'type': 'income', 'sort_order': 13, 'children': []},
    {'name': '其他收入', 'icon': '📌', 'type': 'income', 'sort_order': 14, 'children': []},
    # 转账大类
    {'name': '转账汇款', 'icon': '🔄', 'type': 'transfer', 'sort_order': 15, 'children': []},
    {'name': '信用还款', 'icon': '💳', 'type': 'transfer', 'sort_order': 16, 'children': []},
    {'name': '投资理财', 'icon': '📊', 'type': 'transfer', 'sort_order': 17, 'children': []},
]

# ── 预置账户数据 ────────────────────────────────────────

ACCOUNTS = [
    {'name': '招商银行储蓄卡', 'account_type': 'debit', 'bank_name': '招商银行',
     'match_keywords': '招商银行,招行,cmb'},
    {'name': '交通银行储蓄卡', 'account_type': 'debit', 'bank_name': '交通银行',
     'match_keywords': '交通银行,交行,bocom'},
    {'name': '中信信用卡', 'account_type': 'credit', 'bank_name': '中信银行',
     'match_keywords': '中信,中信银行,cib'},
    {'name': '招商银行信用卡', 'account_type': 'credit', 'bank_name': '招商银行',
     'match_keywords': '招商信用卡,招行信用卡,cmb_credit'},
    {'name': '支付宝', 'account_type': 'platform', 'bank_name': '',
     'match_keywords': '支付宝,alipay,余额'},
    {'name': '京东白条', 'account_type': 'platform', 'bank_name': '京东',
     'match_keywords': '京东,白条,jd'},
    {'name': '美团月付', 'account_type': 'platform', 'bank_name': '美团',
     'match_keywords': '美团,月付,meituan'},
    {'name': '抖音月付', 'account_type': 'platform', 'bank_name': '抖音',
     'match_keywords': '抖音,月付,douyin'},
]

# ── 预置有效规则数据 ────────────────────────────────────

VALID_RULES = [
    {
        'name': '日常消费-银行储蓄卡', 'priority': 100,
        'sources': 'bocom_debit,cmb_debit', 'directions': 'expense',
        'keywords': '快捷支付,网上支付,银联,转账汇款',
    },
    {
        'name': '信用卡消费', 'priority': 95,
        'sources': 'cib_credit,cmb_credit', 'directions': 'expense',
        'keywords': '财付通,支付宝,特约,美团',
    },
    {
        'name': '支付宝消费', 'priority': 90,
        'sources': 'alipay', 'directions': 'expense',
    },
    {
        'name': '京东消费', 'priority': 85,
        'sources': 'jd', 'directions': 'expense',
    },
    {
        'name': '美团消费', 'priority': 80,
        'sources': 'meituan', 'directions': 'expense',
    },
    {
        'name': '抖音消费', 'priority': 75,
        'sources': 'douyin', 'directions': 'expense',
        'keywords': '抖音月付',
    },
    {
        'name': '微信支付消费', 'priority': 88,
        'sources': 'wechat', 'directions': 'expense',
    },
    {
        'name': '工资收入', 'priority': 100,
        'sources': 'bocom_debit', 'directions': 'income',
        'keywords': '代发工资',
    },
    {
        'name': '汇入及退款收入', 'priority': 90,
        'directions': 'income',
        'keywords': '退税,退款,退票',
    },
    {
        'name': '信用卡还款记录', 'priority': 85,
        'sources': 'cib_credit,cmb_credit', 'directions': 'income',
        'keywords': '还款',
        'is_active': False,  # 已停用
    },
    {
        'name': '消费退款', 'priority': 80,
        'directions': 'income',
        'keywords': '退款,退货,退票',
    },
]

# ── 预置无效规则数据 ────────────────────────────────────

INVALID_RULES = [
    # ── 银行类 ──
    {'name': '银行还款/白条/信贷', 'priority': 90,
     'sources': 'bocom_debit,cmb_debit',
     'keywords': '还款,白条,信贷,贷款,分期,信用卡还款'},
    {'name': '银行理财/证券/利息', 'priority': 90,
     'sources': 'bocom_debit,cmb_debit',
     'keywords': '理财,基金,证券,利息,余额宝,朝朝盈,招盈通'},
    {'name': '云闪付转账', 'priority': 85,
     'sources': 'bocom_debit,cmb_debit',
     'keywords': '云闪付'},
    {'name': '转账给施金变', 'priority': 80,
     'sources': 'bocom_debit,cmb_debit',
     'counterparties': '施金变'},
    {'name': '转账给许万森', 'priority': 80,
     'sources': 'bocom_debit,cmb_debit',
     'counterparties': '许万森'},
    {'name': '转账给洗不完', 'priority': 80,
     'sources': 'bocom_debit,cmb_debit',
     'counterparties': '洗不完'},
    {'name': '招行微信转账', 'priority': 85,
     'sources': 'cmb_debit',
     'keywords': '微信转账'},
    # ── 支付宝类 ──
    {'name': '花呗/借呗/网商贷', 'priority': 90,
     'sources': 'alipay',
     'keywords': '花呗,借呗,网商贷,信用借还,自动还款'},
    {'name': '理财/基金/余额宝', 'priority': 90,
     'sources': 'alipay',
     'keywords': '理财,基金,余额宝,蚂蚁财富,买入,赎回'},
    {'name': '转账/提现', 'priority': 85,
     'sources': 'alipay',
     'keywords': '转账,提现,转入,转出'},
    {'name': '信用借还', 'priority': 85,
     'sources': 'alipay',
     'keywords': '信用借还,借呗还款,花呗还款'},
    # ── 京东类 ──
    {'name': '白条/还款/取现', 'priority': 90,
     'sources': 'jd',
     'keywords': '白条,还款,取现,分期'},
    # ── 美团类 ──
    {'name': '还款/月付', 'priority': 90,
     'sources': 'meituan',
     'keywords': '还款,月付,分期'},
    # ── 微信类 ──
    {'name': '还款/提现', 'priority': 90,
     'sources': 'wechat',
     'keywords': '还款,提现,零钱提现'},
    {'name': '零钱通/理财/基金', 'priority': 90,
     'sources': 'wechat',
     'keywords': '零钱通,理财,基金,买入,赎回'},
    {'name': '红包/亲属卡', 'priority': 85,
     'sources': 'wechat',
     'keywords': '红包,亲属卡,群收款'},
    # ── 汇入排除 ──
    {'name': '汇入排除-内部转账', 'priority': 90,
     'directions': 'income',
     'counterparties': '许万森,何永丰,同花顺'},
]


def create_categories(apps, schema_editor):
    Category = apps.get_model('categories', 'Category')
    for cat_data in CATEGORIES:
        children = cat_data.pop('children', [])
        parent = Category.objects.create(**cat_data)
        for child_data in children:
            child_data['parent'] = parent
            # 子分类继承父分类的 type
            child_data.setdefault('type', cat_data['type'])
            child_data.setdefault('sort_order', 0)
            Category.objects.create(**child_data)


def remove_categories(apps, schema_editor):
    Category = apps.get_model('categories', 'Category')
    Category.objects.all().delete()


def create_accounts(apps, schema_editor):
    Account = apps.get_model('accounts', 'Account')
    for acc_data in ACCOUNTS:
        Account.objects.create(**acc_data)


def remove_accounts(apps, schema_editor):
    Account = apps.get_model('accounts', 'Account')
    Account.objects.all().delete()


def create_valid_rules(apps, schema_editor):
    ValidRule = apps.get_model('rules', 'ValidRule')
    for rule_data in VALID_RULES:
        rule_data.setdefault('is_active', True)
        ValidRule.objects.create(**rule_data)


def remove_valid_rules(apps, schema_editor):
    ValidRule = apps.get_model('rules', 'ValidRule')
    ValidRule.objects.all().delete()


def create_invalid_rules(apps, schema_editor):
    InvalidRule = apps.get_model('rules', 'InvalidRule')
    for rule_data in INVALID_RULES:
        rule_data.setdefault('is_active', True)
        InvalidRule.objects.create(**rule_data)


def remove_invalid_rules(apps, schema_editor):
    InvalidRule = apps.get_model('rules', 'InvalidRule')
    InvalidRule.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0001_initial'),
        ('accounts', '0001_initial'),
        ('rules', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_categories, remove_categories),
        migrations.RunPython(create_accounts, remove_accounts),
        migrations.RunPython(create_valid_rules, remove_valid_rules),
        migrations.RunPython(create_invalid_rules, remove_invalid_rules),
    ]
