// Renders index.html frame-by-frame with Playwright and pipes PNGs into ffmpeg.
// Usage:
//   node render.mjs frames out.mp4 [fps]        -> silent video
//   node render.mjs stills outdir t1 t2 ...     -> PNG stills at given times
//   node render.mjs meta meta.json              -> timeline (duration, sfx, captions)
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';

// Playwright is resolved via require() so a globally installed copy works too.
const { chromium } = createRequire(import.meta.url)('playwright');
const here = path.dirname(fileURLToPath(import.meta.url));
const [mode, out, ...rest] = process.argv.slice(2);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
await page.goto(pathToFileURL(path.join(here, 'index.html')).href + '?render=1');
await page.evaluate(() => document.fonts.ready);
const stage = page.locator('#stage');

if (mode === 'meta') {
  const meta = await page.evaluate(() => ({ total: window.TOTAL, sfx: window.SFX, captions: window.CAPTIONS }));
  writeFileSync(out, JSON.stringify(meta, null, 1));
} else if (mode === 'stills') {
  mkdirSync(out, { recursive: true });
  for (const t of rest) {
    await page.evaluate(t => window.renderAt(t), +t);
    await stage.screenshot({ path: path.join(out, `t${String(t).padStart(6, '0')}.png`) });
  }
} else if (mode === 'frames') {
  const fps = +(rest[0] || 24);
  const total = await page.evaluate(() => window.TOTAL);
  const n = Math.round(total * fps);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < n; i++) {
    await page.evaluate(t => window.renderAt(t), i / fps);
    const buf = await stage.screenshot({ type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 240 === 0) console.log(`frame ${i}/${n}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
}
await browser.close();
