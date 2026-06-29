"""
智能分类器 — 基于关键词自动归类到预置分类体系

匹配优先级：
1. 交易类型关键词匹配 → 直接分类
2. 商户名关键词匹配 → 子分类
3. 描述关键词匹配 → 大类
4. 默认分类（其他支出/其他收入）
"""
from typing import Optional


# ── 关键词 → 分类映射 ─────────────────────────────────

# 格式：(分类名, [关键词列表], 类型)
# 子分类名需与预置数据中的子分类名完全匹配
# 匹配范围：description + merchant + trans_type

CATEGORY_KEYWORDS = [
    # ── 餐饮美食 ──
    ('外卖外食', ['外卖', '饿了么', '美团外卖', '大众点评', '点评', '星巴克',
                  '麦当劳', '肯德基', '汉堡王', '必胜客', '海底捞', '奶茶',
                  '咖啡', '瑞幸', 'luckin', '茶百道', '喜茶', '奈雪', '蜜雪冰城']),
    ('零食饮料', ['零食', '饮料', '超市', '便利店', '罗森', '全家', '711',
                  '7-eleven', '好特卖', '零食很忙', '盒马']),
    ('买菜做饭', ['菜市场', '买菜', '生鲜', '叮咚', '朴朴', '每日优鲜',
                  '多多买菜', '美团优选', '淘菜菜']),

    # ── 交通出行 ──
    ('公共交通', ['地铁', '公交', '巴士', '公共汽车', '交通卡', '乘车码',
                  '云闪付-乘车', '一卡通']),
    ('火车高铁', ['火车', '高铁', '动车', '12306', '中国铁路']),
    ('打车出行', ['打车', '滴滴', '花小猪', '曹操出行', 'T3出行', '高德打车',
                  '出租车', '顺风车', '哈啰']),

    # ── 购物消费 ──
    ('日用百货', ['淘宝', '天猫', '拼多多', '京东', '超市', '百货', '日用品',
                  '清洁', '洗衣', '纸巾', '家居', '宜家', '名创优品']),
    ('数码电器', ['数码', '电器', '手机', '电脑', '笔记本', '耳机', '充电',
                  '小米', '华为', '苹果', '大疆', '机械革命', '联想',
                  'steam', '任天堂', 'PS5', 'Xbox']),
    ('服饰美妆', ['服饰', '美妆', '衣服', '鞋', '包', '化妆品', '护肤',
                  '优衣库', 'ZARA', 'HM', 'Nike', 'Adidas', '李宁']),

    # ── 居住生活 ──
    ('水电网费', ['水费', '电费', '燃气', '煤气', '暖气', '网络', '宽带',
                  '话费', '手机费', '通信', '物业费']),
    ('房租物业', ['房租', '租金', '房费', '物业', '维修', '装修']),

    # ── 文化休闲 ──
    ('游戏娱乐', ['游戏', '娱乐', '视频', '会员', '音乐', '电影', 'KTV',
                  'B站', 'bilibili', '优酷', '爱奇艺', '腾讯视频', '网易云',
                  'QQ音乐', '抖音', '快手', 'Steam', '王者', '原神',
                  'Netflix', 'Spotify', 'Disney']),
    ('运动健身', ['运动', '健身', '游泳', '跑步', '瑜伽', '篮球', '足球',
                  'Keep', '乐刻', '超级猩猩', '威尔士']),

    # ── 充值缴费 ──
    ('话费宽带', ['话费', '充值', '宽带', '手机', '联通', '移动', '电信']),

    # ── 医疗健康 ──
    ('医疗健康', ['医院', '诊所', '药', '体检', '门诊', '挂号', '医保',
                  '医疗', '健康', '牙科', '眼科', '心理']),

    # ── 人情往来 ──
    ('人情往来', ['红包', '份子钱', '礼物', '赠礼', '请客', '聚会']),

    # ── 金融理财 ──
    ('金融理财', ['理财', '基金', '股票', '证券', '保险', '贷款', '利息']),

    # ── 工资收入 ──
    ('工资收入', ['工资', '代发工资', '薪资', '薪酬', '奖金', '绩效', '报销']),

    # ── 投资收益 ──
    ('投资收益', ['投资收益', '分红', '利息收入', '理财收益', '基金赎回']),

    # ── 退款收入 ──
    ('退款收入', ['退款', '退货', '退票', '退差价', '撤销', '冲正', '返还',
                  '退订', '退费', '退换', '原路退回']),
]

# 大类直接匹配（无子分类的分类）
PARENT_ONLY_CATEGORIES = {'医疗健康', '人情往来', '金融理财', '工资收入',
                          '投资收益', '退款收入', '其他支出', '其他收入',
                          '转账汇款', '信用还款', '投资理财'}


class SmartCategorizer:
    """智能分类器"""

    def __init__(self, category_model):
        """
        Args:
            category_model: Django Category 模型类
        """
        self.Category = category_model
        self._load_categories()

    def _load_categories(self):
        """加载所有分类到内存，建立名称到 ID 的映射"""
        cats = self.Category.objects.filter(is_active=True).select_related('parent')
        self._name_to_id = {}
        self._id_to_obj = {}
        for c in cats:
            self._name_to_id[c.name] = c.id
            self._id_to_obj[c.id] = c

    def classify(self, description: str, merchant: str, trans_type: str,
                 direction: str = 'expense') -> Optional[int]:
        """
        自动分类

        Args:
            description: 交易描述
            merchant: 商户名
            trans_type: 交易类型
            direction: 收支方向

        Returns:
            匹配到的分类 ID，未匹配返回 None
        """
        search_text = f"{description} {merchant} {trans_type}"

        # 1. 按关键词匹配
        for category_name, keywords in CATEGORY_KEYWORDS:
            for kw in keywords:
                if kw.lower() in search_text.lower():
                    return self._name_to_id.get(category_name)

        # 2. 默认分类
        if direction == 'expense':
            return self._name_to_id.get('其他支出')
        elif direction == 'income':
            return self._name_to_id.get('其他收入')
        return None

    def get_category_name(self, category_id: int) -> str:
        """根据 ID 获取分类名"""
        obj = self._id_to_obj.get(category_id)
        return obj.name if obj else '未知'

    def get_parent_name(self, category_id: int) -> str | None:
        """获取父分类名"""
        obj = self._id_to_obj.get(category_id)
        if obj and obj.parent:
            return obj.parent.name
        return None
