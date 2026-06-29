"""
多来源流水解析器

支持 9 种数据来源：
- CSV: 支付宝、京东、美团
- XLSX: 微信支付
- PDF: 交通银行储蓄卡、招商银行储蓄卡、中信信用卡、招商银行信用卡、抖音月付

每个解析器返回 list[dict]，每条 dict 包含：
    trans_date, amount, direction, source, trans_type, description,
    merchant, counterparty, payment_method, payment_channel
"""
import re
import csv
import io
from decimal import Decimal
from datetime import datetime
from typing import Any

from utils.helpers import detect_source, generate_unique_key

# ── CSV 解析器 ────────────────────────────────────────


def parse_alipay_csv(content: str) -> list[dict]:
    """
    支付宝 CSV 解析
    表头识别 + 列映射
    典型列：交易时间,交易对方,商品说明,收/支,金额,交易状态,交易类型,备注
    """
    reader = csv.DictReader(io.StringIO(content))
    rows = []

    for row in reader:
        # 清理空行
        if not any(row.values()):
            continue

        # 列名兼容不同支付宝导出版本
        date = row.get('交易时间', '') or row.get('交易日期', '')
        counterparty = row.get('交易对方', '') or row.get('对方', '')
        description = row.get('商品说明', '') or row.get('商品', '')
        direction_raw = row.get('收/支', '') or row.get('收支', '') or row.get('资金流向', '')
        amount_raw = row.get('金额', '') or row.get('交易金额', '')
        trans_type = row.get('交易类型', '') or row.get('类型', '')
        payment_method = row.get('支付方式', '') or row.get('付款方式', '')
        status = row.get('交易状态', '') or row.get('状态', '')

        # 跳过非成功交易
        if status and '成功' not in status and '已付' not in status and '交易成功' not in status:
            continue

        # 解析金额
        try:
            amount = Decimal(abs(float(amount_raw)))
        except (ValueError, TypeError):
            continue

        # 解析方向
        if '支' in direction_raw or '付' in direction_raw:
            direction = 'expense'
        elif '收' in direction_raw:
            direction = 'income'
        else:
            direction = 'expense' if '支出' in trans_type else 'income'

        # 解析日期
        try:
            parsed_date = _parse_date(date)
        except ValueError:
            continue

        rows.append({
            'trans_date': parsed_date,
            'amount': amount,
            'direction': direction,
            'trans_type': trans_type.strip(),
            'description': description.strip(),
            'merchant': counterparty.strip(),
            'counterparty': counterparty.strip(),
            'payment_method': payment_method.strip(),
            'payment_channel': _extract_payment_channel(payment_method, description),
            'source': 'alipay',
        })

    return rows


def parse_jd_csv(content: str) -> list[dict]:
    """
    京东 CSV 解析
    列：交易时间,交易对方,商品说明,收/支,金额,交易状态,备注
    """
    reader = csv.DictReader(io.StringIO(content))
    rows = []

    for row in reader:
        if not any(row.values()):
            continue

        date = row.get('交易时间', '') or row.get('交易日期', '')
        counterparty = row.get('交易对方', '') or row.get('商户名称', '')
        description = row.get('商品说明', '') or row.get('交易说明', '')
        direction_raw = row.get('收/支', '') or row.get('收支', '')
        amount_raw = row.get('金额', '') or row.get('交易金额', '')
        trans_type = row.get('交易类型', '') or row.get('类型', '')
        status = row.get('交易状态', '') or row.get('状态', '')

        if status and '成功' not in status and '完成' not in status:
            continue

        try:
            amount = Decimal(abs(float(amount_raw)))
        except (ValueError, TypeError):
            continue

        direction = 'expense' if '支' in direction_raw else 'income'

        try:
            parsed_date = _parse_date(date)
        except ValueError:
            continue

        rows.append({
            'trans_date': parsed_date,
            'amount': amount,
            'direction': direction,
            'trans_type': trans_type.strip(),
            'description': description.strip(),
            'merchant': counterparty.strip(),
            'counterparty': counterparty.strip(),
            'payment_method': '京东白条',
            'payment_channel': '京东白条',
            'source': 'jd',
        })

    return rows


