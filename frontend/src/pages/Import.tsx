import { useState, useEffect, useRef } from 'react';
import {
  Card, Upload, Table, message, Space, Tag, Button, Progress, Tooltip,
} from 'antd';
import {
  InboxOutlined, DeleteOutlined, ReloadOutlined, FileTextOutlined,
  FilePdfOutlined, FileExcelOutlined, CheckCircleFilled,
  CloseCircleFilled, LoadingOutlined,
} from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { importFile, fetchImportHistory } from '../api';
import type { ImportLog } from '../types';

const { Dragger } = Upload;

// 单个文件上传状态
type FileStatus = 'pending' | 'uploading' | 'success' | 'error';

interface UploadItem {
  uid: string;
  name: string;
  size: number;
  file?: File;             // 原始 File 对象，用于重试
  status: FileStatus;
  progress: number;        // 0-100
  result?: {
    source?: string;
    imported_rows?: number;
    skipped_rows?: number;
    error_rows?: number;
    errors?: string[];
  };
  errorMsg?: string;
  thumbUrl?: string;
  ext: string;
}

const getFileIcon = (ext: string) => {
  if (ext === 'pdf') return <FilePdfOutlined style={{ color: '#ff4d4f', fontSize: 40 }} />;
  if (ext === 'xlsx' || ext === 'xls') return <FileExcelOutlined style={{ color: '#52c41a', fontSize: 40 }} />;
  if (ext === 'csv') return <FileTextOutlined style={{ color: '#1890ff', fontSize: 40 }} />;
  return <FileTextOutlined style={{ color: '#999', fontSize: 40 }} />;
};

const formatSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
};

