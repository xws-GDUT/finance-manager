/** 交易流水类型 */
export interface Transaction {
  id: number;
  trans_date: string;
  amount: number;
  direction: 'expense' | 'income';
  direction_display: string;
  source: string;
  source_display: string;
  status: 'confirmed' | 'excluded' | 'unknown' | 'deleted';
  status_display: string;
  trans_type: string;
  description: string;
  merchant: string;
  counterparty: string;
  payment_method: string;
  payment_channel: string;
  remark: string;
  category: number | null;
  category_name: string;
  category_icon: string;
  category_type: string;
  account: number | null;
  account_name: string;
  valid_rule: number | null;
  valid_rule_name: string;
  invalid_rule: number | null;
  invalid_rule_name: string;
  pair: number | null;
  settlement: number | null;
  is_virtual: boolean;
  status_reason: StatusReason[];
  created_at: string;
  updated_at: string;
}

export interface StatusReason {
  type: 'virtual' | 'settlement' | 'refund_pair' | 'invalid_rule' | 'valid_rule';
  label: string;
  color: string;
}

/** 分类 */
export interface Category {
  id: number;
  name: string;
  icon: string;
  type: 'expense' | 'income' | 'transfer';
  sort_order: number;
  children: CategoryChild[];
}

export interface CategoryChild {
  id: number;
  name: string;
  icon: string;
  type: string;
}

/** 账户 */
export interface Account {
  id: number;
  name: string;
  account_type: 'debit' | 'credit' | 'platform';
  bank_name: string;
  owner: string;
  match_keywords: string;
  is_active: boolean;
  stats: {
    tx_count: number;
    total_expense: number;
    total_income: number;
  };
}

/** 有效规则 */
export interface ValidRule {
  id: number;
  name: string;
  priority: number;
  is_active: boolean;
  sources: string;
  trans_types: string;
  directions: string;
  categories: string;
  payment_channels: string;
  keywords: string;
  keyword_exclude: string;
  merchants: string;
  amount_min: number | null;
  amount_max: number | null;
  hit_count: number;
  created_at: string;
  updated_at: string;
}

/** 无效规则 */
export interface InvalidRule extends ValidRule {
  counterparties: string;
}

/** 退款配对 */
export interface TransactionPair {
  id: number;
  expense_tx: number;
  refund_tx: number;
  expense_date: string;
  expense_amount: number;
  expense_desc: string;
  expense_merchant: string;
  refund_date: string;
  refund_amount: number;
  refund_desc: string;
  refund_merchant: string;
  match_score: number;
  match_method: 'auto' | 'manual' | 'aa';
  match_detail: Record<string, number>;
  created_at: string;
}

/** 结算组 */
export interface SettlementGroup {
  id: number;
  name: string;
  description: string;
  status: 'open' | 'closed';
  total_advance: number;
  total_reimbursement: number;
  net_amount: number;
  virtual_tx: number | null;
  is_aa: boolean;
  items: SettlementItem[];
  created_at: string;
  updated_at: string;
}

export interface SettlementItem {
  id: number;
  transaction: number;
  item_type: 'advance' | 'reimbursement';
  trans_date: string;
  amount: number;
  description: string;
  merchant: string;
  direction: string;
}

/** 导入日志 */
export interface ImportLog {
  id: number;
  source: string;
  source_file: string;
  file_size: number;
  total_rows: number;
  imported_rows: number;
  skipped_rows: number;
  error_rows: number;
  error_detail: string[];
  status: string;
  created_at: string;
}

/** 统计 */
export interface StatsOverview {
  total_expense: number;
  total_income: number;
  balance: number;
  month_expense: number;
  month_income: number;
  month_balance: number;
  total_count: number;
  effective_count: number;
}

export interface MonthlyStat {
  month: string;
  expense: number;
  income: number;
}

export interface CategoryStat {
  name: string;
  icon: string;
  amount: number;
  count: number;
}

export interface DailyStat {
  date: string;
  amount: number;
  count: number;
}

/** 分页 */
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/** 筛选值 */
export interface FilterValues {
  sources: { value: string; label: string }[];
  statuses: { value: string; label: string }[];
  directions: { value: string; label: string }[];
  trans_types: { value: string; label: string }[];
  categories: { value: number; label: string; count: number }[];
}

/** AA 扫描结果 */
export interface AAScanResult {
  receipts: { id: number; date: string; amount: string; description: string }[];
  total_receipt: string;
  candidate_expenses: { id: number; date: string; amount: string; description: string }[];
  suggested_pairs: {
    expense_id: number;
    expense_date: string;
    expense_amount: string;
    expense_desc: string;
    receipt_total: string;
    ratio: number;
  }[];
}
