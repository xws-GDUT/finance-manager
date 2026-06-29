"""
共享工具 — 唯一键生成 + 来源识别
"""
import hashlib
from decimal import Decimal


def generate_unique_key(source: str, trans_date: str, amount: Decimal,
                        merchant: str, description: str) -> str:
    """
    生成交易唯一键（MD5 前 16 位）

    规则：{来源}|{日期}|{金额}|{商户}|{描述前50字}
    用于导入去重
    """
    raw = f"{source}|{trans_date}|{amount}|{merchant}|{description[:50]}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()[:16]


# ── 来源自动识别 ──────────────────────────────────────

SOURCE_FILENAME_PATTERNS = {
    'alipay': ['支付宝', 'alipay', '余额宝'],
    'jd': ['京东', 'jd'],
    'meituan': ['美团', 'meituan'],
    'wechat': ['微信', 'wechat', '零钱'],
    'douyin': ['抖音', 'douyin'],
    'bocom_debit': ['交通银行', '交行', 'bocom'],
    'cib_credit': ['中信', 'cib'],
    'cmb_debit': ['招商银行', '招商储蓄', '招行储蓄'],
    'cmb_credit': ['招商信用卡', '招行信用卡', 'cmb_credit'],
}

# PDF 文件的来源识别（按内容关键词）
PDF_CONTENT_SIGNATURES = {
    'bocom_debit': ['交通银行', '交行', '储蓄卡'],
    'cmb_debit': ['招商银行', '一卡通'],
    'cib_credit': ['中信银行', '信用卡账单'],
    'cmb_credit': ['招商银行信用卡', '个人信用卡账单'],
    'douyin': ['抖音月付', 'DOUYIN'],
}


def detect_source(filename: str) -> str | None:
    """根据文件名自动识别来源，返回 source code 或 None"""
    # 先清理文件名中的时间戳后缀（如 _20260629_123456）
    import re
    clean_name = re.sub(r'[_-]?\d{8}[_-]?\d{6}?', '', filename)
    filename_lower = clean_name.lower()
    for source, patterns in SOURCE_FILENAME_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in filename_lower:
                return source
    # 兜底：用原始文件名再匹配一次
    filename_lower = filename.lower()
    for source, patterns in SOURCE_FILENAME_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in filename_lower:
                return source
    return None