export default function Import() {
  const [fileList, setFileList] = useState<UploadItem[]>([]);
  const [importHistory, setImportHistory] = useState<ImportLog[]>([]);
  const [summary, setSummary] = useState({ total: 0, imported: 0, skipped: 0, errors: 0 });

  // 防止自动上传逻辑重复执行
  const pendingUidsRef = useRef<Set<string>>(new Set());

  // 加载历史记录
  useEffect(() => {
    fetchImportHistory().then(setImportHistory).catch(() => {});
  }, []);

  // 汇总统计
  useEffect(() => {
    const total = fileList.length;
    const imported = fileList.filter(f => f.status === 'success')
      .reduce((sum, f) => sum + (f.result?.imported_rows || 0), 0);
    const skipped = fileList.filter(f => f.status === 'success')
      .reduce((sum, f) => sum + (f.result?.skipped_rows || 0), 0);
    const errors = fileList.filter(f => f.status === 'success')
      .reduce((sum, f) => sum + (f.result?.error_rows || 0), 0);
    setSummary({ total, imported, skipped, errors });
  }, [fileList]);

  // 上传单个文件
  const uploadSingleFile = async (uid: string) => {
    const item = fileList.find(f => f.uid === uid);
    if (!item) return;

    setFileList(prev => prev.map(f =>
      f.uid === uid ? { ...f, status: 'uploading', progress: 0, errorMsg: undefined } : f
    ));

    try {
      // 模拟上传进度（axios 不暴露真实进度，使用增量模拟）
      const progressTimer = setInterval(() => {
        setFileList(prev => prev.map(f => {
          if (f.uid !== uid || f.status !== 'uploading') return f;
          if (f.progress >= 90) return f;
          return { ...f, progress: f.progress + 10 };
        }));
      }, 200);

      // 使用原始 File 对象（如果存在）或创建一个占位
      const result = item.file
        ? await importFile(item.file)
        : await importFile(new File([new Blob()], item.name, { type: 'application/octet-stream' }));

      clearInterval(progressTimer);

      setFileList(prev => prev.map(f =>
        f.uid === uid ? {
          ...f,
          status: result.success ? 'success' : 'error',
          progress: 100,
          result,
          errorMsg: result.success ? undefined : (result.errors?.[0] || '导入失败'),
        } : f
      ));

      // 刷新历史
      fetchImportHistory().then(setImportHistory).catch(() => {});
    } catch (e: any) {
      setFileList(prev => prev.map(f =>
        f.uid === uid ? {
          ...f,
          status: 'error',
          progress: 0,
          errorMsg: e?.response?.data?.error || e?.response?.data?.detail || e?.message || '导入失败',
        } : f
      ));
    }
  };

  // 选择文件后的处理
  const handleSelect: UploadProps['customRequest'] = (options) => {
    const file = options.file as File;
    const ext = (file.name.split('.').pop() || '').toLowerCase();
    const newItem: UploadItem = {
      uid: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
      name: file.name,
      size: file.size,
      file,
      status: 'pending',
      progress: 0,
      ext,
      thumbUrl: ['png', 'jpg', 'jpeg', 'gif'].includes(ext)
        ? URL.createObjectURL(file)
        : undefined,
    };

    setFileList(prev => {
      if (prev.some(f => f.name === newItem.name)) {
        message.warning(`文件已存在：${newItem.name}`);
        return prev;
      }
      // 标记为待上传，下次 effect 会触发上传
      pendingUidsRef.current.add(newItem.uid);
      return [...prev, newItem];
    });

    options.onSuccess?.({}, file);
  };

  // 监控 fileList 中的 pending 文件，自动开始上传
  useEffect(() => {
    const pending = fileList.filter(f =>
      f.status === 'pending' && pendingUidsRef.current.has(f.uid)
    );

    if (pending.length > 0) {
      pending.forEach(item => {
        // 从 ref 移除，避免重复触发
        pendingUidsRef.current.delete(item.uid);
        // 异步上传（不 await，让多个文件并发）
        uploadSingleFile(item.uid);
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fileList]);

  // 单个文件重试
  const handleRetry = async (uid: string) => {
    const item = fileList.find(f => f.uid === uid);
    if (!item) return;
    if (!item.file) {
      message.warning('请重新拖入文件以重试');
      return;
    }
    await uploadSingleFile(uid);
  };

  // 重试所有失败的文件
  const handleRetryAll = async () => {
    const failed = fileList.filter(f => f.status === 'error' && f.file);
    if (failed.length === 0) {
      message.warning('没有可重试的文件');
      return;
    }
    for (const item of failed) {
      await uploadSingleFile(item.uid);
    }
  };

  // 删除单个文件
  const handleRemove = (uid: string) => {
    setFileList(prev => {
      const item = prev.find(f => f.uid === uid);
      if (item?.thumbUrl) URL.revokeObjectURL(item.thumbUrl);
      pendingUidsRef.current.delete(uid);
      return prev.filter(f => f.uid !== uid);
    });
  };

  // 清空已完成的文件（仅清空 success 的，error 保留以便重试）
  const handleClearCompleted = () => {
    setFileList(prev => {
      prev.filter(f => f.thumbUrl).forEach(f => {
        if (f.thumbUrl) URL.revokeObjectURL(f.thumbUrl);
      });
      return prev.filter(f => f.status !== 'success');
    });
    message.success('已清空已成功文件');
  };

  // 清空所有
  const handleClearAll = () => {
    fileList.forEach(f => {
      if (f.thumbUrl) URL.revokeObjectURL(f.thumbUrl);
    });
    pendingUidsRef.current.clear();
    setFileList([]);
  };

  // 统计
  const pendingCount = fileList.filter(f => f.status === 'pending' || f.status === 'uploading').length;
  const successCount = fileList.filter(f => f.status === 'success').length;
  const errorCount = fileList.filter(f => f.status === 'error').length;

  const historyColumns = [
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
      <Card
        title="流水导入"
        extra={
          fileList.length > 0 && (
            <Space wrap>
              {errorCount > 0 && (
                <Button
                  icon={<ReloadOutlined />}
                  onClick={handleRetryAll}
                  disabled={pendingCount > 0}
                >
                  重试失败 ({errorCount})
                </Button>
              )}
              {successCount > 0 && (
                <Button onClick={handleClearCompleted} disabled={pendingCount > 0}>
                  清空已完成
                </Button>
              )}
              <Button
                danger
                icon={<DeleteOutlined />}
                onClick={handleClearAll}
                disabled={pendingCount > 0}
              >
                清空列表
              </Button>
            </Space>
          )
        }
        style={{ marginBottom: 24 }}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Dragger
            accept=".csv,.pdf,.xlsx"
            multiple
            customRequest={handleSelect}
            showUploadList={false}
            beforeUpload={(file) => {
              const ext = (file.name.split('.').pop() || '').toLowerCase();
              const allowed = ['csv', 'pdf', 'xlsx'];
              if (!allowed.includes(ext)) {
                message.error(`不支持的文件格式: .${ext}，仅支持 .csv/.pdf/.xlsx`);
                return Upload.LIST_IGNORE;
              }
              return true;
            }}
          >
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">
              支持 CSV、PDF、XLSX 格式。可批量选择多文件。系统自动识别来源。
            </p>
          </Dragger>

          {fileList.length > 0 && (
            <Space size="middle" wrap>
              <Tag color="blue">总文件：{summary.total}</Tag>
              <Tag color="gold">处理中：{pendingCount}</Tag>
              <Tag color="green">已成功：{successCount}</Tag>
              <Tag color="red">已失败：{errorCount}</Tag>
              <Tag color="cyan">导入记录：{summary.imported}</Tag>
              {summary.skipped > 0 && <Tag color="orange">跳过：{summary.skipped}</Tag>}
              {summary.errors > 0 && <Tag color="volcano">错误行：{summary.errors}</Tag>}
            </Space>
          )}

          {fileList.length > 0 && (
            <div>
              {fileList.map((item) => {
                const isUploading = item.status === 'uploading';
                const isSuccess = item.status === 'success';
                const isError = item.status === 'error';

                let borderColor = '#d9d9d9';
                let backgroundColor = '#fafafa';
                let textColor = '#333';
                if (isUploading) {
                  borderColor = '#d9d9d9';
                  backgroundColor = '#fff';
                } else if (isSuccess) {
                  borderColor = '#52c41a';
                  backgroundColor = '#fff';
                } else if (isError) {
                  borderColor = '#ff4d4f';
                  backgroundColor = '#fff';
                  textColor = '#ff4d4f';
                }

                return (
                  <div
                    key={item.uid}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 16,
                      padding: '12px 16px',
                      marginBottom: 12,
                      border: `1px solid ${borderColor}`,
                      borderRadius: 8,
                      background: backgroundColor,
                      transition: 'all 0.2s',
                    }}
                  >
                    <div style={{ width: 64, height: 64, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      {item.thumbUrl ? (
                        <img
                          src={item.thumbUrl}
                          alt={item.name}
                          style={{ maxWidth: '100%', maxHeight: '100%', borderRadius: 4 }}
                        />
                      ) : (
                        getFileIcon(item.ext)
                      )}
                    </div>

                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: isUploading ? 4 : 0, flexWrap: 'wrap' }}>
                        <span style={{
                          fontSize: 14,
                          fontWeight: 500,
                          color: textColor,
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          maxWidth: 400,
                        }}>
                          {item.name}
                        </span>
                        <span style={{ fontSize: 12, color: '#999' }}>
                          {formatSize(item.size)}
                        </span>
                        {isSuccess && item.result && (
                          <Tag color="green" style={{ marginLeft: 4 }}>
                            {item.result.source} · 导入 {item.result.imported_rows} · 跳过 {item.result.skipped_rows}
                          </Tag>
                        )}
                        {isError && (
                          <Tooltip title={item.errorMsg || '导入失败'}>
                            <Tag color="red" style={{ marginLeft: 4 }}>失败</Tag>
                          </Tooltip>
                        )}
                      </div>

                      {isUploading && (
                        <Progress
                          percent={item.progress}
                          size="small"
                          status="active"
                          strokeColor="#1890ff"
                        />
                      )}

                      {isSuccess && item.result && item.result.error_rows! > 0 && (
                        <div style={{ fontSize: 12, color: '#fa8c16', marginTop: 2 }}>
                          其中 {item.result.error_rows} 行解析失败
                        </div>
                      )}

                      {isError && (
                        <div style={{ fontSize: 12, color: '#ff4d4f', marginTop: 2 }}>
                          <CloseCircleFilled style={{ marginRight: 4 }} />
                          {item.errorMsg || '导入失败'}
                        </div>
                      )}
                    </div>

                    <Space size="small">
                      {isUploading && <LoadingOutlined style={{ fontSize: 18, color: '#1890ff' }} />}
                      {isSuccess && <CheckCircleFilled style={{ fontSize: 18, color: '#52c41a' }} />}
                      {isError && (
                        <Tooltip title="重试">
                          <Button
                            type="text"
                            icon={<ReloadOutlined />}
                            onClick={() => handleRetry(item.uid)}
                          />
                        </Tooltip>
                      )}
                      <Tooltip title="删除">
                        <Button
                          type="text"
                          danger
                          icon={<DeleteOutlined />}
                          onClick={() => handleRemove(item.uid)}
                          disabled={isUploading}
                        />
                      </Tooltip>
                    </Space>
                  </div>
                );
              })}
            </div>
          )}
        </Space>
      </Card>

      <Card title="导入历史">
        <Table
          columns={historyColumns}
          dataSource={importHistory}
          rowKey="id"
          pagination={{ pageSize: 20, showTotal: (t) => `共 ${t} 条` }}
          size="small"
        />
      </Card>
    </div>
  );
}
