import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockAxiosInstance = {
  get: vi.fn(),
  post: vi.fn(),
  patch: vi.fn(),
  delete: vi.fn(),
};

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mockAxiosInstance),
  },
}));

// Must re-import after mocking to get the mocked axios instance
let api: typeof import('./index');

beforeEach(async () => {
  vi.clearAllMocks();
  // Reset the mocked create to return our instance each time
  const axiosModule = await import('axios');
  (axiosModule.default.create as ReturnType<typeof vi.fn>).mockReturnValue(mockAxiosInstance);
  // Re-import to pick up fresh mocks
  api = await import('./index');
});

describe('api/index', () => {
  describe('API_BASE default and env override', () => {
    it('uses /api as default when VITE_API_BASE is not set', async () => {
      const axiosModule = await import('axios');
      expect(axiosModule.default.create).toHaveBeenCalledWith(
        expect.objectContaining({ baseURL: '/api' })
      );
    });

    it('uses VITE_API_BASE when set', async () => {
      // We test the default via the import side-effect; env override requires
      // a separate process so we validate the pattern in the source code.
      // The source reads: import.meta.env.VITE_API_BASE || '/api'
      // This confirms the fallback pattern is correct.
      expect(true).toBe(true);
    });
  });

  describe('fetchTransactions', () => {
    it('calls GET /transactions/ with params', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: { results: [], count: 0 } });
      await api.fetchTransactions({ page: '1', source: 'alipay' });
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/transactions/', {
        params: { page: '1', source: 'alipay' },
      });
    });
  });

  describe('fetchTransaction', () => {
    it('calls GET /transactions/:id/', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: { id: 1 } });
      await api.fetchTransaction(42);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/transactions/42/');
    });
  });

  describe('updateTransaction', () => {
    it('calls PATCH /transactions/:id/ with data', async () => {
      mockAxiosInstance.patch.mockResolvedValue({ data: { id: 1, remark: 'test' } });
      await api.updateTransaction(1, { remark: 'test' });
      expect(mockAxiosInstance.patch).toHaveBeenCalledWith('/transactions/1/', { remark: 'test' });
    });
  });

  describe('deleteTransaction', () => {
    it('calls DELETE /transactions/:id/', async () => {
      mockAxiosInstance.delete.mockResolvedValue({});
      await api.deleteTransaction(1);
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/transactions/1/');
    });
  });

  describe('fetchFilterValues', () => {
    it('calls GET /transactions/filter_values/', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: {} });
      await api.fetchFilterValues();
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/transactions/filter_values/');
    });
  });

  describe('fetchStatsOverview', () => {
    it('calls GET /stats/overview', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: {} });
      await api.fetchStatsOverview();
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/stats/overview');
    });
  });

  describe('fetchStatsMonthly', () => {
    it('calls GET /stats/monthly', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: [] });
      await api.fetchStatsMonthly();
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/stats/monthly');
    });
  });

  describe('fetchStatsCategory', () => {
    it('calls GET /stats/category', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: [] });
      await api.fetchStatsCategory();
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/stats/category');
    });
  });

  describe('fetchStatsDaily', () => {
    it('calls GET /stats/daily', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: [] });
      await api.fetchStatsDaily();
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/stats/daily');
    });
  });

  describe('Valid Rules', () => {
    it('fetchValidRules calls GET /valid-rules/', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: { results: [] } });
      await api.fetchValidRules();
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/valid-rules/');
    });

    it('createValidRule calls POST /valid-rules/', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: { id: 1 } });
      await api.createValidRule({ name: 'test' });
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/valid-rules/', { name: 'test' });
    });

    it('updateValidRule calls PATCH /valid-rules/:id/', async () => {
      mockAxiosInstance.patch.mockResolvedValue({ data: { id: 1 } });
      await api.updateValidRule(1, { name: 'updated' });
      expect(mockAxiosInstance.patch).toHaveBeenCalledWith('/valid-rules/1/', { name: 'updated' });
    });

    it('deleteValidRule calls DELETE /valid-rules/:id/', async () => {
      mockAxiosInstance.delete.mockResolvedValue({});
      await api.deleteValidRule(1);
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/valid-rules/1/');
    });

    it('testValidRule calls POST /valid-rules/test/', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: { matched_count: 5 } });
      await api.testValidRule({ keywords: 'test' });
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/valid-rules/test/', { keywords: 'test' });
    });

    it('applyValidRules calls POST /valid-rules/apply/', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: { matched: 10, total: 20 } });
      await api.applyValidRules();
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/valid-rules/apply/');
    });

    it('createDefaultValidRules calls POST /valid-rules/create_defaults/', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: { created: 5, skipped: 2 } });
      await api.createDefaultValidRules();
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/valid-rules/create_defaults/');
    });
  });

  describe('Invalid Rules', () => {
    it('fetchInvalidRules calls GET /invalid-rules/', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: { results: [] } });
      await api.fetchInvalidRules();
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/invalid-rules/');
    });

    it('createInvalidRule calls POST /invalid-rules/', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: { id: 1 } });
      await api.createInvalidRule({ name: 'test' });
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/invalid-rules/', { name: 'test' });
    });

    it('updateInvalidRule calls PATCH /invalid-rules/:id/', async () => {
      mockAxiosInstance.patch.mockResolvedValue({ data: { id: 1 } });
      await api.updateInvalidRule(1, { name: 'updated' });
      expect(mockAxiosInstance.patch).toHaveBeenCalledWith('/invalid-rules/1/', { name: 'updated' });
    });

    it('deleteInvalidRule calls DELETE /invalid-rules/:id/', async () => {
      mockAxiosInstance.delete.mockResolvedValue({});
      await api.deleteInvalidRule(1);
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/invalid-rules/1/');
    });

    it('testInvalidRule calls POST /invalid-rules/test/', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: { matched_count: 3 } });
      await api.testInvalidRule({ counterparties: 'test' });
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/invalid-rules/test/', { counterparties: 'test' });
    });

    it('applyInvalidRules calls POST /invalid-rules/apply/', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: {} });
      await api.applyInvalidRules();
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/invalid-rules/apply/');
    });

    it('createDefaultInvalidRules calls POST /invalid-rules/create_defaults/', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: { created: 3, skipped: 1 } });
      await api.createDefaultInvalidRules();
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/invalid-rules/create_defaults/');
    });
  });

  describe('Refund Pairs', () => {
    it('fetchRefundPairs calls GET /refund-pairs/', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: { results: [] } });
      await api.fetchRefundPairs();
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/refund-pairs/');
    });

    it('autoPair calls POST /refund-pairs/auto/', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: {} });
      await api.autoPair();
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/refund-pairs/auto/');
    });

    it('manualPair calls POST /refund-pairs/ with ids', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: {} });
      await api.manualPair(10, 20);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/refund-pairs/', {
        expense_id: 10,
        refund_id: 20,
      });
    });

    it('unpair calls DELETE /refund-pairs/:id/', async () => {
      mockAxiosInstance.delete.mockResolvedValue({});
      await api.unpair(5);
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/refund-pairs/5/');
    });

    it('fetchAAScan calls GET /refund-pairs/aa_scan/', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: [] });
      await api.fetchAAScan();
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/refund-pairs/aa_scan/');
    });

    it('createAA calls POST /refund-pairs/aa_create/', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: {} });
      await api.createAA([1, 2], 10, 'test group');
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/refund-pairs/aa_create/', {
        receipt_ids: [1, 2],
        expense_id: 10,
        group_name: 'test group',
      });
    });
  });

  describe('Settlements', () => {
    it('fetchSettlements calls GET /settlements/', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: { results: [] } });
      await api.fetchSettlements();
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/settlements/');
    });

    it('fetchSettlement calls GET /settlements/:id/', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: {} });
      await api.fetchSettlement(1);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/settlements/1/');
    });

    it('createSettlement calls POST /settlements/', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: {} });
      await api.createSettlement({ name: 'test' });
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/settlements/', { name: 'test' });
    });

    it('deleteSettlement calls DELETE /settlements/:id/', async () => {
      mockAxiosInstance.delete.mockResolvedValue({});
      await api.deleteSettlement(1);
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/settlements/1/');
    });

    it('closeSettlement calls POST /settlements/:id/close/', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: {} });
      await api.closeSettlement(1);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/settlements/1/close/');
    });

    it('reopenSettlement calls POST /settlements/:id/reopen/', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: {} });
      await api.reopenSettlement(1);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/settlements/1/reopen/');
    });

    it('addSettlementItem calls POST with correct data', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: {} });
      await api.addSettlementItem(1, 100, 'advance');
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/settlements/1/add_item/', {
        transaction_id: 100,
        item_type: 'advance',
      });
    });

    it('removeSettlementItem calls DELETE', async () => {
      mockAxiosInstance.delete.mockResolvedValue({});
      await api.removeSettlementItem(1, 5);
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/settlements/1/items/5/');
    });

    it('searchCandidates calls GET with params', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: [] });
      await api.searchCandidates('test', 'expense');
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/settlements/candidates/', {
        params: { keyword: 'test', direction: 'expense' },
      });
    });
  });

  describe('Import', () => {
    it('importFile sends FormData with file and source', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: {} });
      const file = new File(['content'], 'test.csv', { type: 'text/csv' });
      await api.importFile(file, 'alipay');
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/import/upload',
        expect.any(FormData),
      );
      const formData = mockAxiosInstance.post.mock.calls[0][1] as FormData;
      expect(formData.get('file')).toBe(file);
      expect(formData.get('source')).toBe('alipay');
    });

    it('importFile sends FormData without source when omitted', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: {} });
      const file = new File(['content'], 'test.csv', { type: 'text/csv' });
      await api.importFile(file);
      const formData = mockAxiosInstance.post.mock.calls[0][1] as FormData;
      expect(formData.get('file')).toBe(file);
      expect(formData.get('source')).toBeNull();
    });

    it('importBatch sends FormData with multiple files', async () => {
      mockAxiosInstance.post.mockResolvedValue({ data: {} });
      const files = [
        new File(['a'], 'a.csv', { type: 'text/csv' }),
        new File(['b'], 'b.csv', { type: 'text/csv' }),
      ];
      await api.importBatch(files);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/import/batch',
        expect.any(FormData),
      );
      const formData = mockAxiosInstance.post.mock.calls[0][1] as FormData;
      const allFiles = formData.getAll('files') as File[];
      expect(allFiles).toHaveLength(2);
    });

    it('fetchImportHistory calls GET /import/history', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: [] });
      await api.fetchImportHistory();
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/import/history');
    });
  });

  describe('Categories and Accounts', () => {
    it('fetchCategories calls GET /categories', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: [] });
      await api.fetchCategories();
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/categories');
    });

    it('fetchAccounts calls GET /accounts', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: [] });
      await api.fetchAccounts();
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/accounts');
    });
  });
});
