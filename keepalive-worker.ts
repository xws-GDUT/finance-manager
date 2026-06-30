/**
 * Cloudflare Workers — Render 防休眠脚本
 * 
 * 每 10 分钟 ping 一次 Render 服务，防止免费层休眠。
 * 部署到 Cloudflare Workers 后，使用 Cron Trigger 定时执行。
 *
 * 部署步骤：
 * 1. npm install -g wrangler
 * 2. wrangler login
 * 3. wrangler deploy
 * 4. 在 Cloudflare Dashboard → Workers → Triggers → 添加 Cron: */10 * * * *
 */

// 需要保持活跃的服务列表
const SERVICES = [
  {
    name: 'finance-manager-api',
    url: 'https://finance-manager-0j5p.onrender.com/api/accounts',
    method: 'GET',
  },
  {
    name: 'finance-manager-web',
    url: 'https://finance-manager-web-o2hk.onrender.com',
    method: 'GET',
  },
];

export default {
  // HTTP 触发（手动测试用）
  async fetch(request: Request): Promise<Response> {
    const results = await pingAll();
    return new Response(JSON.stringify(results, null, 2), {
      headers: { 'Content-Type': 'application/json' },
    });
  },

  // Cron 触发
  async scheduled(event: ScheduledEvent): Promise<void> {
    console.log(`[${new Date().toISOString()}] Keepalive ping...`);
    await pingAll();
  },
};

async function pingAll(): Promise<Array<{ name: string; status: number; time: number }>> {
  const results = [];
  for (const svc of SERVICES) {
    const start = Date.now();
    try {
      const resp = await fetch(svc.url, { method: svc.method });
      const elapsed = Date.now() - start;
      console.log(`  ${svc.name}: ${resp.status} (${elapsed}ms)`);
      results.push({ name: svc.name, status: resp.status, time: elapsed });
    } catch (err: any) {
      console.log(`  ${svc.name}: ERROR - ${err.message}`);
      results.push({ name: svc.name, status: 0, time: Date.now() - start, error: err.message });
    }
  }
  return results;
}
