import axios from 'axios';
import type {
  Transaction, PaginatedResponse, FilterValues,
  StatsOverview, MonthlyStat, CategoryStat, DailyStat,
  ValidRule, InvalidRule,
  TransactionPair, AAScanResult,
  SettlementGroup,
  Category, Account, ImportLog,
} from '../types';

// 本地开发通过 Vite proxy 转发 /api，Render 部署通过 VITE_API_BASE 指定后端地址
const API_BASE = import.meta.env.VITE_API_BASE || '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// ── 交易查询 ──────────────────────────────────────────

export const fetchTransactions = (params: Record<string, string>) =>
  api.get<PaginatedResponse<Transaction>>('/transactions/', { params }).then(r => r.data);

export const fetchTransaction = (id: number) =>
  api.get<Transaction>(`/transactions/${id}/`).then(r => r.data);

export const updateTransaction = (id: number, data: Partial<Transaction>) =>
  api.patch<Transaction>(`/transactions/${id}/`, data).then(r => r.data);

export const deleteTransaction = (id: number) =>
  api.delete(`/transactions/${id}/`);

export const fetchFilterValues = () =>
  api.get<FilterValues>('/transactions/filter_values/').then(r => r.data);

// ── 统计分析 ──────────────────────────────────────────

export const fetchStatsOverview = () =>
  api.get<StatsOverview>('/stats/overview').then(r => r.data);

export const fetchStatsMonthly = () =>
  api.get<MonthlyStat[]>('/stats/monthly').then(r => r.data);

export const fetchStatsCategory = () =>
  api.get<CategoryStat[]>('/stats/category').then(r => r.data);

export const fetchStatsDaily = () =>
  api.get<DailyStat[]>('/stats/daily').then(r => r.data);

// ── 有效规则 ──────────────────────────────────────────

export const fetchValidRules = () =>
  api.get<{ results: ValidRule[] }>('/valid-rules/').then(r => r.data.results);

export const createValidRule = (data: Partial<ValidRule>) =>
  api.post<ValidRule>('/valid-rules/', data).then(r => r.data);

export const updateValidRule = (id: number, data: Partial<ValidRule>) =>
  api.patch<ValidRule>(`/valid-rules/${id}/`, data).then(r => r.data);

export const deleteValidRule = (id: number) =>
  api.delete(`/valid-rules/${id}/`);

export const testValidRule = (data: Record<string, unknown>) =>
  api.post<{ matched_count: number }>('/valid-rules/test/', data).then(r => r.data);

export const applyValidRules = () =>
  api.post('/valid-rules/apply/').then(r => r.data);

export const createDefaultValidRules = () =>
  api.post<{ created: number; skipped: number }>('/valid-rules/create_defaults/').then(r => r.data);

// ── 无效规则 ──────────────────────────────────────────

export const fetchInvalidRules = () =>
  api.get<{ results: InvalidRule[] }>('/invalid-rules/').then(r => r.data.results);

export const createInvalidRule = (data: Partial<InvalidRule>) =>
  api.post<InvalidRule>('/invalid-rules/', data).then(r => r.data);

export const updateInvalidRule = (id: number, data: Partial<InvalidRule>) =>
  api.patch<InvalidRule>(`/invalid-rules/${id}/`, data).then(r => r.data);

export const deleteInvalidRule = (id: number) =>
  api.delete(`/invalid-rules/${id}/`);

export const testInvalidRule = (data: Record<string, unknown>) =>
  api.post<{ matched_count: number }>('/invalid-rules/test/', data).then(r => r.data);

export const applyInvalidRules = () =>
  api.post('/invalid-rules/apply/').then(r => r.data);

export const createDefaultInvalidRules = () =>
  api.post<{ created: number; skipped: number }>('/invalid-rules/create_defaults/').then(r => r.data);

// ── 退款配对 ──────────────────────────────────────────

export const fetchRefundPairs = () =>
  api.get<{ results: TransactionPair[] }>('/refund-pairs/').then(r => r.data.results);

export const autoPair = () =>
  api.post('/refund-pairs/auto/').then(r => r.data);

export const manualPair = (expenseId: number, refundId: number) =>
  api.post('/refund-pairs/', { expense_id: expenseId, refund_id: refundId }).then(r => r.data);

export const unpair = (id: number) =>
  api.delete(`/refund-pairs/${id}/`);

export const fetchAAScan = () =>
  api.get<AAScanResult[]>('/refund-pairs/aa_scan/').then(r => r.data);

export const createAA = (receiptIds: number[], expenseId: number, groupName?: string) =>
  api.post('/refund-pairs/aa_create/', {
    receipt_ids: receiptIds,
    expense_id: expenseId,
    group_name: groupName,
  }).then(r => r.data);

// ── 垫付结算 ──────────────────────────────────────────

export const fetchSettlements = () =>
  api.get<{ results: SettlementGroup[] }>('/settlements/').then(r => r.data.results);

export const fetchSettlement = (id: number) =>
  api.get<SettlementGroup>(`/settlements/${id}/`).then(r => r.data);

export const createSettlement = (data: { name: string; description?: string }) =>
  api.post<SettlementGroup>('/settlements/', data).then(r => r.data);

export const deleteSettlement = (id: number) =>
  api.delete(`/settlements/${id}/`);

export const closeSettlement = (id: number) =>
  api.post(`/settlements/${id}/close/`).then(r => r.data);

export const reopenSettlement = (id: number) =>
  api.post(`/settlements/${id}/reopen/`).then(r => r.data);

export const addSettlementItem = (settlementId: number, transactionId: number, itemType: string) =>
  api.post(`/settlements/${settlementId}/add_item/`, {
    transaction_id: transactionId,
    item_type: itemType,
  }).then(r => r.data);

export const removeSettlementItem = (settlementId: number, itemId: number) =>
  api.delete(`/settlements/${settlementId}/items/${itemId}/`);

export const searchCandidates = (keyword: string, direction?: string) =>
  api.get('/settlements/candidates/', { params: { keyword, direction } }).then(r => r.data);

// ── 流水导入 ──────────────────────────────────────────

export const importFile = (file: File, source?: string) => {
  const formData = new FormData();
  formData.append('file', file);
  if (source) formData.append('source', source);
  return api.post('/import/upload', formData).then(r => r.data);
};

export const importBatch = (files: File[]) => {
  const formData = new FormData();
  files.forEach(f => formData.append('files', f));
  return api.post('/import/batch', formData).then(r => r.data);
};

export const fetchImportHistory = () =>
  api.get<ImportLog[]>('/import/history').then(r => r.data);

// ── 分类与账户 ────────────────────────────────────────

export const fetchCategories = () =>
  api.get<Category[]>('/categories').then(r => r.data);

export const fetchAccounts = () =>
  api.get<Account[]>('/accounts').then(r => r.data);