def parse_meituan_csv(content: str) -> list[dict]:
    """
    美团 CSV 解析
    列：交易时间,交易对方,商品说明,收/支,金额,支付方式,交易状态
    """
    reader = csv.DictReader(io.StringIO(content))
    rows = []

    for row in reader:
        if not any(row.values()):
            continue

        date = row.get('交易时间', '') or row.get('交易日期', '')
        counterparty = row.get('交易对方', '') or row.get('商户', '')
        description = row.get('商品说明', '') or row.get('交易说明', '')
        direction_raw = row.get('收/支', '') or row.get('收支', '')
        amount_raw = row.get('金额', '') or row.get('交易金额', '')
        trans_type = row.get('交易类型', '') or row.get('类型', '')
        payment_method = row.get('支付方式', '') or row.get('付款方式', '')
        status = row.get('交易状态', '') or row.get('状态', '')

        if status and '成功' not in status and '完成' not in status:
            continue

        try:
            amount = Decimal(abs(float(amount_raw)))
        except (ValueError, TypeError):
            continue

        direction = 'expense' if '支' in direction_raw else 'income'

        try:
            parsed_date = _parse_date(date)
        except ValueError:
            continue

        rows.append({
            'trans_date': parsed_date,
            'amount': amount,
            'direction': direction,
            'trans_type': trans_type.strip(),
            'description': description.strip(),
            'merchant': counterparty.strip(),
            'counterparty': counterparty.strip(),
            'payment_method': payment_method.strip() or '美团月付',
            'payment_channel': '美团月付',
            'source': 'meituan',
        })

    return rows


def parse_wechat_xlsx(worksheet) -> list[dict]:
    """
    微信支付 XLSX 解析
    用 openpyxl 读取工作表，表头识别 + 列映射
    典型列：交易时间,交易对方,商品,收/支,金额(元),支付方式,当前状态,交易类型,备注
    """
    rows_data = []

    # 读取所有行
    all_rows = []
    for row in worksheet.iter_rows(values_only=True):
        all_rows.append([str(c) if c is not None else '' for c in row])

    if not all_rows:
        return rows_data

    # 表头识别
    header = all_rows[0]
    col_map = {}
    header_mapping = {
        'date': ['交易时间', '时间', '日期'],
        'counterparty': ['交易对方', '对方', '商户'],
        'description': ['商品', '商品说明', '交易说明'],
        'direction_raw': ['收/支', '收支', '类型'],
        'amount': ['金额', '金额(元)', '交易金额'],
        'payment_method': ['支付方式', '付款方式'],
        'status': ['当前状态', '交易状态', '状态'],
        'trans_type': ['交易类型', '类型'],
    }

    for idx, col_name in enumerate(header):
        col_name_clean = col_name.strip()
        for key, aliases in header_mapping.items():
            if any(a in col_name_clean for a in aliases):
                col_map[key] = idx
                break

    # 解析数据行
    for row in all_rows[1:]:
        if not any(row):
            continue

        def _get(key, default=''):
            idx = col_map.get(key)
            return row[idx].strip() if idx is not None and idx < len(row) else default

        amount_raw = _get('amount')
        direction_raw = _get('direction_raw')
        status = _get('status')
        date = _get('date')

        if status and '支付成功' not in status and '已入账' not in status and '成功' not in status:
            continue

        try:
            amount = Decimal(abs(float(amount_raw.replace(',', ''))))
        except (ValueError, TypeError):
            continue

        if '支出' in direction_raw or '支' in direction_raw:
            direction = 'expense'
        elif '收入' in direction_raw or '收' in direction_raw:
            direction = 'income'
        else:
            direction = 'expense'

        try:
            parsed_date = _parse_date(date)
        except ValueError:
            continue

        rows_data.append({
            'trans_date': parsed_date,
            'amount': amount,
            'direction': direction,
            'trans_type': _get('trans_type'),
            'description': _get('description'),
            'merchant': _get('counterparty'),
            'counterparty': _get('counterparty'),
            'payment_method': _get('payment_method') or '微信支付',
            'payment_channel': '微信支付',
            'source': 'wechat',
        })

    return rows_data


