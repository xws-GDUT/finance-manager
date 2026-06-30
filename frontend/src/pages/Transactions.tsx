import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  Table, Card, Space, Input, Select, DatePicker, Tag,
  Button, Modal, TreeSelect, message, Popconfirm, Tooltip,
  Checkbox,
} from 'antd';
import { EditOutlined, DeleteOutlined, SearchOutlined, FilterOutlined } from '@ant-design/icons';
import type { ColumnsType, FilterValue, ColumnType } from 'antd/es/table';
import type { FilterDropdownProps } from 'antd/es/table/interface';
import dayjs from 'dayjs';
import {
  fetchTransactions, fetchFilterValues,
  updateTransaction, deleteTransaction,
  fetchCategories,
} from '../api';
import type { Transaction, FilterValues, Category } from '../types';

const { RangePicker } = DatePicker;

/** 通用的表头筛选下拉组件 */
function FilterDropdown({
  options,
  selectedValues,
  onChange,
  placeholder,
}: {
  options: { value: string | number; label: string; count?: number }[];
  selectedValues: (string | number)[];
  onChange: (values: (string | number)[]) => void;
  placeholder?: string;
}) {
  const [search, setSearch] = useState('');
  const allValues = useMemo(() => options.map(o => o.value), [options]);

  // 搜索结果 — 筛选后的选项
  const filteredOptions = useMemo(() => {
    if (!search) return options;
    const kw = search.toLowerCase();
    return options.filter(o => o.label.toLowerCase().includes(kw));
  }, [options, search]);

  // 筛选后的全部值（用于"全选"）
  const filteredAllValues = useMemo(() => filteredOptions.map(o => o.value), [filteredOptions]);

  // 筛选后是否全选
  const isAllFilteredSelected = filteredAllValues.length > 0 && filteredAllValues.every(v => selectedValues.includes(v));
  // 是否部分选中
  const isIndeterminate = selectedValues.length > 0 && !isAllFilteredSelected;

  const toggleAll = () => {
    if (isAllFilteredSelected) {
      // 取消全选：移除当前筛选结果中的所有值
      onChange(selectedValues.filter(v => !filteredAllValues.includes(v)));
    } else {
      // 全选：合并当前筛选结果中的所有值（保留已选的不在当前筛选中的值）
      const newSet = new Set([...selectedValues, ...filteredAllValues]);
      onChange(Array.from(newSet));
    }
  };

  return (
    <div style={{ padding: 8, minWidth: 200, maxWidth: 300 }}>
      <Input
        placeholder={placeholder || '搜索...'}
        value={search}
        onChange={e => setSearch(e.target.value)}
        style={{ marginBottom: 8 }}
        allowClear
        size="small"
        prefix={<SearchOutlined />}
      />
      <div style={{ marginBottom: 4, maxHeight: 240, overflowY: 'auto' }}>
        <div
          style={{ padding: '4px 8px', borderBottom: '1px solid #f0f0f0', cursor: 'pointer', fontWeight: 500 }}
          onClick={toggleAll}
        >
          <Checkbox checked={isAllFilteredSelected} indeterminate={isIndeterminate}>
            全选
          </Checkbox>
        </div>
        <Checkbox.Group
          value={selectedValues}
          onChange={values => onChange(values as (string | number)[])}
          style={{ width: '100%' }}
        >
          {filteredOptions.map(opt => (
            <div key={String(opt.value)} style={{ padding: '2px 8px' }}>
              <Checkbox value={opt.value}>
                {opt.label}
                {opt.count !== undefined && (
                  <span style={{ color: '#999', marginLeft: 4, fontSize: 12 }}>({opt.count})</span>
                )}
              </Checkbox>
            </div>
          ))}
        </Checkbox.Group>
        {filteredOptions.length === 0 && search && (
          <div style={{ padding: 16, textAlign: 'center', color: '#999' }}>无匹配结果</div>
        )}
      </div>
    </div>
  );
}

