import { useState, useEffect } from 'react';
import { Card, Tree, Spin, Tag } from 'antd';
import type { DataNode } from 'antd/es/tree';
import { fetchCategories } from '../api';

export default function Categories() {
  const [treeData, setTreeData] = useState<DataNode[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCategories().then(cats => {
      const nodes: DataNode[] = cats.map(c => ({
        title: (
          <span>
            <span style={{ marginRight: 8 }}>{c.icon}</span>
            <span style={{ fontWeight: 500 }}>{c.name}</span>
            <Tag color={c.type === 'expense' ? 'red' : c.type === 'income' ? 'green' : 'blue'}
              style={{ marginLeft: 8, fontSize: 11 }}>
              {c.type === 'expense' ? '支出' : c.type === 'income' ? '收入' : '转账'}
            </Tag>
          </span>
        ),
        key: `cat-${c.id}`,
        children: c.children?.map(ch => ({
          title: (
            <span>
              <span style={{ marginRight: 4 }}>{ch.icon}</span>
              {ch.name}
            </span>
          ),
          key: `cat-${ch.id}`,
        })),
      }));
      setTreeData(nodes);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <Card title="分类管理">
      <Tree
        treeData={treeData}
        defaultExpandAll
        showLine={{ showLeafIcon: false }}
        style={{ fontSize: 15 }}
      />
    </Card>
  );
}