# ── PDF 解析器 ────────────────────────────────────────


def parse_bocom_debit_pdf(pages) -> list[dict]:
    """
    交通银行储蓄卡 PDF 解析
    使用 pdfplumber 表格提取
    """
    rows = []
    for page in pages:
        tables = page.extract_tables()
        for table in tables:
            for row_data in table:
                if not row_data or not any(row_data):
                    continue
                parsed = _parse_bocom_row(row_data)
                if parsed:
                    rows.append(parsed)
    return rows


def _parse_bocom_row(row_data: list) -> dict | None:
    """解析交通银行单行数据"""
    cleaned = [str(c).strip() if c else '' for c in row_data]

    # 跳过头行
    if '交易日期' in cleaned[0] or '记账日期' in cleaned[0]:
        return None

    # 寻找日期列
    date = ''
    amount_raw = ''
    for cell in cleaned:
        if re.match(r'\d{4}[/-]\d{2}[/-]\d{2}', cell):
            date = cell
            break

    if not date:
        return None

    # 寻找金额列
    for cell in cleaned:
        if re.match(r'^[+-]?\d[\d,]*\.?\d*$', cell):
            amount_raw = cell
            break

    if not amount_raw:
        return None

    amount_raw = amount_raw.replace(',', '').replace('+', '')
    try:
        amount = Decimal(abs(float(amount_raw)))
    except ValueError:
        return None

    direction = 'expense' if amount_raw.startswith('-') else 'income'

    # 提取描述（取最长的非金额非日期文本）
    texts = [c for c in cleaned if c and c != date and c != amount_raw]
    description = ' '.join(texts) if texts else ''
    counterparty = texts[0] if texts else ''

    try:
        parsed_date = _parse_date(date)
    except ValueError:
        return None

    return {
        'trans_date': parsed_date,
        'amount': amount,
        'direction': direction,
        'trans_type': _detect_bocom_type(description),
        'description': description,
        'merchant': counterparty,
        'counterparty': counterparty,
        'payment_method': '交通银行储蓄卡',
        'payment_channel': _extract_payment_channel_from_text(description),
        'source': 'bocom_debit',
    }


def _detect_bocom_type(desc: str) -> str:
    if '快捷支付' in desc:
        return '快捷支付'
    if '网上支付' in desc:
        return '网上支付'
    if '银联' in desc:
        return '银联支付'
    if '转账' in desc:
        return '转账汇款'
    if '代发工资' in desc:
        return '代发工资'
    if '还款' in desc:
        return '还款'
    return '其他'


def parse_cmb_debit_pdf(pages) -> list[dict]:
    """
    招商银行储蓄卡 PDF 解析
    使用 pdfplumber 文本 + 正则匹配
    格式：日期 摘要 支出(-) 收入(+) 余额
    """
    rows = []
    text = '\n'.join(page.extract_text() or '' for page in pages)

    # 匹配模式：日期 + 描述 + 金额
    # 招行格式通常是：YYYY-MM-DD  描述内容  -金额  余额
    pattern = re.compile(
        r'(\d{4}[-/]\d{2}[-/]\d{2})\s+(.+?)\s+'
        r'([-]?[\d,]+\.\d{2})\s+[\d,]+\.\d{2}'
    )

    for match in pattern.finditer(text):
        date = match.group(1)
        desc = match.group(2).strip()
        amount_raw = match.group(3).replace(',', '')

        # 跳过余额结转等
        if '余额' in desc or '利息' in desc and '结转' in desc:
            continue

        try:
            amount = Decimal(abs(float(amount_raw)))
        except ValueError:
            continue

        direction = 'expense' if amount_raw.startswith('-') else 'income'

        try:
            parsed_date = _parse_date(date)
        except ValueError:
            continue

        rows.append({
            'trans_date': parsed_date,
            'amount': amount,
            'direction': direction,
            'trans_type': _detect_cmb_type(desc),
            'description': desc,
            'merchant': _extract_merchant_from_desc(desc),
            'counterparty': _extract_counterparty_from_desc(desc),
            'payment_method': '招商银行储蓄卡',
            'payment_channel': _extract_payment_channel_from_text(desc),
            'source': 'cmb_debit',
        })

    return rows


