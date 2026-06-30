import { describe, it, expect } from 'vitest';

// Type-only imports — verify that all types compile and are exported
import type {
  Transaction,
  StatusReason,
  Category,
  CategoryChild,
  Account,
  ValidRule,
  InvalidRule,
  TransactionPair,
  SettlementGroup,
  SettlementItem,
  ImportLog,
  StatsOverview,
  MonthlyStat,
  CategoryStat,
  DailyStat,
  PaginatedResponse,
  FilterValues,
  AAScanResult,
} from './index';

describe('types/index', () => {
  it('Transaction type has required fields', () => {
    const tx: Transaction = {
      id: 1,
      trans_date: '2025-01-01',
      amount: 100.5,
      direction: 'expense',
      direction_display: '支出',
      source: 'alipay',
      source_display: '支付宝',
      status: 'confirmed',
      status_display: '已确认',
      trans_type: '消费',
      description: '测试',
      merchant: '测试商家',
      counterparty: '',
      payment_method: '',
      payment_channel: '',
      remark: '',
      category: 1,
      category_name: '餐饮',
      category_icon: '🍜',
      category_type: 'expense',
      account: 1,
      account_name: '支付宝',
      valid_rule: null,
      valid_rule_name: '',
      invalid_rule: null,
      invalid_rule_name: '',
      pair: null,
      settlement: null,
      is_virtual: false,
      status_reason: [],
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    };
    expect(tx.id).toBe(1);
    expect(tx.amount).toBe(100.5);
    expect(tx.direction).toBe('expense');
  });

  it('StatusReason type works', () => {
    const sr: StatusReason = {
      type: 'virtual',
      label: '虚拟交易',
      color: 'blue',
    };
    expect(sr.type).toBe('virtual');
  });

  it('Category and CategoryChild types work', () => {
    const child: CategoryChild = { id: 101, name: '早餐', icon: '🥐', type: 'expense' };
    const cat: Category = {
      id: 1,
      name: '餐饮',
      icon: '🍜',
      type: 'expense',
      sort_order: 1,
      children: [child],
    };
    expect(cat.children).toHaveLength(1);
    expect(cat.children[0].name).toBe('早餐');
  });

  it('Account type has stats', () => {
    const account: Account = {
      id: 1,
      name: '支付宝',
      account_type: 'platform',
      bank_name: '',
      owner: '张三',
      match_keywords: 'alipay',
      is_active: true,
      stats: { tx_count: 10, total_expense: 500, total_income: 200 },
    };
    expect(account.stats.tx_count).toBe(10);
  });

  it('ValidRule and InvalidRule types', () => {
    const valid: ValidRule = {
      id: 1,
      name: '测试规则',
      priority: 50,
      is_active: true,
      sources: 'alipay',
      trans_types: '',
      directions: 'expense',
      categories: '',
      payment_channels: '',
      keywords: '餐饮',
      keyword_exclude: '',
      merchants: '',
      amount_min: null,
      amount_max: null,
      hit_count: 0,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    };
    const invalid: InvalidRule = { ...valid, counterparties: '测试商户' };
    expect(invalid.counterparties).toBe('测试商户');
  });

  it('TransactionPair type', () => {
    const pair: TransactionPair = {
      id: 1,
      expense_tx: 100,
      refund_tx: 200,
      expense_date: '2025-01-01',
      expense_amount: 50,
      expense_desc: '消费',
      expense_merchant: '商户A',
      refund_date: '2025-01-02',
      refund_amount: 50,
      refund_desc: '退款',
      refund_merchant: '商户A',
      match_score: 0.95,
      match_method: 'auto',
      match_detail: { amount: 1 },
      created_at: '2025-01-01T00:00:00Z',
    };
    expect(pair.match_method).toBe('auto');
  });

  it('SettlementGroup and SettlementItem types', () => {
    const item: SettlementItem = {
      id: 1,
      transaction: 10,
      item_type: 'advance',
      trans_date: '2025-01-01',
      amount: 100,
      description: '垫付',
      merchant: '商户',
      direction: 'expense',
    };
    const group: SettlementGroup = {
      id: 1,
      name: '聚餐',
      description: '',
      status: 'open',
      total_advance: 100,
      total_reimbursement: 0,
      net_amount: 100,
      virtual_tx: null,
      is_aa: false,
      items: [item],
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    };
    expect(group.items).toHaveLength(1);
  });

  it('ImportLog type', () => {
    const log: ImportLog = {
      id: 1,
      source: 'alipay',
      source_file: 'test.csv',
      file_size: 1024,
      total_rows: 100,
      imported_rows: 95,
      skipped_rows: 3,
      error_rows: 2,
      error_detail: ['row 5: invalid amount'],
      status: 'success',
      created_at: '2025-01-01T00:00:00Z',
    };
    expect(log.imported_rows).toBe(95);
  });

  it('StatsOverview type', () => {
    const stats: StatsOverview = {
      total_expense: 10000,
      total_income: 15000,
      balance: 5000,
      month_expense: 2000,
      month_income: 3000,
      month_balance: 1000,
      total_count: 50,
      effective_count: 45,
    };
    expect(stats.balance).toBe(5000);
  });

  it('MonthlyStat, CategoryStat, DailyStat types', () => {
    const ms: MonthlyStat = { month: '2025-01', expense: 500, income: 600 };
    const cs: CategoryStat = { name: '餐饮', icon: '🍜', amount: 300, count: 5 };
    const ds: DailyStat = { date: '2025-01-01', amount: 100, count: 2 };
    expect(ms.month).toBe('2025-01');
    expect(cs.icon).toBe('🍜');
    expect(ds.count).toBe(2);
  });

  it('PaginatedResponse generic type', () => {
    const res: PaginatedResponse<Transaction> = {
      count: 1,
      next: null,
      previous: null,
      results: [],
    };
    expect(res.count).toBe(1);
  });

  it('FilterValues type', () => {
    const fv: FilterValues = {
      sources: [{ value: 'alipay', label: '支付宝' }],
      statuses: [{ value: 'confirmed', label: '已确认' }],
      directions: [{ value: 'expense', label: '支出' }],
      trans_types: [{ value: '消费', label: '消费' }],
      categories: [{ value: 1, label: '餐饮', count: 10 }],
    };
    expect(fv.categories[0].count).toBe(10);
  });

  it('AAScanResult type', () => {
    const aa: AAScanResult = {
      receipts: [{ id: 1, date: '2025-01-01', amount: '100', description: '收款' }],
      total_receipt: '100',
      candidate_expenses: [{ id: 2, date: '2025-01-01', amount: '80', description: '支出' }],
      suggested_pairs: [{
        expense_id: 2,
        expense_date: '2025-01-01',
        expense_amount: '80',
        expense_desc: '支出',
        receipt_total: '100',
        ratio: 0.8,
      }],
    };
    expect(aa.suggested_pairs[0].ratio).toBe(0.8);
  });
});
