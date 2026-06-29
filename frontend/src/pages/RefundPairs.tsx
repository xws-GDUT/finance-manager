import { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Tag, message, Modal, Descriptions, Collapse } from 'antd';
import { SyncOutlined, ScanOutlined, PlusOutlined } from '@ant-design/icons';
import { fetchRefundPairs, autoPair, unpair, fetchAAScan, createAA } from '../api';
import type { TransactionPair, AAScanResult } from '../types';

export default function RefundPairs() {
  const [pairs, setPairs] = useState<TransactionPair[]>([]);
  const [loading, setLoading] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detail, setDetail] = useState<TransactionPair | null>(null);

  // AA
  const [aaResults, setAaResults] = useState<AAScanResult[]>([]);
  const [aaOpen, setAaOpen] = useState(false);

  const loadPairs = async () => {
    setLoading(true);
    try { setPairs(await fetchRefundPairs()); } catch { message.error('加载失败'); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadPairs(); }, []);

  const handleAutoPair = async () => {
    try {
      const res = await autoPair();
      message.success(`自动配对完成：${res.paired} 对，跳过 ${res.skipped}`);
      loadPairs();
    } catch { message.error('配对失败'); }
  };

  const handleUnpair = async (id: number) => {
    try { await unpair(id); message.success('已解除'); loadPairs(); }
    catch { message.error('操作失败'); }
  };

  const handleAAScan = async () => {
    try {
      const res = await fetchAAScan();
      setAaResults(res);
      setAaOpen(true);
    } catch { message.error('扫描失败'); }
  };

  const handleAACreate = async (expenseId: number, receiptIds: number[]) => {
    try {
      await createAA(receiptIds, expenseId);
      message.success('AA 结算组已创建');
      setAaOpen(false);
      loadPairs();
    } catch { message.error('创建失败'); }
  };

  const columns = [
    { title: '配对ID', dataIndex: 'id', key: 'id', width: 70 },
    {
      title: '消费', key: 'expense', width: 250,
      render: (_: unknown, r: TransactionPair) => (
        <div>
          <div style={{ color: '#cf1322', fontWeight: 500 }}>-¥{r.expense_amount.toLocaleString()}</div>
          <div style={{ fontSize: 12, color: '#666' }}>{r.expense_merchant || r.expense_desc}</div>
          <div style={{ fontSize: 11, color: '#999' }}>{r.expense_date}</div>
        </div>
      ),
    },
    {
      title: '退款', key: 'refund', width: 250,
      render: (_: unknown, r: TransactionPair) => (
        <div>
          <div style={{ color: '#389e0d', fontWeight: 500 }}>+¥{r.refund_amount.toLocaleString()}</div>
          <div style={{ fontSize: 12, color: '#666' }}>{r.refund_merchant || r.refund_desc}</div>
          <div style={{ fontSize: 11, color: '#999' }}>{r.refund_date}</div>
        </div>
      ),
    },
    {
      title: '得分', dataIndex: 'match_score', key: 'score', width: 80,
      render: (v: number) => <Tag color={v >= 80 ? 'green' : v >= 60 ? 'orange' : 'red'}>{v.toFixed(1)}</Tag>,
    },
    {
      title: '方式', dataIndex: 'match_method', key: 'method', width: 80,
      render: (v: string) => <Tag>{v === 'auto' ? '自动' : v === 'manual' ? '手动' : 'AA'}</Tag>,
    },
    {
      title: '操作', key: 'actions', width: 140,
      render: (_: unknown, r: TransactionPair) => (
        <Space size="small">
          <Button type="link" size="small" onClick={() => { setDetail(r); setDetailOpen(true); }}>详情</Button>
          <Button type="link" size="small" danger onClick={() => handleUnpair(r.id)}>解除</Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card title="退款配对" extra={
        <Space>
          <Button icon={<ScanOutlined />} onClick={handleAAScan}>AA 扫描</Button>
          <Button type="primary" icon={<SyncOutlined />} onClick={handleAutoPair}>自动配对</Button>
        </Space>
      }>
        <Table columns={columns} dataSource={pairs} rowKey="id" loading={loading} size="middle"
          pagination={{ pageSize: 20, showTotal: (t) => `共 ${t} 对` }} />
      </Card>

      <Modal title="配对详情" open={detailOpen} onCancel={() => setDetailOpen(false)} footer={null} width={500}>
        {detail && (
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="消费日期">{detail.expense_date}</Descriptions.Item>
            <Descriptions.Item label="退款日期">{detail.refund_date}</Descriptions.Item>
            <Descriptions.Item label="消费金额"><span style={{ color: '#cf1322' }}>-¥{detail.expense_amount.toLocaleString()}</span></Descriptions.Item>
            <Descriptions.Item label="退款金额"><span style={{ color: '#389e0d' }}>+¥{detail.refund_amount.toLocaleString()}</span></Descriptions.Item>
            <Descriptions.Item label="消费商户" span={2}>{detail.expense_merchant || detail.expense_desc}</Descriptions.Item>
            <Descriptions.Item label="退款商户" span={2}>{detail.refund_merchant || detail.refund_desc}</Descriptions.Item>
            <Descriptions.Item label="匹配得分">{detail.match_score.toFixed(1)}</Descriptions.Item>
            <Descriptions.Item label="配对方式"><Tag>{detail.match_method}</Tag></Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      <Modal title="AA 群收款扫描" open={aaOpen} onCancel={() => setAaOpen(false)} footer={null} width={700}>
        {aaResults.length === 0 ? (
          <p>未发现 AA 群收款场景</p>
        ) : (
          <Collapse items={aaResults.map((r, i) => ({
            key: String(i),
            label: `AA 场景 #${i + 1} - 总收款 ¥${Number(r.total_receipt).toLocaleString()}`,
            children: (
              <div>
                <div style={{ marginBottom: 12 }}>
                  <strong>群收款：</strong>
                  {r.receipts.map(rc => (
                    <Tag key={rc.id} color="green">+¥{Number(rc.amount).toLocaleString()} {rc.date}</Tag>
                  ))}
                </div>
                <div style={{ marginBottom: 12 }}>
                  <strong>建议配对：</strong>
                  {r.suggested_pairs.map(sp => (
                    <div key={sp.expense_id} style={{ margin: '8px 0', padding: 8, background: '#fafafa', borderRadius: 4 }}>
                      <div>消费：-¥{Number(sp.expense_amount).toLocaleString()} ({sp.expense_desc}) - 匹配率：{(sp.ratio * 100).toFixed(0)}%</div>
                      <Button type="primary" size="small" icon={<PlusOutlined />}
                        onClick={() => handleAACreate(sp.expense_id, r.receipts.map(rc => rc.id))}>
                        创建 AA 结算
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            ),
          }))} />
        )}
      </Modal>
    </div>
  );
}