def _detect_cmb_type(desc: str) -> str:
    if '快捷支付' in desc:
        return '快捷支付'
    if '网上支付' in desc:
        return '网上支付'
    if '转账' in desc:
        return '转账汇款'
    if '代发' in desc or '工资' in desc:
        return '代发工资'
    if '还款' in desc:
        return '还款'
    if '银联' in desc:
        return '银联支付'
    if '取款' in desc or 'ATM' in desc:
        return '取款'
    return '其他'


def parse_cib_credit_pdf(pages) -> list[dict]:
    """
    中信信用卡 PDF 解析
    使用 pdfplumber 表格 + 状态机
    典型格式：交易日期 记账日期 交易说明 金额
    """
    rows = []
    in_table = False
    current_month = None

    for page in pages:
        text = page.extract_text() or ''

        # 提取账单月份
        month_match = re.search(r'(\d{4})年(\d{1,2})月', text)
        if month_match:
            current_month = f"{month_match.group(1)}-{int(month_match.group(2)):02d}"

        tables = page.extract_tables()
        for table in tables:
            for row_data in table:
                if not row_data or not any(row_data):
                    continue

                cleaned = [str(c).strip() if c else '' for c in row_data]

                # 跳过表头
                if any('交易日期' in c or '记账日期' in c for c in cleaned):
                    in_table = True
                    continue
                if any('本期应还' in c or '最低还款' in c or '积分' in c for c in cleaned):
                    in_table = False
                    continue

                if not in_table:
                    continue

                parsed = _parse_cib_row(cleaned, current_month)
                if parsed:
                    rows.append(parsed)

    return rows


def _parse_cib_row(cleaned: list, current_month: str) -> dict | None:
    """解析中信信用卡单行"""
    date = ''
    desc = ''
    amount_raw = ''

    for cell in cleaned:
        if re.match(r'\d{1,2}/\d{1,2}', cell) and not date:
            date = cell
        elif re.match(r'[-]?[\d,]+\.\d{2}$', cell):
            amount_raw = cell
        elif cell and not date:
            # 可能是纯日期
            pass

    if not date or not amount_raw:
        return None

    # 组装完整日期
    if '/' in date and len(date.split('/')[0]) <= 2:
        month_day = date.split('/')
        if current_month:
            full_date = f"{current_month}-{int(month_day[0]):02d}-{int(month_day[1]):02d}"
        else:
            full_date = f"2024-{int(month_day[0]):02d}-{int(month_day[1]):02d}"
    else:
        full_date = date

    amount_raw = amount_raw.replace(',', '')
    try:
        amount = Decimal(abs(float(amount_raw)))
    except ValueError:
        return None

    direction = 'expense' if amount_raw.startswith('-') else 'income'

    desc = ' '.join([c for c in cleaned if c and c != date and c != amount_raw])

    try:
        parsed_date = _parse_date(full_date)
    except ValueError:
        return None

    return {
        'trans_date': parsed_date,
        'amount': amount,
        'direction': direction,
        'trans_type': _detect_cib_type(desc),
        'description': desc,
        'merchant': _extract_merchant_from_desc(desc),
        'counterparty': _extract_counterparty_from_desc(desc),
        'payment_method': '中信信用卡',
        'payment_channel': _extract_payment_channel_from_text(desc),
        'source': 'cib_credit',
    }


def _detect_cib_type(desc: str) -> str:
    if '财付通' in desc:
        return '财付通'
    if '支付宝' in desc:
        return '支付宝'
    if '美团' in desc:
        return '美团'
    if '特约' in desc:
        return '特约商户'
    if '还款' in desc:
        return '还款'
    return '消费'


