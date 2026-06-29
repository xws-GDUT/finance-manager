"""
无效规则引擎（黑名单）

核心逻辑：
- 命中任一无效规则 → 交易标记为无效（覆盖有效规则的结果）
- 所有匹配条件为 AND 关系
- 空条件（未设置）视为匹配全部

在有效规则引擎基础上额外支持：
  counterparties  对手方精确匹配
"""
from django.db import transaction as db_transaction


class InvalidRuleEngine:
    """无效规则引擎"""

    def __init__(self, invalid_rule_model, category_model):
        self.InvalidRule = invalid_rule_model
        self.Category = category_model

    def match(self, transaction) -> int | None:
        """
        匹配交易到无效规则

        Returns:
            命中的规则 ID，未命中返回 None
        """
        rules = self.InvalidRule.objects.filter(is_active=True).order_by('-priority')

        for rule in rules:
            if self._match_rule(rule, transaction):
                return rule.id

        return None

    def _match_rule(self, rule, tx) -> bool:
        """检查单条规则是否匹配交易"""
        # 来源
        if rule.sources and not self._match_list(tx.source, rule.sources):
            return False

        # 收支方向
        if rule.directions and not self._match_list(tx.direction, rule.directions):
            return False

        # 交易类型
        if rule.trans_types and not self._match_list_contains(tx.trans_type, rule.trans_types):
            return False

        # 分类
        if rule.categories and tx.category:
            cat_name = tx.category.name
            if not self._match_list_contains(cat_name, rule.categories):
                return False

        # 支付渠道
        if rule.payment_channels and not self._match_list_contains(
            tx.payment_channel, rule.payment_channels
        ):
            return False

        # 关键词
        if rule.keywords:
            search_text = f"{tx.description} {tx.merchant} {tx.counterparty} {tx.trans_type} {tx.payment_channel}"
            if not self._match_list_contains(search_text, rule.keywords):
                return False

        # 排除关键词
        if rule.keyword_exclude:
            search_text = f"{tx.description} {tx.merchant} {tx.counterparty} {tx.trans_type}"
            if self._match_list_contains(search_text, rule.keyword_exclude):
                return False

        # 商户
        if rule.merchants and not self._match_list_contains(tx.merchant, rule.merchants):
            return False

        # 对手方（精确匹配，无效规则特有）
        if rule.counterparties and not self._match_list(tx.counterparty, rule.counterparties):
            return False

        # 金额范围
        if rule.amount_min is not None and tx.amount < rule.amount_min:
            return False
        if rule.amount_max is not None and tx.amount > rule.amount_max:
            return False

        return True

    @staticmethod
    def _match_list(value: str, rule_field: str) -> bool:
        if not value:
            return False
        values = [v.strip() for v in rule_field.split(',') if v.strip()]
        return value in values

    @staticmethod
    def _match_list_contains(value: str, rule_field: str) -> bool:
        if not value:
            return False
        values = [v.strip() for v in rule_field.split(',') if v.strip()]
        return any(v in value for v in values)

    def apply_all(self):
        """
        重新应用所有无效规则到所有非删除交易
        返回 (matched_count, total_count)
        """
        from apps.transactions.models import Transaction

        total = 0
        matched = 0

        with db_transaction.atomic():
            txs = Transaction.objects.exclude(status='deleted').select_related('category')

            for tx in txs:
                total += 1
                rule_id = self.match(tx)

                if rule_id is not None:
                    if tx.invalid_rule_id != rule_id:
                        tx.invalid_rule_id = rule_id
                        tx.status = 'excluded'
                        tx.save(update_fields=['invalid_rule_id', 'status'])
                        matched += 1
                elif tx.invalid_rule_id is not None:
                    tx.invalid_rule_id = None
                    tx.save(update_fields=['invalid_rule_id'])

        # 更新命中计数
        self.InvalidRule.objects.all().update(hit_count=0)
        from django.db.models import Count
        stats = (
            Transaction.objects
            .exclude(status='deleted')
            .filter(invalid_rule__isnull=False)
            .values('invalid_rule')
            .annotate(cnt=Count('id'))
        )
        for item in stats:
            self.InvalidRule.objects.filter(id=item['invalid_rule']).update(hit_count=item['cnt'])

        return matched, total

    def test_rule(self, rule_data: dict) -> int:
        """测试规则匹配多少交易"""
        from apps.transactions.models import Transaction

        txs = Transaction.objects.exclude(status='deleted').select_related('category')
        count = 0

        for tx in txs:
            if self._test_match(rule_data, tx):
                count += 1

        return count

    def _test_match(self, rule_data: dict, tx) -> bool:
        if rule_data.get('sources') and not self._match_list(tx.source, rule_data['sources']):
            return False
        if rule_data.get('directions') and not self._match_list(tx.direction, rule_data['directions']):
            return False
        if rule_data.get('trans_types') and not self._match_list_contains(tx.trans_type, rule_data['trans_types']):
            return False
        if rule_data.get('categories') and tx.category:
            if not self._match_list_contains(tx.category.name, rule_data['categories']):
                return False
        if rule_data.get('payment_channels') and not self._match_list_contains(tx.payment_channel, rule_data['payment_channels']):
            return False
        if rule_data.get('keywords'):
            search_text = f"{tx.description} {tx.merchant} {tx.counterparty} {tx.trans_type} {tx.payment_channel}"
            if not self._match_list_contains(search_text, rule_data['keywords']):
                return False
        if rule_data.get('keyword_exclude'):
            search_text = f"{tx.description} {tx.merchant} {tx.counterparty} {tx.trans_type}"
            if self._match_list_contains(search_text, rule_data['keyword_exclude']):
                return False
        if rule_data.get('merchants') and not self._match_list_contains(tx.merchant, rule_data['merchants']):
            return False
        if rule_data.get('counterparties') and not self._match_list(tx.counterparty, rule_data['counterparties']):
            return False
        if rule_data.get('amount_min') is not None and tx.amount < rule_data['amount_min']:
            return False
        if rule_data.get('amount_max') is not None and tx.amount > rule_data['amount_max']:
            return False
        return True