export default function Transactions() {
  const [data, setData] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [filters, setFilters] = useState<FilterValues | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);

  // 筛选状态
  const [search, setSearch] = useState('');
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null] | null>(null);

  // 表头筛选值
  const [categoryFilter, setCategoryFilter] = useState<(string | number)[]>([]);
  const [transTypeFilter, setTransTypeFilter] = useState<(string | number)[]>([]);
  const [sourceFilter, setSourceFilter] = useState<(string | number)[]>([]);
  const [statusFilter, setStatusFilter] = useState<(string | number)[]>([]);
  const [directionFilter, setDirectionFilter] = useState<(string | number)[]>([]);

  // 编辑 Modal
  const [editModal, setEditModal] = useState(false);
  const [editingTx, setEditingTx] = useState<Transaction | null>(null);
  const [editCategory, setEditCategory] = useState<number | null>(null);
  const [editRemark, setEditRemark] = useState('');

  // 排序
  const [sortOrder, setSortOrder] = useState<string>('-trans_date');

  // 防抖 ref
  const searchTimer = useRef<ReturnType<typeof setTimeout>>();

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {
        page: String(page),
        page_size: String(pageSize),
        ordering: sortOrder,
      };
      if (search) params.search = search;
      if (dateRange?.[0]) params.date_from = dateRange[0].format('YYYY-MM-DD');
      if (dateRange?.[1]) params.date_to = dateRange[1].format('YYYY-MM-DD');
      if (categoryFilter.length) params.categories = categoryFilter.join(',');
      if (transTypeFilter.length) params.trans_types = transTypeFilter.join(',');
      if (sourceFilter.length) params.sources = sourceFilter.join(',');
      if (statusFilter.length) params.statuses = statusFilter.join(',');
      if (directionFilter.length) params.directions = directionFilter.join(',');

      const res = await fetchTransactions(params);
      setData(res.results);
      setTotal(res.count);
    } catch {
      message.error('加载交易数据失败');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, search, dateRange, categoryFilter, transTypeFilter, sourceFilter, statusFilter, directionFilter, sortOrder]);

  useEffect(() => { loadData(); }, [loadData]);
  useEffect(() => {
    fetchFilterValues().then(setFilters).catch(() => {});
    fetchCategories().then(setCategories).catch(() => {});
  }, []);

  // 排序变化
  const handleTableChange = (_pagination: unknown, _filters: unknown, sorter: any) => {
    if (sorter.field) {
      const order = sorter.order === 'ascend' ? sorter.field : `-${sorter.field}`;
      setSortOrder(order);
    }
    setPage(1);
  };

  // 编辑
  const openEdit = (tx: Transaction) => {
    setEditingTx(tx);
    setEditCategory(tx.category);
    setEditRemark(tx.remark || '');
    setEditModal(true);
  };

  const saveEdit = async () => {
    if (!editingTx) return;
    try {
      await updateTransaction(editingTx.id, {
        category: editCategory ?? undefined,
        remark: editRemark,
      });
      message.success('已更新');
      setEditModal(false);
      loadData();
    } catch {
      message.error('更新失败');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteTransaction(id);
      message.success('已删除');
      loadData();
    } catch {
      message.error('删除失败');
    }
  };

  // 构建分类 TreeSelect 数据
  const buildCategoryTree = (cats: Category[]): any[] =>
    cats.map(c => ({
      title: `${c.icon} ${c.name}`,
      value: c.id,
      key: c.id,
      children: c.children?.map(ch => ({
        title: `${ch.icon} ${ch.name}`,
        value: ch.id,
        key: ch.id,
      })),
    }));

  // 表头筛选配置
  const sourceOptions = useMemo(() => filters?.sources || [], [filters]);
  const statusOptions = useMemo(() => filters?.statuses || [], [filters]);
  const transTypeOptions = useMemo(() => filters?.trans_types || [], [filters]);
  const categoryOptions = useMemo(() => filters?.categories || [], [filters]);
  const directionOptions = useMemo(() => filters?.directions || [], [filters]);

  const columns: ColumnsType<Transaction> = [
    {
      title: '日期', dataIndex: 'trans_date', key: 'trans_date',
      width: 110, sorter: true, fixed: 'left',
      render: (v: string) => dayjs(v).format('YYYY-MM-DD'),
    },
    {
      title: '类型', dataIndex: 'direction', key: 'direction', width: 80,
      filterDropdown: (props: FilterDropdownProps) => (
        <FilterDropdown
          options={directionOptions}
          selectedValues={directionFilter}
          onChange={(v) => { setDirectionFilter(v); setPage(1); }}
          placeholder="搜索类型..."
        />
      ),
      onFilter: () => true,
      filtered: directionFilter.length > 0,
      filterIcon: (filtered: boolean) => (
        <FilterOutlined style={{ color: filtered ? '#1677ff' : undefined }} />
      ),
      render: (_: string, r: Transaction) => (
        <Tag color={r.direction === 'expense' ? 'red' : 'green'}>
          {r.direction_display}
        </Tag>
      ),
    },
    {
      title: '分类', dataIndex: 'category_name', key: 'category', width: 130,
      filterDropdown: (props: FilterDropdownProps) => (
        <FilterDropdown
          options={categoryOptions}
          selectedValues={categoryFilter}
          onChange={(v) => { setCategoryFilter(v); setPage(1); }}
          placeholder="搜索分类..."
        />
      ),
      onFilter: () => true,
      filtered: categoryFilter.length > 0,
      filterIcon: (filtered: boolean) => (
        <FilterOutlined style={{ color: filtered ? '#1677ff' : undefined }} />
      ),
      render: (_: string, r: Transaction) => (
        <span>{r.category_icon} {r.category_name || '未分类'}</span>
      ),
    },
    {
      title: '交易类型', dataIndex: 'trans_type', key: 'trans_type', width: 100,
      ellipsis: true,
      filterDropdown: (props: FilterDropdownProps) => (
        <FilterDropdown
          options={transTypeOptions}
          selectedValues={transTypeFilter}
          onChange={(v) => { setTransTypeFilter(v); setPage(1); }}
          placeholder="搜索交易类型..."
        />
      ),
      onFilter: () => true,
      filtered: transTypeFilter.length > 0,
      filterIcon: (filtered: boolean) => (
        <FilterOutlined style={{ color: filtered ? '#1677ff' : undefined }} />
      ),
    },
    {
      title: '商户/描述', key: 'desc', width: 220, ellipsis: true,
      render: (_: unknown, r: Transaction) => (
        <Tooltip title={r.description}>
          <span>{r.merchant || r.description}</span>
        </Tooltip>
      ),
    },
    {
      title: '对手方', dataIndex: 'counterparty', key: 'counterparty', width: 100,
      ellipsis: true,
    },
    {
      title: '金额', dataIndex: 'amount', key: 'amount', width: 120, sorter: true,
      render: (v: number, r: Transaction) => (
        <span style={{ color: r.direction === 'expense' ? '#cf1322' : '#389e0d', fontWeight: 500 }}>
          {r.direction === 'expense' ? '-' : '+'}¥{v.toLocaleString()}
        </span>
      ),
    },
    {
      title: '支付方式', dataIndex: 'payment_method', key: 'payment_method', width: 100,
      ellipsis: true,
    },
    {
      title: '来源', dataIndex: 'source_display', key: 'source', width: 110,
      filterDropdown: (props: FilterDropdownProps) => (
        <FilterDropdown
          options={sourceOptions}
          selectedValues={sourceFilter}
          onChange={(v) => { setSourceFilter(v); setPage(1); }}
          placeholder="搜索来源..."
        />
      ),
      onFilter: () => true,
      filtered: sourceFilter.length > 0,
      filterIcon: (filtered: boolean) => (
        <FilterOutlined style={{ color: filtered ? '#1677ff' : undefined }} />
      ),
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 80,
      filterDropdown: (props: FilterDropdownProps) => (
        <FilterDropdown
          options={statusOptions}
          selectedValues={statusFilter}
          onChange={(v) => { setStatusFilter(v); setPage(1); }}
          placeholder="搜索状态..."
        />
      ),
      onFilter: () => true,
      filtered: statusFilter.length > 0,
      filterIcon: (filtered: boolean) => (
        <FilterOutlined style={{ color: filtered ? '#1677ff' : undefined }} />
      ),
      render: (s: string) => {
        const m: Record<string, { color: string; text: string }> = {
          confirmed: { color: 'green', text: '有效' },
          excluded: { color: 'red', text: '无效' },
          unknown: { color: 'default', text: '未知' },
        };
        const info = m[s] || { color: 'default', text: s };
        return <Tag color={info.color}>{info.text}</Tag>;
      },
    },
    {
      title: '判定原因', key: 'reasons', width: 180,
      render: (_: unknown, r: Transaction) => (
        <Space size={2} wrap>
          {r.status_reason?.map((reason, i) => (
            <Tag key={i} color={reason.color} style={{ fontSize: 11 }}>
              {reason.label}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '操作', key: 'actions', width: 100, fixed: 'right',
      render: (_: unknown, r: Transaction) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEdit(r)} />
          <Popconfirm title="确定删除此交易？" onConfirm={() => handleDelete(r.id)}>
            <Button type="link" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Card title="交易明细" style={{ overflow: 'auto' }}>
      {/* 筛选栏 */}
      <Space wrap style={{ marginBottom: 16 }}>
        <Input
          placeholder="搜索描述/商户/对手方..."
          prefix={<SearchOutlined />}
          value={search}
          onChange={e => {
            setSearch(e.target.value);
            setPage(1);
          }}
          style={{ width: 240 }}
          allowClear
        />
        <RangePicker
          value={dateRange as any}
          onChange={(v) => { setDateRange(v as any); setPage(1); }}
          allowClear
        />
        <Button onClick={loadData}>刷新</Button>
      </Space>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1400 }}
        sticky={{ offsetHeader: 0 }}
        onChange={handleTableChange as any}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: true,
          pageSizeOptions: ['20', '30', '50', '100'],
          showTotal: (t) => `共 ${t} 条`,
          onChange: (p, ps) => { setPage(p); setPageSize(ps); },
        }}
        size="middle"
      />

      {/* 编辑 Modal */}
      <Modal
        title="编辑交易"
        open={editModal}
        onOk={saveEdit}
        onCancel={() => setEditModal(false)}
        okText="保存"
        cancelText="取消"
      >
        {editingTx && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <div style={{ marginBottom: 4, fontWeight: 500 }}>分类</div>
              <TreeSelect
                style={{ width: '100%' }}
                value={editCategory}
                onChange={(v) => setEditCategory(v)}
                treeData={buildCategoryTree(categories)}
                placeholder="选择分类"
                allowClear
                treeDefaultExpandAll
              />
            </div>
            <div>
              <div style={{ marginBottom: 4, fontWeight: 500 }}>备注</div>
              <Input.TextArea
                value={editRemark}
                onChange={e => setEditRemark(e.target.value)}
                rows={3}
                placeholder="添加备注..."
              />
            </div>
          </Space>
        )}
      </Modal>
    </Card>
  );
}
