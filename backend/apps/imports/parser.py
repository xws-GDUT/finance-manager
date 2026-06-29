"""
多来源流水解析器 — 适配真实导出格式

支持 9 种数据来源：
- CSV: 支付宝(GBK)、京东(UTF-8-BOM)、美团(UTF-8-BOM) — 均有元数据头
- XLSX: 微信支付
- PDF: 交通银行储蓄卡、招商银行储蓄卡、中信信用卡、招商银行信用卡、抖音月付

每个解析器返回 list[dict]
"""
import re
import csv
import io
from decimal import Decimal
from datetime import datetime
from typing import Any

from utils.helpers import detect_source


# ═══════════════════════════════════════════════════════════
# CSV 通用工具
# ═══════════════════════════════════════════════════════════

def _read_csv_content(file_path: str) -> str:
    """读取 CSV 文件内容，自动尝试多种编码"""
    for encoding in ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'gb18030']:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                if content.strip():
                    return content
        except (UnicodeDecodeError, UnicodeError):
            continue
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def _find_header_line(lines: list[str], keywords: list[str]) -> int:
    """在行列表中找表头行，返回行号（从0开始），未找到返回 -1"""
    for i, line in enumerate(lines):
        if all(kw in line for kw in keywords):
            return i
    return -1


# ═══════════════════════════════════════════════════════════
# 支付宝 CSV — GBK 编码，前 24 行元数据
# ═══════════════════════════════════════════════════════════

def parse_alipay_csv(content: str) -> list[dict]:
    """支付宝 CSV：GBK 编码，前 N 行元数据，表头含"交易时间,交易分类,交易对方..." """
    lines = content.split('\n')
    header_idx = _find_header_line(lines, ['交易时间', '交易分类', '交易对方'])
    if header_idx < 0:
        return []

    reader = csv.DictReader(lines[header_idx:])
    rows = []
    for row in reader:
        if not row.get('交易时间'):
            continue

        date = row.get('交易时间', '')
        merchant = row.get('交易对方', '')
        description = row.get('商品说明', '')
        direction_raw = row.get('收/支', '')
        amount_raw = row.get('金额', '')
        trans_type = row.get('交易分类', '')
        payment_method = row.get('收/付款方式', '')
        status = row.get('交易状态', '')

        if not status or ('成功' not in status and '已付' not in status):
            continue

        try:
            amount = Decimal(abs(float(amount_raw.replace(',', ''))))
        except (ValueError, TypeError):
            continue

        # 不计收支 → 跳过
        if direction_raw == '不计收支' or '不计收支' in direction_raw:
            continue

        direction = 'expense' if '支' in direction_raw else 'income'

        try:
            parsed_date = _parse_date(date.strip())
        except ValueError:
            continue

        rows.append({
            'trans_date': parsed_date,
            'amount': amount,
            'direction': direction,
            'trans_type': trans_type.strip(),
            'description': description.strip(),
            'merchant': merchant.strip(),
            'counterparty': merchant.strip(),
            'payment_method': payment_method.strip(),
            'payment_channel': _extract_payment_channel(payment_method, description),
            'source': 'alipay',
        })
    return rows


# ═══════════════════════════════════════════════════════════
# 京东 CSV — UTF-8-BOM，前 22 行元数据
# ═══════════════════════════════════════════════════════════

def parse_jd_csv(content: str) -> list[dict]:
    """京东 CSV：UTF-8-BOM，前 N 行元数据，表头含"交易时间,商户名称,交易说明..." """
    lines = content.split('\n')
    header_idx = _find_header_line(lines, ['交易时间', '商户名称', '交易说明'])
    if header_idx < 0:
        return []

    reader = csv.DictReader(lines[header_idx:])
    rows = []
    for row in reader:
        if not row.get('交易时间'):
            continue

        date = row.get('交易时间', '').strip()
        merchant = row.get('商户名称', '')
        description = row.get('交易说明', '')
        direction_raw = row.get('收/支', '')
        amount_raw = row.get('金额', '')
        trans_type = row.get('交易分类', '')
        payment_method = row.get('收/付款方式', '')
        status = row.get('交易状态', '')

        if not status or ('成功' not in status and '完成' not in status):
            continue

        try:
            amount = Decimal(abs(float(amount_raw.replace(',', ''))))
        except (ValueError, TypeError):
            continue

        # 不计收支 → 跳过
        if '不计收支' in direction_raw:
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
            'merchant': merchant.strip(),
            'counterparty': merchant.strip(),
            'payment_method': payment_method.strip() or '京东白条',
            'payment_channel': '京东白条',
            'source': 'jd',
        })
    return rows