def parse_cmb_credit_pdf(pages) -> list[dict]:
    """
    招商银行信用卡 PDF 解析
    使用 pdfplumber 表格 + 日期推断
    """
    rows = []
    current_statement_year = None
    current_statement_month = None

    for page in pages:
        text = page.extract_text() or ''

        # 提取账单年月
        month_match = re.search(r'账单周期.*?(\d{4})[/-](\d{2})', text)
        if month_match:
            current_statement_year = int(month_match.group(1))
            current_statement_month = int(month_match.group(2))

        tables = page.extract_tables()
        for table in tables:
            for row_data in table:
                if not row_data or not any(row_data):
                    continue

                cleaned = [str(c).strip() if c else '' for c in row_data]
                parsed = _parse_cmb_credit_row(
                    cleaned, current_statement_year, current_statement_month
                )
                if parsed:
                    rows.append(parsed)

    return rows


def _parse_cmb_credit_row(cleaned: list, year: int | None, month: int | None) -> dict | None:
    """解析招行信用卡单行"""
    date = ''
    desc = ''
    amount_raw = ''

    for cell in cleaned:
        # 日期格式：MM/DD 或 M/D
        if re.match(r'\d{1,2}/\d{1,2}$', cell) and not date:
            date = cell
        elif re.match(r'^[-]?[\d,]+\.\d{2}$', cell):
            amount_raw = cell
        elif cell:
            desc += cell + ' '

    if not date or not amount_raw:
        return None

    desc = desc.strip()

    # 组装日期
    parts = date.split('/')
    if year and month:
        full_date = f"{year}-{int(parts[0]):02d}-{int(parts[1]):02d}"
    else:
        full_date = f"2024-{int(parts[0]):02d}-{int(parts[1]):02d}"

    amount_raw = amount_raw.replace(',', '')
    try:
        amount = Decimal(abs(float(amount_raw)))
    except ValueError:
        return None

    direction = 'expense' if amount_raw.startswith('-') else 'income'

    try:
        parsed_date = _parse_date(full_date)
    except ValueError:
        return None

    return {
        'trans_date': parsed_date,
        'amount': amount,
        'direction': direction,
        'trans_type': _detect_cmb_credit_type(desc),
        'description': desc,
        'merchant': _extract_merchant_from_desc(desc),
        'counterparty': _extract_counterparty_from_desc(desc),
        'payment_method': '招商银行信用卡',
        'payment_channel': _extract_payment_channel_from_text(desc),
        'source': 'cmb_credit',
    }


def _detect_cmb_credit_type(desc: str) -> str:
    if '财付通' in desc:
        return '财付通'
    if '支付宝' in desc:
        return '支付宝'
    if '美团' in desc:
        return '美团'
    if '特约' in desc:
        return '特约商户'
    return '消费'


def parse_douyin_pdf(pages) -> list[dict]:
    """
    抖音月付 PDF 解析
    使用 pdfplumber 文本 + 正则
    """
    rows = []
    text = '\n'.join(page.extract_text() or '' for page in pages)

    # 匹配模式：日期 描述 金额
    pattern = re.compile(
        r'(\d{4}[-/]\d{2}[-/]\d{2})\s+(.+?)\s+'
        r'([-]?[\d,]+\.\d{2})'
    )

    for match in pattern.finditer(text):
        date = match.group(1)
        desc = match.group(2).strip()
        amount_raw = match.group(3).replace(',', '')

        try:
            amount = Decimal(abs(float(amount_raw)))
        except ValueError:
            continue

        direction = 'expense' if amount_raw.startswith('-') else 'income'

        try:
            parsed_date = _parse_date(date)
        except ValueError:
            continue

        rows.append({
            'trans_date': parsed_date,
            'amount': amount,
            'direction': direction,
            'trans_type': '抖音月付',
            'description': desc,
            'merchant': _extract_merchant_from_desc(desc),
            'counterparty': '',
            'payment_method': '抖音月付',
            'payment_channel': '抖音月付',
            'source': 'douyin',
        })

    return rows


# ── 统一入口 ──────────────────────────────────────────


