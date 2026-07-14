#!/usr/bin/env node
/**
 * 把 HTML 报告渲染成 PNG 图片(整页,不截断)。
 *
 * 用 Chrome DevTools Protocol (CDP) 直接控制 chrome 二进制,
 * 不依赖 puppeteer。chrome 来自 puppeteer 的浏览器缓存(已存在,无需下载)。
 *
 * 流程:启动 chrome --remote-debugging-port → 连 CDP → 打开页面 →
 *       查询实际页面高度 → captureScreenshot(captureBeyondViewport) → 输出 PNG。
 *
 * 用法:
 *   render-report.js <html文件路径> [输出png路径]
 *   render-report.js demo-report.html              # 输出 demo-report.png
 *   render-report.js demo-report.html out.png      # 输出 out.png
 *
 * stdout 放结果 json,错误走 stderr。
 */

const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');
// 用 Node 21+ 内置的全局 WebSocket,零依赖

// 找 chrome 内核二进制:系统 chrome 优先 → puppeteer 缓存兜底
function findChrome() {
  // 1. 系统 chrome:PATH 里找 + 常见安装路径
  const cmds = ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'chrome'];
  const systemPaths = [
    '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium', '/usr/bin/chromium-browser',
    '/opt/google/chrome/chrome',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  ];
  for (const c of cmds) {
    try {
      const which = require('child_process').execSync(`which ${c} 2>/dev/null`, {encoding:'utf8'}).trim();
      if (which) return which;
    } catch {}
  }
  for (const p of systemPaths) {
    if (fs.existsSync(p)) return p;
  }
  // 2. 兜底:puppeteer 下载的 chrome 缓存(如果用户装过 puppeteer)
  const home = process.env.HOME || '/home';
  const puppeteerGlob = `${home}/.cache/puppeteer/chrome`;
  if (fs.existsSync(puppeteerGlob)) {
    const versions = fs.readdirSync(puppeteerGlob).sort().reverse();
    for (const v of versions) {
      const bin = path.join(puppeteerGlob, v, 'chrome-linux64', 'chrome');
      if (fs.existsSync(bin)) return bin;
    }
  }
  return null;
}

function emitError(type, message, hint) {
  process.stderr.write(JSON.stringify({type, message, hint}) + '\n');
  process.exit(1);
}

async function getWsUrl(port) {
  // 轮询 /json/version 拿 websocket 调试地址
  for (let i = 0; i < 30; i++) {
    await new Promise(r => setTimeout(r, 200));
    try {
      const data = await new Promise((resolve, reject) => {
        http.get(`http://127.0.0.1:${port}/json/version`, res => {
          let body = '';
          res.on('data', c => body += c);
          res.on('end', () => resolve(JSON.parse(body)));
        }).on('error', reject);
      });
      if (data.webSocketDebuggerUrl) return data.webSocketDebuggerUrl;
    } catch {}
  }
  return null;
}

async function main() {
  const htmlPath = process.argv[2];
  const outPath = process.argv[3] || htmlPath.replace(/\.html?$/i, '') + '.png';
  if (!htmlPath) emitError('usage_error', '缺少 HTML 文件路径参数', '用法: render-report.js <html> [输出png]');

  const absHtml = path.resolve(htmlPath);
  if (!fs.existsSync(absHtml)) emitError('io_error', `HTML 文件不存在: ${absHtml}`, '检查路径');

  const chrome = findChrome();
  if (!chrome) emitError('env_error', '找不到 chrome 内核',
    '装系统 chrome 或 chromium(如 apt install chromium-browser),或 npm install puppeteer 会自动下载一个');

  if (typeof WebSocket === 'undefined') emitError('env_error', 'Node 版本太旧,无内置 WebSocket(需 Node 21+)', `当前: ${process.version}`);

  // 启动 chrome,临时 user-data-dir 避免污染
  const port = 9222 + Math.floor(Math.random() * 1000);
  const tmpProfile = `/tmp/nov-tarot-chrome-${port}`;
  const chromeProc = spawn(chrome, [
    '--headless=new', '--disable-gpu', '--no-sandbox',
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${tmpProfile}`,
    '--disable-extensions', '--disable-default-apps',
  ], {stdio: 'ignore'});

  let wsUrl;
  try {
    wsUrl = await getWsUrl(port);
    if (!wsUrl) emitError('runtime_error', 'chrome 启动后无法连接调试端口', '检查 chrome 是否能正常运行');

    // browser endpoint 不支持 Page 域,要先创建一个 tab,连 tab 的 ws
    // 用 HTTP PUT /json/new 创建 tab(新版 chrome 可能需要 about:blank 占位)
    const tabWsUrl = await new Promise((resolve, reject) => {
      const req = http.request({hostname: '127.0.0.1', port, path: '/json/new?file://blank', method: 'PUT'}, res => {
        let body = '';
        res.on('data', c => body += c);
        res.on('end', () => {
          try { resolve(JSON.parse(body).webSocketDebuggerUrl); } catch(e){ reject(e); }
        });
      });
      req.on('error', reject);
      req.end();
    });
    if (!tabWsUrl) emitError('runtime_error', '无法创建 tab', 'chrome 版本可能不支持 /json/new');

    const ws = new WebSocket(tabWsUrl);
    await new Promise((r, rej) => { ws.addEventListener('open', r); ws.addEventListener('error', rej); });

    let msgId = 0;
    const pending = new Map();
    ws.addEventListener('message', ev => {
      const msg = JSON.parse(ev.data);
      if (msg.id && pending.has(msg.id)) {
        pending.get(msg.id)(msg);
        pending.delete(msg.id);
      }
    });
    const send = (method, params = {}) => new Promise((resolve, reject) => {
      const id = ++msgId;
      pending.set(id, msg => msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result));
      ws.send(JSON.stringify({id, method, params}));
    });

    await send('Page.enable');

    // 用 file:// 加载
    const fileUrl = 'file://' + absHtml;
    await send('Page.navigate', {url: fileUrl});
    // 等页面加载(静态 HTML 很快)
    await new Promise(r => setTimeout(r, 800));

    // 拿实际页面尺寸
    const metrics = await send('Page.getLayoutMetrics');
    const { width, height } = metrics.cssContentSize || metrics.contentSize;
    // 给一点点 padding 防边缘截断
    await send('Emulation.setDeviceMetricsOverride', {
      width: Math.ceil(width), height: Math.ceil(height) + 20, deviceScaleFactor: 1, mobile: false
    });
    await new Promise(r => setTimeout(r, 300));

    // 整页截图
    const shot = await send('Page.captureScreenshot', {format: 'png', captureBeyondViewport: true});
    const buf = Buffer.from(shot.data, 'base64');
    fs.writeFileSync(outPath, buf);

    ws.close();
    process.stdout.write(JSON.stringify({ok: true, output: outPath, width: Math.ceil(width), height: Math.ceil(height) + 20, bytes: buf.length}) + '\n');
  } finally {
    chromeProc.kill('SIGKILL');
    try { require('child_process').execSync(`rm -rf ${tmpProfile}`, {stdio:'ignore'}); } catch {}
  }
}

main().catch(e => emitError('runtime_error', e.message, '查看 chrome 是否正常'));