# ═══════════════════════════════════════════════════════════
# 美团 CSV — UTF-8-BOM，前 20 行元数据
# ═══════════════════════════════════════════════════════════

def parse_meituan_csv(content: str) -> list[dict]:
    """美团 CSV：UTF-8-BOM，前 N 行元数据，表头含"交易创建时间,交易成功时间,交易类型..." """
    lines = content.split('\n')
    header_idx = _find_header_line(lines, ['交易创建时间', '交易成功时间', '交易类型', '订单标题'])
    if header_idx < 0:
        return []

    reader = csv.DictReader(lines[header_idx:])
    rows = []
    for row in reader:
        if not row.get('交易创建时间'):
            continue

        date = row.get('交易创建时间', '').strip()
        trans_type = row.get('交易类型', '')
        description = row.get('订单标题', '')
        direction_raw = row.get('收/支', '')
        # 美团用实付金额
        amount_raw = row.get('实付金额', '') or row.get('订单金额', '')
        payment_method = row.get('支付方式', '')

        # 清理金额中的 ¥ 符号
        amount_raw = amount_raw.replace('¥', '').replace(',', '').strip()

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
            'merchant': description.strip()[:50],
            'counterparty': '',
            'payment_method': payment_method.strip() or '美团月付',
            'payment_channel': '美团月付',
            'source': 'meituan',
        })
    return rows


# ═══════════════════════════════════════════════════════════
# 微信支付 XLSX
# ═══════════════════════════════════════════════════════════

