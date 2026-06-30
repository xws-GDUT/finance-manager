/**
 * Cloudflare Workers — Render 防休眠脚本
 * 每 10 分钟 ping 一次 Render 服务，防止免费层休眠。
 */
const SERVICES = [
  { name: 'finance-manager-api', url: 'https://finance-manager-0j5p.onrender.com/api/accounts', method: 'GET' },
  { name: 'finance-manager-web', url: 'https://finance-manager-web-o2hk.onrender.com', method: 'GET' },
];

async function pingAll() {
  const results = [];
  for (const svc of SERVICES) {
    const start = Date.now();
    try {
      const resp = await fetch(svc.url, { method: svc.method });
      const elapsed = Date.now() - start;
      console.log(`  ${svc.name}: ${resp.status} (${elapsed}ms)`);
      results.push({ name: svc.name, status: resp.status, time: elapsed });
    } catch (err) {
      console.log(`  ${svc.name}: ERROR - ${err.message}`);
      results.push({ name: svc.name, status: 0, time: Date.now() - start, error: err.message });
    }
  }
  return results;
}

export default {
  async fetch(request) {
    const results = await pingAll();
    return new Response(JSON.stringify(results, null, 2), {
      headers: { 'Content-Type': 'application/json' },
    });
  },
  async scheduled(event) {
    console.log(`[${new Date().toISOString()}] Keepalive ping...`);
    await pingAll();
  },
};
