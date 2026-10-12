// Renders a GLSL fragment shader to PNG in headless Chromium (SwiftShader).
// usage: node run.mjs <shader.frag> <out.png> <w> <h> [uniformsJSON]
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
const { chromium } = createRequire(import.meta.url)(process.env.PW_PATH || 'playwright');
const [frag, out, w = '1600', h = '1000', uni = '{}'] = process.argv.slice(2);
const src = fs.readFileSync(frag, 'utf8');
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: +w, height: +h } });
page.on('console', m => console.log('[page]', m.text()));
await page.setContent('<canvas id="c"></canvas>');
const t0 = Date.now();
const url = await page.evaluate(async ({ src, w, h, uni }) => {
  const c = document.getElementById('c'); c.width = w; c.height = h;
  const gl = c.getContext('webgl2', { preserveDrawingBuffer: true });
  if (!gl) return 'ERR no webgl2';
  const sh = (t, s) => { const o = gl.createShader(t); gl.shaderSource(o, s); gl.compileShader(o);
    if (!gl.getShaderParameter(o, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(o)); return o; };
  const p = gl.createProgram();
  gl.attachShader(p, sh(gl.VERTEX_SHADER, '#version 300 es\nin vec2 a;void main(){gl_Position=vec4(a,0,1);}'));
  gl.attachShader(p, sh(gl.FRAGMENT_SHADER, src));
  gl.linkProgram(p); gl.useProgram(p);
  const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,1,1]), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(p, 'a'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  gl.uniform2f(gl.getUniformLocation(p, 'R'), w, h);
  for (const [k, v] of Object.entries(uni)) {
    const l = gl.getUniformLocation(p, k); if (!l) continue;
    if (Array.isArray(v)) gl[`uniform${v.length}fv`](l, v); else gl.uniform1f(l, v);
  }
  gl.enable(gl.SCISSOR_TEST);
  const T = 100;
  for (let y = 0; y < h; y += T) {
    gl.scissor(0, y, w, T); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    gl.readPixels(0, y, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4)); // flush per tile
    await new Promise(r => setTimeout(r, 0));
  }
  return c.toDataURL('image/png');
}, { src, w: +w, h: +h, uni: JSON.parse(uni) });
if (url.startsWith('ERR')) { console.error(url); process.exit(1); }
fs.writeFileSync(out, Buffer.from(url.split(',')[1], 'base64'));
console.log(`rendered ${path.basename(out)} in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
await browser.close();