def parse_wechat_xlsx(worksheet) -> list[dict]:
    """微信支付 XLSX — 前 18 行元数据，表头在 L17"""
    all_rows = []
    for row in worksheet.iter_rows(values_only=True):
        all_rows.append([str(c) if c is not None else '' for c in row])

    if len(all_rows) < 18:
        return []

    # 跳过元数据，从表头行开始
    header = all_rows[17]
    data_rows = all_rows[18:]

    col_map = {}
    header_mapping = {
        'date': ['交易时间'],
        'trans_type': ['交易类型'],
        'counterparty': ['交易对方'],
        'description': ['商品'],
        'direction_raw': ['收/支'],
        'amount': ['金额'],
        'payment_method': ['支付方式'],
        'status': ['当前状态'],
    }

    for idx, col_name in enumerate(header):
        col_clean = col_name.strip()
        for key, aliases in header_mapping.items():
            if any(a in col_clean for a in aliases):
                col_map[key] = idx
                break

    rows = []
    for row in data_rows:
        if not any(row):
            continue

        def _get(key, default=''):
            idx = col_map.get(key)
            return row[idx].strip() if idx is not None and idx < len(row) else default

        amount_raw = _get('amount').replace('¥', '').replace(',', '')
        direction_raw = _get('direction_raw')
        status = _get('status')

        # 跳过非成功交易（转账等待确认等）
        if status and '成功' not in status and '已入账' not in status:
            continue

        try:
            amount = Decimal(abs(float(amount_raw)))
        except (ValueError, TypeError):
            continue

        direction = 'expense' if ('支' in direction_raw or '支出' in direction_raw) else 'income'

        try:
            parsed_date = _parse_date(_get('date'))
        except ValueError:
            continue

        rows.append({
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
    return rows


# ═══════════════════════════════════════════════════════════
# PDF 解析器
# ═══════════════════════════════════════════════════════════

def parse_bocom_debit_pdf(pages) -> list[dict]:
    """交通银行储蓄卡 PDF — 表格提取"""
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
    cleaned = [str(c).strip() if c else '' for c in row_data]
    if not cleaned or '交易日期' in cleaned[0] or '记账日期' in cleaned[0]:
        return None

    date = ''
    amount_raw = ''
    for cell in cleaned:
        if re.match(r'\d{4}[/-]\d{2}[/-]\d{2}', cell) and not date:
            date = cell
        elif re.match(r'^[+-]?\d[\d,]*\.?\d*$', cell):
            amount_raw = cell

    if not date or not amount_raw:
        return None

    amount_raw = amount_raw.replace(',', '').replace('+', '')
    try:
        amount = Decimal(abs(float(amount_raw)))
    except ValueError:
        return None

    direction = 'expense' if amount_raw.startswith('-') else 'income'
    texts = [c for c in cleaned if c and c != date and c != amount_raw]
    description = ' '.join(texts) if texts else ''
    counterparty = texts[0] if texts else ''

    try:
        parsed_date = _parse_date(date)
    except ValueError:
        return None

    return {
        'trans_date': parsed_date, 'amount': amount, 'direction': direction,
        'trans_type': _detect_bocom_type(description),
        'description': description, 'merchant': counterparty,
        'counterparty': counterparty,
        'payment_method': '交通银行储蓄卡',
        'payment_channel': _extract_payment_channel_from_text(description),
        'source': 'bocom_debit',
    }


def _detect_bocom_type(desc: str) -> str:
    for kw, tp in [('快捷支付', '快捷支付'), ('网上支付', '网上支付'),
                   ('银联', '银联支付'), ('转账', '转账汇款'),
                   ('代发工资', '代发工资'), ('还款', '还款')]:
        if kw in desc:
            return tp
    return '其他'


def parse_cmb_debit_pdf(pages) -> list[dict]:
    """招商银行储蓄卡 PDF — 文本+正则"""
    rows = []
    text = '\n'.join(page.extract_text() or '' for page in pages)
    pattern = re.compile(
        r'(\d{4}[-/]\d{2}[-/]\d{2})\s+(.+?)\s+([-]?[\d,]+\.\d{2})\s+[\d,]+\.\d{2}'
    )
    for match in pattern.finditer(text):
        date = match.group(1)
        desc = match.group(2).strip()
        amount_raw = match.group(3).replace(',', '')
        if '余额' in desc and '结转' in desc:
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
            'trans_date': parsed_date, 'amount': amount, 'direction': direction,
            'trans_type': _detect_cmb_type(desc),
            'description': desc, 'merchant': _extract_merchant_from_desc(desc),
            'counterparty': _extract_counterparty_from_desc(desc),
            'payment_method': '招商银行储蓄卡',
            'payment_channel': _extract_payment_channel_from_text(desc),
            'source': 'cmb_debit',
        })
    return rows


def _detect_cmb_type(desc: str) -> str:
    for kw, tp in [('快捷支付', '快捷支付'), ('网上支付', '网上支付'),
                   ('转账', '转账汇款'), ('代发', '代发工资'), ('工资', '代发工资'),
                   ('还款', '还款'), ('银联', '银联支付'), ('取款', '取款'), ('ATM', '取款')]:
        if kw in desc:
            return tp
    return '其他'


