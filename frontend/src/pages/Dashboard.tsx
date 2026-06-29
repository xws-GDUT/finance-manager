import { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Spin } from 'antd';
import {
  ArrowUpOutlined, ArrowDownOutlined,
  WalletOutlined, DollarOutlined,
} from '@ant-design/icons';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts';
import { fetchStatsOverview, fetchStatsMonthly, fetchStatsCategory } from '../api';
import type { StatsOverview, MonthlyStat, CategoryStat } from '../types';

export default function Dashboard() {
  const [overview, setOverview] = useState<StatsOverview | null>(null);
  const [monthly, setMonthly] = useState<MonthlyStat[]>([]);
  const [categoryStats, setCategoryStats] = useState<CategoryStat[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchStatsOverview(),
      fetchStatsMonthly(),
      fetchStatsCategory(),
    ]).then(([ov, mo, ca]) => {
      setOverview(ov);
      setMonthly(mo);
      setCategoryStats(ca);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  if (!overview || overview.total_count === 0) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: 60, color: '#999' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📊</div>
          <div style={{ fontSize: 18, marginBottom: 8 }}>暂无数据</div>
          <div>请先导入交易流水，系统将自动生成统计分析</div>
        </div>
      </Card>
    );
  }

  const formatMoney = (v: number) => `¥${v.toLocaleString()}`;

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总支出"
              value={overview?.total_expense ?? 0}
              precision={2}
              prefix={<ArrowUpOutlined />}
              suffix="元"
              valueStyle={{ color: '#cf1322' }}
              formatter={(v) => formatMoney(Number(v))}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总收入"
              value={overview?.total_income ?? 0}
              precision={2}
              prefix={<ArrowDownOutlined />}
              suffix="元"
              valueStyle={{ color: '#389e0d' }}
              formatter={(v) => formatMoney(Number(v))}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="本月支出"
              value={overview?.month_expense ?? 0}
              precision={2}
              prefix={<WalletOutlined />}
              suffix="元"
              valueStyle={{ color: '#cf1322' }}
              formatter={(v) => formatMoney(Number(v))}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="收支结余"
              value={overview?.balance ?? 0}
              precision={2}
              prefix={<DollarOutlined />}
              suffix="元"
              valueStyle={{ color: (overview?.balance ?? 0) >= 0 ? '#389e0d' : '#cf1322' }}
              formatter={(v) => formatMoney(Number(v))}
            />
          </Card>
        </Col>
      </Row>

      {/* 月度趋势 */}
      <Card title="月度收支趋势" style={{ marginBottom: 24 }}>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={monthly}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip formatter={(v: any) => `¥${Number(v).toLocaleString()}`} />
            <Legend />
            <Bar dataKey="expense" name="支出" fill="#cf1322" radius={[4, 4, 0, 0]} />
            <Bar dataKey="income" name="收入" fill="#389e0d" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* 分类分布 */}
      <Card title="支出分类排行 (Top 8)">
        <Row gutter={[16, 16]}>
          {categoryStats.map((cat, i) => (
            <Col xs={24} sm={12} md={6} key={i}>
              <Card size="small" hoverable>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 18, fontWeight: 500 }}>
                    {cat.icon} {cat.name}
                  </span>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ color: '#cf1322', fontWeight: 600 }}>
                      ¥{cat.amount.toLocaleString()}
                    </div>
                    <div style={{ fontSize: 12, color: '#999' }}>
                      {cat.count} 笔
                    </div>
                  </div>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>
    </div>
  );
}