PARSER_MAP = {
    'alipay': parse_alipay_csv,
    'jd': parse_jd_csv,
    'meituan': parse_meituan_csv,
    'wechat': None,  # XLSX 需要特殊处理
    'bocom_debit': parse_bocom_debit_pdf,
    'cmb_debit': parse_cmb_debit_pdf,
    'cib_credit': parse_cib_credit_pdf,
    'cmb_credit': parse_cmb_credit_pdf,
    'douyin': parse_douyin_pdf,
}


def parse_file(file_path: str, filename: str,
               source_hint: str | None = None) -> tuple[list[dict], str]:
    """
    统一文件解析入口

    Args:
        file_path: 文件路径
        filename: 原始文件名
        source_hint: 来源提示（优先于自动识别）

    Returns:
        (parsed_rows, detected_source) 解析结果列表和识别到的来源
    """
    # 识别来源
    source = source_hint or detect_source(filename)
    if not source:
        raise ValueError(f'无法识别文件来源: {filename}')

    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''

    # CSV 解析
    if ext == 'csv' and source in ('alipay', 'jd', 'meituan'):
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        parser = PARSER_MAP[source]
        return parser(content), source

    # XLSX 解析（微信支付）
    if ext == 'xlsx' and source == 'wechat':
        import openpyxl
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb.active
        rows = parse_wechat_xlsx(ws)
        wb.close()
        return rows, source

    # PDF 解析
    if ext == 'pdf':
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            pages = pdf.pages
        parser = PARSER_MAP.get(source)
        if not parser:
            raise ValueError(f'不支持的 PDF 来源: {source}')
        return parser(pages), source

    raise ValueError(f'不支持的文件格式: {ext} (来源: {source})')


# ── 辅助函数 ──────────────────────────────────────────


def _parse_date(date_str: str) -> str:
    """统一日期解析，返回 YYYY-MM-DD"""
    date_str = date_str.strip()
    formats = [
        '%Y-%m-%d', '%Y/%m/%d',
        '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S',
        '%Y年%m月%d日',
        '%m/%d/%Y', '%m/%d/%y',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    # 最后尝试：如果是 YYYY-MM-DD HH:MM:SS 格式
    try:
        return datetime.strptime(date_str[:10], '%Y-%m-%d').strftime('%Y-%m-%d')
    except ValueError:
        pass
    raise ValueError(f'无法解析日期: {date_str}')


def _extract_payment_channel(payment_method: str, description: str) -> str:
    """从支付方式中提取支付渠道"""
    text = (payment_method + ' ' + description).lower()
    if '支付宝' in text or 'alipay' in text:
        return '支付宝'
    if '微信' in text or 'wechat' in text:
        return '微信支付'
    if '银行卡' in text or '储蓄卡' in text:
        return '银行卡'
    if '信用卡' in text:
        return '信用卡'
    if '余额' in text:
        return '余额'
    return payment_method.strip()


def _extract_payment_channel_from_text(text: str) -> str:
    """从描述文本中提取支付渠道"""
    t = text.lower()
    if '支付宝' in t or 'alipay' in t:
        return '支付宝'
    if '微信' in t or 'wechat' in t or '财付通' in t:
        return '微信支付'
    if '银联' in t:
        return '银联'
    if '快捷支付' in t:
        return '快捷支付'
    if '网上支付' in t:
        return '网上支付'
    return ''


def _extract_merchant_from_desc(desc: str) -> str:
    """从描述中提取商户名"""
    # 招行格式：商户名-城市
    # 中信格式：(商户名)
    m = re.search(r'^(.+?)[\s-]', desc)
    if m:
        return m.group(1).strip()
    return desc.strip()


def _extract_counterparty_from_desc(desc: str) -> str:
    """从描述中提取对手方"""
    # 常见格式：转账给XXX / 向XXX转账
    m = re.search(r'转账给(\S+)', desc)
    if m:
        return m.group(1)
    m = re.search(r'向(\S+)转账', desc)
    if m:
        return m.group(1)
    return ''