def parse_cib_credit_pdf(pages) -> list[dict]:
    """中信信用卡 PDF — 表格+状态机"""
    rows = []
    in_table = False
    current_month = None
    for page in pages:
        text = page.extract_text() or ''
        month_match = re.search(r'(\d{4})年(\d{1,2})月', text)
        if month_match:
            current_month = f"{month_match.group(1)}-{int(month_match.group(2)):02d}"
        tables = page.extract_tables()
        for table in tables:
            for row_data in table:
                if not row_data or not any(row_data):
                    continue
                cleaned = [str(c).strip() if c else '' for c in row_data]
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
    date = ''
    desc_parts = []
    amount_raw = ''
    for cell in cleaned:
        if re.match(r'\d{1,2}/\d{1,2}', cell) and not date:
            date = cell
        elif re.match(r'^[-]?[\d,]+\.\d{2}$', cell):
            amount_raw = cell
        elif cell:
            desc_parts.append(cell)
    if not date or not amount_raw:
        return None

    parts = date.split('/')
    if current_month:
        full_date = f"{current_month}-{int(parts[0]):02d}-{int(parts[1]):02d}"
    else:
        full_date = f"2026-{int(parts[0]):02d}-{int(parts[1]):02d}"

    amount_raw = amount_raw.replace(',', '')
    try:
        amount = Decimal(abs(float(amount_raw)))
    except ValueError:
        return None

    direction = 'expense' if amount_raw.startswith('-') else 'income'
    desc = ' '.join(desc_parts)

    try:
        parsed_date = _parse_date(full_date)
    except ValueError:
        return None

    return {
        'trans_date': parsed_date, 'amount': amount, 'direction': direction,
        'trans_type': _detect_cib_type(desc),
        'description': desc, 'merchant': _extract_merchant_from_desc(desc),
        'counterparty': _extract_counterparty_from_desc(desc),
        'payment_method': '中信信用卡',
        'payment_channel': _extract_payment_channel_from_text(desc),
        'source': 'cib_credit',
    }


def _detect_cib_type(desc: str) -> str:
    for kw, tp in [('财付通', '财付通'), ('支付宝', '支付宝'),
                   ('美团', '美团'), ('特约', '特约商户'), ('还款', '还款')]:
        if kw in desc:
            return tp
    return '消费'


def parse_cmb_credit_pdf(pages) -> list[dict]:
    """招商银行信用卡 PDF — 表格+日期推断"""
    rows = []
    current_statement_year = None
    current_statement_month = None
    for page in pages:
        text = page.extract_text() or ''
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
                parsed = _parse_cmb_credit_row(cleaned, current_statement_year, current_statement_month)
                if parsed:
                    rows.append(parsed)
    return rows


def _parse_cmb_credit_row(cleaned: list, year: int | None, month: int | None) -> dict | None:
    date = ''
    desc = ''
    amount_raw = ''
    for cell in cleaned:
        if re.match(r'\d{1,2}/\d{1,2}$', cell) and not date:
            date = cell
        elif re.match(r'^[-]?[\d,]+\.\d{2}$', cell):
            amount_raw = cell
        elif cell:
            desc += cell + ' '
    if not date or not amount_raw:
        return None
    desc = desc.strip()
    parts = date.split('/')
    if year and month:
        full_date = f"{year}-{int(parts[0]):02d}-{int(parts[1]):02d}"
    else:
        full_date = f"2026-{int(parts[0]):02d}-{int(parts[1]):02d}"
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
        'trans_date': parsed_date, 'amount': amount, 'direction': direction,
        'trans_type': _detect_cmb_credit_type(desc),
        'description': desc, 'merchant': _extract_merchant_from_desc(desc),
        'counterparty': _extract_counterparty_from_desc(desc),
        'payment_method': '招商银行信用卡',
        'payment_channel': _extract_payment_channel_from_text(desc),
        'source': 'cmb_credit',
    }


def _detect_cmb_credit_type(desc: str) -> str:
    for kw, tp in [('财付通', '财付通'), ('支付宝', '支付宝'),
                   ('美团', '美团'), ('特约', '特约商户')]:
        if kw in desc:
            return tp
    return '消费'


def parse_douyin_pdf(pages) -> list[dict]:
    """抖音月付 PDF — 文本+正则"""
    rows = []
    text = '\n'.join(page.extract_text() or '' for page in pages)
    pattern = re.compile(r'(\d{4}[-/]\d{2}[-/]\d{2})\s+(.+?)\s+([-]?[\d,]+\.\d{2})')
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
            'trans_date': parsed_date, 'amount': amount, 'direction': direction,
            'trans_type': '抖音月付',
            'description': desc, 'merchant': _extract_merchant_from_desc(desc),
            'counterparty': '',
            'payment_method': '抖音月付', 'payment_channel': '抖音月付',
            'source': 'douyin',
        })
    return rows


# ═══════════════════════════════════════════════════════════
# 统一入口
# ═══════════════════════════════════════════════════════════

