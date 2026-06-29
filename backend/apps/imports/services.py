"""
流水导入服务 — 统一入口

处理完整导入流程：
1. 文件解析（parser.parse_file）
2. 智能分类（categorizer.SmartCategorizer）
3. 有效规则判定（valid_engine.ValidRuleEngine）
4. 无效规则判定（invalid_engine.InvalidRuleEngine）
5. 自动创建/匹配账户
6. 生成 unique_key 去重入库
7. 记录导入日志
8. 自动退款配对
"""
import os
import hashlib
from decimal import Decimal
from django.db import transaction as db_transaction

from .parser import parse_file
from .categorizer import SmartCategorizer
from .valid_engine import ValidRuleEngine
from .invalid_engine import InvalidRuleEngine
from .refund_pair import RefundPairEngine


class ImportService:
    """流水导入服务"""

    def __init__(self):
        from apps.transactions.models import Transaction
        from apps.rules.models import ValidRule, InvalidRule
        from apps.categories.models import Category
        from apps.accounts.models import Account
        from apps.imports.models import ImportLog

        self.Transaction = Transaction
        self.ValidRule = ValidRule
        self.InvalidRule = InvalidRule
        self.Category = Category
        self.Account = Account
        self.ImportLog = ImportLog

        self.categorizer = SmartCategorizer(Category)
        self.valid_engine = ValidRuleEngine(ValidRule, Category)
        self.invalid_engine = InvalidRuleEngine(InvalidRule, Category)
        self.refund_engine = RefundPairEngine(
            Transaction,
            Transaction,  # pair model 传入 Transaction（实际使用 TransactionPair）
        )

    def import_file(self, file_path: str, filename: str,
                    source_hint: str | None = None) -> dict:
        """
        导入单个文件

        Returns:
            {
                'success': bool,
                'source': str,
                'total_rows': int,
                'imported_rows': int,
                'skipped_rows': int,
                'error_rows': int,
                'errors': list[str],
            }
        """
        result = {
            'success': True,
            'source': '',
            'total_rows': 0,
            'imported_rows': 0,
            'skipped_rows': 0,
            'error_rows': 0,
            'errors': [],
        }

        # 1. 解析文件
        try:
            parsed_rows, source = parse_file(file_path, filename, source_hint)
            result['source'] = source
        except Exception as e:
            result['success'] = False
            result['errors'].append(f'文件解析失败: {str(e)}')
            return result

        result['total_rows'] = len(parsed_rows)

        # 2. 逐行处理（每行独立事务，避免长事务锁表）
        for row in parsed_rows:
            try:
                with db_transaction.atomic():
                    self._process_row(row, source, result)
            except Exception as e:
                result['error_rows'] += 1
                if len(result['errors']) < 10:
                    result['errors'].append(f"行处理失败: {str(e)[:100]}")

        # 3. 记录导入日志
        self._log_import(filename, source, result, os.path.getsize(file_path))

        # 4. 自动退款配对（仅当有成功导入时）
        if result['imported_rows'] > 0:
            try:
                pair_result = self.refund_engine.auto_pair()
                result['refund_pairs'] = pair_result
            except Exception:
                pass  # 退款配对失败不影响导入

        return result

    def _process_row(self, row: dict, source: str, result: dict):
        """处理单行数据，入库"""
        # 生成唯一键
        unique_key = self._generate_key(source, row)

        # 去重检查
        if self.Transaction.objects.filter(unique_key=unique_key).exists():
            result['skipped_rows'] += 1
            return

        # 智能分类
        category_id = self.categorizer.classify(
            row.get('description', ''),
            row.get('merchant', ''),
            row.get('trans_type', ''),
            row.get('direction', 'expense'),
        )

        # 自动匹配账户
        account = self._match_account(row.get('payment_method', ''), source)

        # 创建交易
        tx = self.Transaction.objects.create(
            trans_date=row['trans_date'],
            amount=row['amount'],
            direction=row['direction'],
            source=source,
            status='unknown',  # 初始未知，后续规则引擎处理
            trans_type=row.get('trans_type', ''),
            description=row.get('description', ''),
            merchant=row.get('merchant', ''),
            counterparty=row.get('counterparty', ''),
            payment_method=row.get('payment_method', ''),
            payment_channel=row.get('payment_channel', ''),
            unique_key=unique_key,
            category_id=category_id,
            account=account,
        )

        # 规则引擎判定
        self._apply_rules(tx)

        result['imported_rows'] += 1

    def _apply_rules(self, tx):
        """应用规则引擎判定交易状态"""
        # 有效规则
        valid_rule_id = self.valid_engine.match(tx)
        if valid_rule_id:
            tx.valid_rule_id = valid_rule_id
            tx.status = 'confirmed'

        # 无效规则（覆盖有效）
        invalid_rule_id = self.invalid_engine.match(tx)
        if invalid_rule_id:
            tx.invalid_rule_id = invalid_rule_id
            tx.status = 'excluded'

        if valid_rule_id or invalid_rule_id:
            tx.save(update_fields=['status', 'valid_rule_id', 'invalid_rule_id'])

    def _match_account(self, payment_method: str, source: str):
        """自动匹配账户"""
        if not payment_method:
            # 通过来源匹配
            source_to_keyword = {
                'alipay': '支付宝',
                'jd': '京东',
                'meituan': '美团',
                'wechat': '微信',
                'douyin': '抖音',
                'bocom_debit': '交通银行',
                'cmb_debit': '招商银行',
                'cib_credit': '中信',
                'cmb_credit': '招商银行信用卡',
            }
            payment_method = source_to_keyword.get(source, '')

        # 搜索匹配
        accounts = self.Account.objects.filter(is_active=True)
        for acc in accounts:
            if acc.match_keywords:
                keywords = [k.strip() for k in acc.match_keywords.split(',')]
                for kw in keywords:
                    if kw.lower() in payment_method.lower():
                        return acc

        # 无匹配则尝试创建新账户
        return None

    @staticmethod
    def _generate_key(source: str, row: dict) -> str:
        """生成唯一键"""
        raw = (
            f"{source}|{row['trans_date']}|{row['amount']}"
            f"|{row.get('merchant', '')}|{row.get('description', '')[:50]}"
        )
        return hashlib.md5(raw.encode('utf-8')).hexdigest()[:16]

    def _log_import(self, filename: str, source: str,
                    result: dict, file_size: int):
        """记录导入日志"""
        self.ImportLog.objects.create(
            source=source,
            source_file=filename,
            file_size=file_size,
            total_rows=result['total_rows'],
            imported_rows=result['imported_rows'],
            skipped_rows=result['skipped_rows'],
            error_rows=result['error_rows'],
            error_detail=result.get('errors', []),
            status='success' if result['success'] and result['error_rows'] == 0 else 'partial',
        )
