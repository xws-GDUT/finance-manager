import { useState, useEffect } from 'react';
import {
  Card, Upload, Table, message, Space, Tag, Progress,
} from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { importFile, fetchImportHistory } from '../api';
import type { ImportLog } from '../types';

const { Dragger } = Upload;

export default function Import() {
  const [uploading, setUploading] = useState(false);
  const [importHistory, setImportHistory] = useState<ImportLog[]>([]);
  const [lastResult, setLastResult] = useState<any>(null);

  useEffect(() => {
    fetchImportHistory().then(setImportHistory).catch(() => {});
  }, []);

  const handleSingleImport: UploadProps['customRequest'] = async (options) => {
    const file = options.file as File;
    setUploading(true);
    try {
      const result = await importFile(file);
      setLastResult(result);
      if (result.success) {
        message.success(`导入完成：${result.imported_rows} 条新记录，跳过 ${result.skipped_rows} 条`);
      } else {
        message.error(`导入失败：${result.errors?.[0] || '未知错误'}`);
      }
      fetchImportHistory().then(setImportHistory).catch(() => {});
    } catch (e: any) {
      const errMsg = e?.response?.data?.error || e?.response?.data?.detail || e.message || '未知错误';
      message.error(`导入失败：${errMsg}`);
    } finally {
      setUploading(false);
    }
  };

  const columns = [
    { title: '文件名', dataIndex: 'source_file', key: 'file', ellipsis: true },
    { title: '来源', dataIndex: 'source', key: 'source', width: 100 },
    { title: '总行数', dataIndex: 'total_rows', key: 'total', width: 80 },
    {
      title: '结果', key: 'result', width: 200,
      render: (_: unknown, r: ImportLog) => (
        <Space size={4}>
          <Tag color="green">导入 {r.imported_rows}</Tag>
          {r.skipped_rows > 0 && <Tag color="orange">跳过 {r.skipped_rows}</Tag>}
          {r.error_rows > 0 && <Tag color="red">错误 {r.error_rows}</Tag>}
        </Space>
      ),
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', width: 80,
      render: (s: string) => <Tag color={s === 'success' ? 'green' : 'orange'}>{s}</Tag>,
    },
    {
      title: '时间', dataIndex: 'created_at', key: 'time', width: 170,
      render: (v: string) => new Date(v).toLocaleString(),
    },
  ];

  return (
    <div>
      <Card title="流水导入" style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Dragger
            accept=".csv,.pdf,.xlsx"
            multiple
            customRequest={handleSingleImport}
            showUploadList={false}
            disabled={uploading}
          >
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">
              支持 CSV、PDF、XLSX 格式。系统自动识别来源（支付宝/微信/京东/美团/抖音/银行）。
            </p>
          </Dragger>

          {uploading && <Progress percent={99} status="active" />}

          {lastResult && (
            <Card size="small" title="最近导入结果">
              <Space wrap>
                <Tag color="blue">来源：{lastResult.source}</Tag>
                <Tag>总行数：{lastResult.total_rows}</Tag>
                <Tag color="green">导入：{lastResult.imported_rows}</Tag>
                <Tag color="orange">跳过：{lastResult.skipped_rows}</Tag>
                {lastResult.error_rows > 0 && <Tag color="red">错误：{lastResult.error_rows}</Tag>}
              </Space>
              {lastResult.errors?.length > 0 && (
                <div style={{ marginTop: 8, color: '#cf1322', fontSize: 12 }}>
                  {lastResult.errors.map((e: string, i: number) => <div key={i}>• {e}</div>)}
                </div>
              )}
            </Card>
          )}
        </Space>
      </Card>

      <Card title="导入历史">
        <Table
          columns={columns}
          dataSource={importHistory}
          rowKey="id"
          pagination={{ pageSize: 20, showTotal: (t) => `共 ${t} 条` }}
          size="small"
        />
      </Card>
    </div>
  );
}