PARSER_MAP = {
    'alipay': parse_alipay_csv,
    'jd': parse_jd_csv,
    'meituan': parse_meituan_csv,
    'wechat': None,
    'bocom_debit': parse_bocom_debit_pdf,
    'cmb_debit': parse_cmb_debit_pdf,
    'cib_credit': parse_cib_credit_pdf,
    'cmb_credit': parse_cmb_credit_pdf,
    'douyin': parse_douyin_pdf,
}


def parse_file(file_path: str, filename: str,
               source_hint: str | None = None) -> tuple[list[dict], str]:
    """统一文件解析入口"""
    source = source_hint or detect_source(filename)
    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''

    # PDF 文件如果文件名无法识别，尝试内容检测
    if not source and ext == 'pdf':
        import pdfplumber
        try:
            with pdfplumber.open(file_path) as pdf:
                text = '\n'.join(p.extract_text() or '' for p in pdf.pages[:2])
            source = _detect_source_from_text(text)
        except Exception:
            pass

    if not source:
        raise ValueError(f'无法识别文件来源: {filename}')

    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''

    if ext == 'csv' and source in ('alipay', 'jd', 'meituan'):
        content = _read_csv_content(file_path)
        parser = PARSER_MAP[source]
        return parser(content), source

    if ext == 'xlsx' and source == 'wechat':
        import openpyxl
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb.active
        rows = parse_wechat_xlsx(ws)
        wb.close()
        return rows, source

    if ext == 'pdf':
        import pdfplumber
        parser = PARSER_MAP.get(source)
        if not parser:
            raise ValueError(f'不支持的 PDF 来源: {source}')
        with pdfplumber.open(file_path) as pdf:
            # 在 with 块内完成所有 page 操作（pdfplumber 的 page 是惰性的）
            result = parser(pdf.pages)
        return result, source

    raise ValueError(f'不支持的文件格式: {ext} (来源: {source})')


# ═══════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════

def _parse_date(date_str: str) -> str:
    date_str = date_str.strip()
    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S',
                '%Y年%m月%d日', '%m/%d/%Y', '%m/%d/%y']:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    try:
        return datetime.strptime(date_str[:10], '%Y-%m-%d').strftime('%Y-%m-%d')
    except ValueError:
        pass
    raise ValueError(f'无法解析日期: {date_str}')


def _extract_payment_channel(payment_method: str, description: str) -> str:
    text = (payment_method + ' ' + description).lower()
    if '花呗' in text:
        return '花呗'
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
    t = text.lower()
    for kw, ch in [('支付宝', '支付宝'), ('alipay', '支付宝'),
                   ('微信', '微信支付'), ('wechat', '微信支付'),
                   ('财付通', '微信支付'), ('银联', '银联'),
                   ('快捷支付', '快捷支付'), ('网上支付', '网上支付')]:
        if kw in t:
            return ch
    return ''


def _extract_merchant_from_desc(desc: str) -> str:
    m = re.search(r'^(.+?)[\s-]', desc)
    if m:
        return m.group(1).strip()
    return desc.strip()


def _extract_counterparty_from_desc(desc: str) -> str:
    for pat in [r'转账给(\S+)', r'向(\S+)转账']:
        m = re.search(pat, desc)
        if m:
            return m.group(1)
    return ''


def _detect_source_from_text(text: str) -> str | None:
    """从 PDF 文本内容检测来源"""
    t = text
    # 抖音月付
    if '抖音月付' in t or 'DOUYIN' in t or 'dy_' in t.lower():
        return 'douyin'
    # 中信信用卡
    if '中信银行' in t and '信用卡' in t:
        return 'cib_credit'
    # 招商银行信用卡
    if '招商银行信用卡' in t or '招商银行' in t and '信用卡账单' in t:
        return 'cmb_credit'
    # 招商银行储蓄卡
    if '招商银行' in t and ('一卡通' in t or '储蓄卡' in t or '交易流水' in t):
        return 'cmb_debit'
    # 交通银行储蓄卡
    if '交通银行' in t or '交行' in t:
        return 'bocom_debit'
    return None
