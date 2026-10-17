const noise = `
// Simplex 3D noise: permute, taylorInvSqrt and snoise.
// Copyright (C) 2011 Ashima Arts. All rights reserved.
// Author: Ian McEwan, Ashima Arts. Maintainer: Stefan Gustavson.
// Distributed under the MIT License. Full notice: /licenses/webgl-noise.txt
// https://github.com/stegu/webgl-noise
vec4 permute(vec4 x) { return mod(((x * 34.0) + 1.0) * x, 289.0); }
vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

float snoise(vec3 v) {
  const vec2 C = vec2(1.0 / 6.0, 1.0 / 3.0);
  const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
  vec3 i = floor(v + dot(v, C.yyy));
  vec3 x0 = v - i + dot(i, C.xxx);
  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min(g.xyz, l.zxy);
  vec3 i2 = max(g.xyz, l.zxy);
  vec3 x1 = x0 - i1 + C.xxx;
  vec3 x2 = x0 - i2 + C.yyy;
  vec3 x3 = x0 - D.yyy;
  i = mod(i, 289.0);
  vec4 p = permute(permute(permute(
    i.z + vec4(0.0, i1.z, i2.z, 1.0))
    + i.y + vec4(0.0, i1.y, i2.y, 1.0))
    + i.x + vec4(0.0, i1.x, i2.x, 1.0));
  float n_ = 1.0 / 7.0;
  vec3 ns = n_ * D.wyz - D.xzx;
  vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_);
  vec4 x = x_ * ns.x + ns.yyyy;
  vec4 y = y_ * ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);
  vec4 b0 = vec4(x.xy, y.xy);
  vec4 b1 = vec4(x.zw, y.zw);
  vec4 s0 = floor(b0) * 2.0 + 1.0;
  vec4 s1 = floor(b1) * 2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));
  vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
  vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;
  vec3 p0 = vec3(a0.xy, h.x);
  vec3 p1 = vec3(a0.zw, h.y);
  vec3 p2 = vec3(a1.xy, h.z);
  vec3 p3 = vec3(a1.zw, h.w);
  vec4 norm = taylorInvSqrt(vec4(dot(p0, p0), dot(p1, p1), dot(p2, p2), dot(p3, p3)));
  p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
  vec4 m = max(0.6 - vec4(dot(x0, x0), dot(x1, x1), dot(x2, x2), dot(x3, x3)), 0.0);
  m = m * m;
  return 42.0 * dot(m * m, vec4(dot(p0, x0), dot(p1, x1), dot(p2, x2), dot(p3, x3)));
}

float fbm(vec3 p, int octaves) {
  float sum = 0.0;
  float amp = 0.5;
  for (int i = 0; i < 6; i++) {
    if (i >= octaves) break;
    sum += amp * snoise(p);
    p = p * 2.03 + 17.1;
    amp *= 0.5;
  }
  return sum;
}
`;

export const bodyVertex = `
varying vec3 vObj;
varying vec3 vNormalW;
varying vec3 vPosW;
varying vec2 vUv;

void main() {
  vObj = normalize(position);
  vUv = uv;
  vec4 world = modelMatrix * vec4(position, 1.0);
  vPosW = world.xyz;
  vNormalW = normalize(mat3(modelMatrix) * normal);
  gl_Position = projectionMatrix * viewMatrix * world;
}
`;

export const PLANET_KIND = { umbral: 0, giant: 1, moon: 2 } as const;

export const planetFragment = `
uniform mat4 modelMatrix;
uniform vec3 uSunPos;
uniform vec3 uAtmosphere;
uniform float uAtmosphereStrength;
uniform float uRecede;
uniform float uVeil;
uniform float uHover;
uniform float uTime;
uniform vec3 uSeed;
uniform vec3 uColorA;
uniform vec3 uColorB;
uniform vec3 uColorC;
uniform vec3 uColorD;
uniform sampler2D uAlbedo;
uniform sampler2D uData;
uniform vec3 uRingNormal;
uniform vec2 uRingRadii;
uniform vec3 uCenter;

varying vec3 vObj;
varying vec3 vNormalW;
varying vec3 vPosW;
varying vec2 vUv;

${noise}

struct Surface {
  vec3 albedo;
  vec3 normal;
  float specular;
  float gloss;
  float shadow;
};

vec3 bumpFromDerivatives(vec3 N, float dBx, float dBy, float strength) {
  vec3 sigmaX = dFdx(vPosW);
  vec3 sigmaY = dFdy(vPosW);
  vec3 r1 = cross(sigmaY, N);
  vec3 r2 = cross(N, sigmaX);
  float det = dot(sigmaX, r1);
  vec3 grad = sign(det) * (dBx * r1 + dBy * r2);
  return normalize(abs(det) * N - strength * grad);
}

#if KIND == 0
Surface surface(vec3 N, vec3 L) {
  vec3 data = texture2D(uData, vUv).rgb;
  vec3 albedo = texture2D(uAlbedo, vUv).rgb;
  float clouds = data.b;
  float land = clamp(data.g - clouds * 0.9, 0.0, 1.0);
  vec2 du = dFdx(vUv);
  vec2 dv = dFdy(vUv);
  float h = data.r;
  float dBx = texture2D(uData, vUv + du).r - h;
  float dBy = texture2D(uData, vUv + dv).r - h;
  vec3 normal = bumpFromDerivatives(N, dBx, dBy, 9.0 * smoothstep(0.05, 0.4, land));
  albedo = mix(albedo, vec3(0.88, 0.89, 0.93), clouds * 0.88);
  float water = 1.0 - clamp(data.g, 0.0, 1.0);
  return Surface(albedo, normal, 0.55 * water, 90.0, 1.0);
}
#endif

#if KIND == 1
Surface surface(vec3 N, vec3 L) {
  vec3 p = vObj;
  float warp = fbm(p * vec3(1.3, 3.2, 1.3) + uSeed, 3);
  float lat = p.y + warp * 0.14;
  float flow = fbm(vec3(p.x * 1.1, lat * 5.5, p.z * 1.1) + warp * 0.8 + vec3(uTime * 0.006, 0.0, 0.0), 4);
  float belts = 0.5 + 0.5 * sin(lat * 8.5 + flow * 2.6);
  vec3 albedo = mix(uColorA, uColorB, smoothstep(0.15, 0.85, belts));
  albedo = mix(albedo, uColorC, smoothstep(0.1, 0.45, flow) * 0.65);
  vec3 stormCenter = normalize(vec3(0.62, -0.28, 0.73));
  float storm = smoothstep(0.26, 0.05, distance(p * vec3(1.0, 1.9, 1.0), stormCenter * vec3(1.0, 1.9, 1.0)));
  albedo = mix(albedo, uColorD, storm * (0.55 + 0.45 * flow));

  float shadow = 1.0;
  float denom = dot(L, uRingNormal);
  if (abs(denom) > 0.001) {
    float t = dot(uCenter - vPosW, uRingNormal) / denom;
    if (t > 0.0) {
      float r = length(vPosW + L * t - uCenter);
      float inside = smoothstep(uRingRadii.x, uRingRadii.x * 1.04, r) * (1.0 - smoothstep(uRingRadii.y * 0.97, uRingRadii.y, r));
      shadow = 1.0 - 0.55 * inside;
    }
  }
  return Surface(albedo, N, 0.0, 1.0, shadow);
}
#endif

#if KIND == 2
Surface surface(vec3 N, vec3 L) {
  float tone = 0.78 + 0.3 * fbm(vObj * 3.0 + uSeed, 3);
  return Surface(uColorA * tone, N, 0.0, 1.0, 1.0);
}
#endif

void main() {
  vec3 N = normalize(vNormalW);
  vec3 L = normalize(uSunPos - vPosW);
  vec3 V = normalize(cameraPosition - vPosW);
  Surface s = surface(N, L);

  float ndl = dot(s.normal, L);
  float geomNdl = dot(N, L);
  float diffuse = smoothstep(-0.08, 1.0, ndl) * s.shadow;
  vec3 sunlight = vec3(1.06, 0.97, 0.88);
  vec3 ambient = vec3(0.040, 0.046, 0.085);
  vec3 color = s.albedo * (sunlight * diffuse * 1.7 + ambient);

  float terminator = exp(-pow(geomNdl / 0.17, 2.0));
  color += s.albedo * vec3(0.32, 0.11, 0.22) * terminator * 0.42;

  vec3 H = normalize(L + V);
  float highlight = pow(max(dot(s.normal, H), 0.0), s.gloss) * s.specular * step(0.0, geomNdl);
  color += vec3(1.0, 0.92, 0.80) * highlight * s.shadow;

  float fresnel = pow(1.0 - max(dot(N, V), 0.0), 3.2);
  float lit = smoothstep(-0.3, 0.45, geomNdl);
  color += uAtmosphere * fresnel * (uAtmosphereStrength * (0.12 + 0.88 * lit) + uHover * 0.55);

  color = 1.0 - exp(-color * 1.25);
  color *= mix(1.0, 0.15, uRecede) * (1.0 - 0.82 * uVeil);
  gl_FragColor = vec4(color, 1.0);
  #include <colorspace_fragment>
}
`;

export const haloFragment = `
uniform vec3 uSunPos;
uniform vec3 uColor;
uniform vec3 uCenter;
uniform float uRadius;
uniform float uExtent;
uniform float uStrength;

varying vec3 vPosW;

void main() {
  vec3 ray = normalize(vPosW - cameraPosition);
  vec3 toCenter = uCenter - cameraPosition;
  vec3 closest = cameraPosition + ray * dot(toCenter, ray);
  float impact = length(closest - uCenter) / uRadius;
  float glow = 1.0 - smoothstep(1.0, uExtent, impact);
  glow *= smoothstep(0.93, 1.0, impact);
  vec3 limb = normalize(closest - uCenter);
  float lit = smoothstep(-0.35, 0.5, dot(limb, normalize(uSunPos - uCenter)));
  gl_FragColor = vec4(uColor * glow * glow * lit * uStrength, 1.0);
  #include <colorspace_fragment>
}
`;

export const ringVertex = `
varying vec3 vPosW;
varying vec3 vLocal;

void main() {
  vLocal = position;
  vec4 world = modelMatrix * vec4(position, 1.0);
  vPosW = world.xyz;
  gl_Position = projectionMatrix * viewMatrix * world;
}
`;

export const ringFragment = `
uniform vec3 uSunPos;
uniform vec3 uCenter;
uniform float uPlanetRadius;
uniform vec2 uRadii;
uniform vec3 uColorA;
uniform vec3 uColorB;
uniform float uOpacity;
uniform float uRecede;
uniform float uVeil;

varying vec3 vPosW;
varying vec3 vLocal;

void main() {
  float r = (length(vLocal.xy) - uRadii.x) / (uRadii.y - uRadii.x);
  float lanes = 0.5 + 0.28 * sin(r * 34.0) + 0.22 * sin(r * 91.0 + 1.3);
  float gap = 1.0 - smoothstep(0.02, 0.0, abs(r - 0.56)) * 0.9;
  float density = clamp(lanes, 0.0, 1.0) * gap;
  float edges = smoothstep(0.0, 0.05, r) * (1.0 - smoothstep(0.92, 1.0, r));
  vec3 color = mix(uColorA, uColorB, smoothstep(0.2, 0.9, r + 0.15 * sin(r * 20.0)));

  vec3 L = normalize(uSunPos - vPosW);
  vec3 toCenter = uCenter - vPosW;
  float along = dot(toCenter, L);
  float miss = length(toCenter - L * along);
  float shadow = along > 0.0 ? smoothstep(uPlanetRadius * 0.94, uPlanetRadius * 1.04, miss) : 1.0;

  float alpha = density * edges * uOpacity;
  color *= (0.12 + 0.88 * shadow) * mix(1.0, 0.2, uRecede);
  alpha *= 1.0 - 0.85 * uVeil;
  gl_FragColor = vec4(color, alpha);
  #include <colorspace_fragment>
}
`;

export const sunFragment = `
uniform float uTime;
uniform float uRecede;

varying vec3 vObj;
varying vec3 vNormalW;
varying vec3 vPosW;

${noise}

void main() {
  vec3 V = normalize(cameraPosition - vPosW);
  float facing = max(dot(normalize(vNormalW), V), 0.0);
  float cells = fbm(vObj * 3.4 + vec3(0.0, uTime * 0.03, 0.0), 4);
  float flares = fbm(vObj * 8.0 - vec3(uTime * 0.04, 0.0, 0.0), 3);
  vec3 core = vec3(1.0, 0.93, 0.74);
  vec3 mid = vec3(0.98, 0.69, 0.42);
  vec3 limb = vec3(0.80, 0.36, 0.34);
  vec3 color = mix(limb, mid, smoothstep(0.0, 0.55, facing));
  color = mix(color, core, smoothstep(0.45, 1.0, facing));
  color *= 0.92 + 0.22 * cells + 0.1 * flares;
  color *= 1.25 * mix(1.0, 0.72, uRecede);
  gl_FragColor = vec4(color, 1.0);
  #include <colorspace_fragment>
}
`;

export const pointsVertex = `
attribute float aSize;
attribute vec3 aColor;
attribute float aPhase;

uniform float uPixelRatio;
uniform float uFocalPx;
uniform float uTime;
uniform float uAttenuate;

varying vec3 vColor;
varying float vPhase;

void main() {
  vColor = aColor;
  vPhase = aPhase;
  vec4 view = modelViewMatrix * vec4(position, 1.0);
  gl_Position = projectionMatrix * view;
  float size = mix(aSize, aSize * uFocalPx / max(-view.z, 0.001), uAttenuate);
  gl_PointSize = max(size * uPixelRatio, 1.0);
}
`;

export const pointsFragment = `
uniform float uOpacity;
uniform float uCore;
uniform float uGlow;
uniform float uSpikes;

varying vec3 vColor;
varying float vPhase;

void main() {
  vec2 p = (gl_PointCoord - 0.5) * 2.0;
  float d = length(p);
  float core = 1.0 - smoothstep(uCore * 0.55, uCore, d);
  float glow = pow(max(1.0 - d, 0.0), 2.6) * uGlow;
  vec2 a = abs(p);
  float spikes = (exp(-a.y * 26.0) * pow(max(1.0 - a.x, 0.0), 3.0)
    + exp(-a.x * 26.0) * pow(max(1.0 - a.y, 0.0), 3.0)) * uSpikes * vPhase;
  gl_FragColor = vec4(vColor * min(core + glow + spikes, 1.0) * uOpacity * vPhase, 1.0);
  #include <colorspace_fragment>
}
`;

export const tailVertex = `
attribute vec2 aTail;

uniform float uLength;
uniform vec2 uWidth;
uniform float uBend;
uniform vec3 uLateral;

varying vec2 vTail;

void main() {
  float u = aTail.x;
  vec3 center = vec3(0.0, 0.0, u * uLength) + uLateral * (u * u * uLength * uBend);
  vec3 tangent = vec3(0.0, 0.0, uLength) + uLateral * (2.0 * u * uLength * uBend);
  vec3 worldCenter = (modelMatrix * vec4(center, 1.0)).xyz;
  vec3 worldTangent = normalize(mat3(modelMatrix) * tangent);
  vec3 side = normalize(cross(worldTangent, normalize(cameraPosition - worldCenter)));
  float width = 1.35 * (uWidth.x * (0.45 + 0.55 * sqrt(u)) + uWidth.y * u * (1.0 - 0.4 * u));
  vTail = aTail;
  gl_Position = projectionMatrix * viewMatrix * vec4(worldCenter + side * aTail.y * width, 1.0);
}
`;

export const tailFragment = `
uniform float uTime;
uniform float uOpacity;
uniform float uSeed;
uniform float uSkew;
uniform float uFade;
uniform float uDiffuse;
uniform float uStreaks;
uniform float uWarmth;
uniform vec3 uHead;
uniform vec3 uMid;
uniform vec3 uOuter;
uniform vec3 uWarm;

varying vec2 vTail;

${noise}

const int STREAMS = 6;

float hash(float n) {
  return fract(sin(n) * 43758.5453);
}

void main() {
  float u = vTail.x;
  float v = vTail.y * 1.35;
  float flow = uTime * 0.012;
  float w = v - uSkew - 0.12 * snoise(vec3(u * 1.2 - flow, uSeed, 0.5)) * u;

  float envelope = exp(-pow(w / (w > 0.0 ? 0.56 : 0.42), 2.0));
  float patches = 0.5 + 0.5 * fbm(vec3(w * 4.0, u * 6.0 - flow * 2.0, uSeed + 3.0), 3);
  float dust = envelope * mix(0.35, 1.0, patches);

  float streams = 0.0;
  for (int k = 0; k < STREAMS; k++) {
    float id = float(k) + uSeed * 7.0;
    float primary = k == 0 ? 1.0 : 0.0;
    float spread = mix((hash(id * 1.7) - 0.5) * 1.5, 0.0, primary);
    float bend = (hash(id * 3.1) - 0.5) * 0.6;
    float offset = spread * smoothstep(0.0, 0.8, u) + bend * u * u
      + 0.1 * sin(u * 9.0 + id * 3.7 - flow * 6.0) * u;
    float sigma = (mix(mix(0.06, 0.14, hash(id * 5.3)), 0.16, primary) * (0.6 + 0.8 * u)
      + 0.3 * (1.0 - smoothstep(0.0, 0.3, u)))
      * (1.0 + 0.3 * sin(u * 6.5 + id * 5.1));
    float start = mix(0.02 + 0.25 * hash(id * 2.3), 0.04, primary);
    float reach = mix(0.45 + 0.5 * hash(id * 4.7), 1.0, primary);
    float presence = smoothstep(-0.1, 0.5, snoise(vec3(u * 4.5 - flow, id, 4.0)) + 0.1 + 0.35 * primary);
    float life = smoothstep(start, start + 0.08, u) * (1.0 - smoothstep(reach * 0.6, reach, u));
    float strength = mix(mix(0.35, 0.9, hash(id * 7.9)), 0.4, primary);
    streams += exp(-pow((w - offset) / sigma, 2.0)) * presence * life * strength;
  }

  float wisps = 0.5 + 0.5 * fbm(vec3(v * 3.0, u * 4.0 - flow * 2.0, uSeed + 9.0), 3);
  float along = smoothstep(0.0, 0.1, u) * exp(-u * uFade * 1.6)
    * mix(0.4, 1.0, smoothstep(0.05, 0.35, u))
    * (1.0 - smoothstep(0.6, 1.0, u + (wisps - 0.5) * 0.4));
  float rim = 1.0 - smoothstep(0.8, 1.0, abs(vTail.y));
  streams = (1.0 - exp(-streams * 1.2)) * mix(0.35, 1.0, envelope);
  float density = (dust * uDiffuse + streams * uStreaks) * along * rim;
  float light = 1.0 - exp(-density * 2.0);

  vec3 dustColor = mix(uMid, uOuter, smoothstep(0.1, 0.9, abs(w) * 0.8 + u * 0.5));
  vec3 streamColor = mix(uHead, uWarm, uWarmth * smoothstep(0.05, 0.5, u));
  float share = streams * uStreaks / max(streams * uStreaks + dust * uDiffuse, 0.0001);
  vec3 color = mix(mix(dustColor, streamColor, share), uHead, 1.0 - smoothstep(0.0, 0.15, u));

  gl_FragColor = vec4(color * light * uOpacity, 1.0);
  #include <colorspace_fragment>
}
`;

export const comaVertex = `
uniform float uSize;
uniform vec3 uAxis;

varying vec2 vOffset;
varying vec2 vTailDirection;

void main() {
  vec4 center = modelViewMatrix * vec4(0.0, 0.0, 0.0, 1.0);
  vec2 projected = (mat3(viewMatrix) * uAxis).xy;
  vTailDirection = projected / max(length(projected), 0.0001);
  vOffset = position.xy;
  center.xy += position.xy * uSize;
  gl_Position = projectionMatrix * center;
}
`;

export const comaFragment = `
uniform float uOpacity;

varying vec2 vOffset;
varying vec2 vTailDirection;

${noise}

void main() {
  float d = length(vOffset);
  float along = dot(vOffset, vTailDirection);
  float across = length(vOffset - vTailDirection * along);
  float trail = max(along, 0.0);
  vec2 shaped = vec2(min(along, 0.0) + trail * 0.6, across / (1.0 + trail * 0.8));
  float r = length(shaped);
  float grain = 0.5 + 0.5 * snoise(vec3(shaped * 6.0, 2.0));
  float nucleus = exp(-pow(d / 0.008, 2.0));
  float core = exp(-pow(r / 0.026, 2.0));
  float coma = exp(-pow(r / (0.07 * mix(0.9, 1.1, grain)), 1.8));
  float outer = exp(-pow(r / 0.13, 2.0)) * mix(0.75, 1.0, grain);
  vec3 color = vec3(1.0, 0.97, 0.96) * nucleus * 0.3
    + vec3(0.62, 0.6, 1.0) * core * 0.12
    + vec3(0.3, 0.3, 0.95) * coma * 0.26
    + vec3(0.2, 0.26, 0.88) * outer * 0.06;
  color = 1.0 - exp(-color * 1.3);
  color *= 1.0 - smoothstep(0.75, 1.0, d);
  gl_FragColor = vec4(color * uOpacity, 1.0);
  #include <colorspace_fragment>
}
`;

export const nebulaVertex = `
varying vec2 vPlane;

void main() {
  vPlane = position.xy;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

export const nebulaFragment = `
uniform float uOpacity;
uniform float uSeed;
uniform float uScale;
uniform vec3 uSources[3];
uniform vec3 uIndigo;
uniform vec3 uViolet;
uniform vec3 uBlue;
uniform vec3 uMagenta;
uniform vec3 uLavender;
uniform vec3 uPink;
uniform vec3 uWhite;
uniform vec3 uSoot;

varying vec2 vPlane;

${noise}

const float GAIN = 0.93;
const float PINK = 0.85;
const float WHITE = 0.12;
const float DUST = 1.1;
const float HALO = 0.6;

const vec2 BAND = vec2(0.85, -0.53);
const mat2 LANES = mat2(0.6, 0.8, -0.8, 0.6);

vec2 toBand(vec2 v) {
  return vec2(dot(v, BAND), dot(v, vec2(-BAND.y, BAND.x)));
}

#if LAYER == 0
const int FLOW = 1;
#else
const int FLOW = 2;
#endif

vec2 flow(vec2 q) {
  vec3 s = vec3(q * 0.9, 3.7);
  return vec2(fbm(s, FLOW), fbm(s + vec3(5.2, 1.3, 2.7), FLOW));
}

float envelope(vec2 p, vec2 w) {
  vec2 b = toBand(p);
  float r = length(b / vec2(1.45, 0.56)) + w.x * 0.32 + w.y * 0.2;
  return (1.0 - smoothstep(0.12, 1.0, r)) * smoothstep(-1.3, 0.15, b.x + w.y * 0.3);
}

float outskirts(vec2 q, vec2 w) {
  vec2 b = toBand(q - vec2(0.12, -0.05));
  float lobes = snoise(vec3(normalize(b + 1e-4) * 1.2, 8.3));
  vec2 reach = vec2(mix(1.25, 1.75, smoothstep(-0.5, 0.6, b.x)), mix(1.05, 1.15, smoothstep(-0.3, 0.6, b.y)));
  float r = length(b / reach) * (1.0 - 0.3 * lobes) + w.x * 0.35 + w.y * 0.2;
  return 1.0 - smoothstep(0.1, 1.0, r);
}

float falloff(vec2 d, float radius) {
  return 1.0 / (1.0 + dot(d, d) / (radius * radius));
}

float shadowAt(vec2 q) {
  vec2 lane = LANES * q;
  return smoothstep(0.05, 0.42, fbm(vec3(lane.x * 1.2 + 3.1, lane.y * 3.6 - 1.7, 21.0), 2));
}

float primaryLight = 0.0;

float light(vec2 q, vec2 w) {
  vec2 s0 = uSources[0].xy;
  vec2 d0 = q - s0;
#if LAYER == 1
  float shade = shadowAt(mix(q, s0, 0.45) + w * 0.12);
#else
  float shade = 0.3;
#endif
  float primary = (falloff(d0, 0.1) + 0.6 * exp(-length(toBand(d0) / vec2(1.0, 0.7)) * 2.2)) * exp(-2.0 * shade);
  primaryLight = primary;
  float secondary = 0.42 * falloff(q - uSources[1].xy, 0.2) + 0.26 * falloff(q - uSources[2].xy, 0.12);
  vec2 l = toBand(q - vec2(-0.5, 0.22) - w * 0.15);
  float ambient = 0.16 * exp(-length(l / vec2(0.55, 0.32)) * 1.6);
  return primary + secondary + ambient;
}

float stars(vec2 q, out float halo) {
  float core = 0.0;
  halo = 0.0;
  for (int i = 0; i < 3; i++) {
    vec2 d = q - uSources[i].xy;
    float size = i == 0 ? 1.0 : 0.6;
    float d2 = dot(d, d);
    core += size * exp(-d2 / (0.000036 * size));
    halo += size * size * size * exp(-d2 / (0.0011 * size * size));
  }
  return core;
}

float filaments(vec3 p) {
  float sum = 0.0;
  float weight = 1.0;
  float amp = 0.6;
  for (int i = 0; i < 3; i++) {
    float r = 1.0 - abs(snoise(p));
    r *= r;
    r *= r * weight;
    weight = clamp(r * 2.4, 0.0, 1.0);
    sum += r * amp;
    p = p * 2.3 + vec3(9.3, -4.1, 2.7);
    amp *= 0.8;
  }
  return min(sum * 1.6, 1.0);
}

float dustLanes(vec2 q, vec2 w) {
  vec2 lane = LANES * (q + w * 0.25);
  float drift = 0.5 * snoise(vec3(q * 1.3, 5.0));
  float field = fbm(vec3(lane.x * 1.2 + 3.1 + drift * 0.6, lane.y * 3.6 - 1.7 + drift * 0.4, 21.0), 3);
  return smoothstep(0.08, 0.42, field);
}

#if LAYER == 0
const float REACH = 0.8;
#else
const float REACH = 1.0;
#endif

void main() {
  vec2 p = vPlane;
  vec2 q = p * uScale;
#if LAYER == 1
  vec2 bound = toBand(p * REACH) / vec2(1.45, 0.56);
  if (dot(bound, bound) > 1.9 || bound.x < -1.35) {
#else
  vec2 bound = toBand(q - vec2(0.12, -0.05)) / vec2(2.3, 1.45);
  if (dot(bound, bound) > 1.0) {
#endif
    gl_FragColor = vec4(0.0);
    return;
  }
  float frame = 1.0 - smoothstep(0.78, 1.0, max(abs(p.x), abs(p.y)));
  vec2 w = flow(q);
#if LAYER == 0
  float env = max(envelope(q * 0.62, w), outskirts(q, w));
  if (env < 0.004) {
    gl_FragColor = vec4(0.0);
    return;
  }
  float L = light(q, w);
  float haze = 0.5 + 0.5 * fbm(vec3(q * 1.2 + w * 0.5, uSeed), 2);
  float wisps = filaments(vec3(toBand(q) * vec2(1.5, 2.1) + w * 0.9, uSeed + 5.0));
  float density = env * smoothstep(0.15, 0.7, haze) * (0.3 + 0.7 * wisps);
  vec3 color = mix(uIndigo, uBlue, haze);
  color = mix(color, uViolet, smoothstep(0.1, 0.8, L));
  gl_FragColor = vec4(color * density * (0.62 + 0.6 * L) * frame * uOpacity, 1.0);
#elif LAYER == 1
  float L = light(q, w);
  float shape = envelope(p, w);
  float outer = outskirts(q, w);
  float body = 0.5 + 0.5 * fbm(vec3(q * 1.7 + w * 0.6, uSeed), 3);
  float breaks = smoothstep(0.2, 0.75, 0.5 + 0.5 * snoise(vec3(q * 4.6 + w * 1.3, uSeed + 6.0)));
  float fil = filaments(vec3(toBand(q) * vec2(2.3, 2.7) + w * 0.75, uSeed + 2.0)) * mix(0.45, 1.0, breaks);
  float cells = 0.5 + 0.5 * fbm(vec3(q * 2.3 + w * 0.7, 11.0), 3);
  float hole = 1.0 - smoothstep(0.28, 0.55, cells);
  float shell = exp(-pow((cells - 0.52) / 0.06, 2.0));
  float nearCore = smoothstep(0.05, 0.6, L);
  float lane = dustLanes(q, w) * DUST * mix(0.35, 1.0, nearCore);
  float gas = smoothstep(0.08, 0.7, body);
  float strands = 0.4 + 0.6 * fil;
  float env = max(shape, 0.75 * outer);
  float before = env * gas * strands * (1.0 - hole * mix(0.3, 0.9, nearCore)) * (1.0 - 0.75 * lane);
  float fill = smoothstep(0.14, 0.45, L) * smoothstep(0.05, 0.4, body);
  float envFilled = max(shape, 0.95 * outer);
  float lanes = lane * mix(0.35, 1.0, cells);
  float pocket = 1.0 - smoothstep(0.12, 0.22, cells);
  float carve = max(hole * mix(0.25, 0.45, nearCore) * (1.0 - 0.5 * fil), pocket * 0.7);
  float filled = envFilled * (0.3 + 0.7 * gas) * strands * (1.0 - carve) * (1.0 - 0.75 * lanes * (1.0 - 0.75 * hole));
  float density = mix(before, max(filled, before), fill);
  float litDensity = before + mix(1.0, 0.35, smoothstep(0.25, 0.7, primaryLight)) * (density - before);
  float lit = litDensity * (0.3 + 1.55 * L) + shell * env * L * 0.3 * (1.0 - lanes);
  float t = 1.0 - exp(-lit * GAIN * 1.3);
  float hue = smoothstep(-0.35, 0.35, fbm(vec3(q * 1.3 + w, 17.0), 2));
  vec3 color = mix(uIndigo, uViolet, smoothstep(0.0, 0.25, t));
  color = mix(color, mix(uBlue, uMagenta, min(hue + 0.35 * nearCore, 1.0)), smoothstep(0.12, 0.45, t) * 0.9);
  vec3 bright = mix(mix(uLavender, uViolet, 0.4), uLavender, smoothstep(0.25, 0.7, fil));
  bright = mix(bright, uPink, smoothstep(0.38, 0.8, hue * 0.55 + cells * 0.6) * PINK);
  color = mix(color, bright, smoothstep(0.5, 0.82, t));
  color = mix(color, mix(uLavender, uPink, 0.45 + 0.45 * hue), smoothstep(0.3, 1.2, L) * HALO * smoothstep(0.0, 0.5, density) * (0.6 + 0.4 * breaks));
  color = mix(color, uWhite, smoothstep(0.82, 0.95, t) * WHITE);
  vec3 emitted = color * t * 1.25;
  float halo;
  float core = stars(q, halo);
  emitted += mix(uPink, uLavender, 0.5) * halo * 0.55 + uWhite * core * 1.6;
  gl_FragColor = vec4(emitted * frame * uOpacity, 1.0);
#else
  float env = max(envelope(p, w * 1.2), outskirts(q, w * 1.2));
  if (env < 0.004) {
    gl_FragColor = vec4(0.0);
    return;
  }
  float L = light(q, w);
  float lanes = dustLanes(q, w);
  float grain = 0.5 + 0.5 * fbm(vec3(q * 3.0 + w, uSeed), 2);
  float clumps = smoothstep(0.55, 0.8, grain);
  float rim = smoothstep(0.0, 0.45, env) * (1.0 - smoothstep(0.45, 0.95, env));
  float patchy = smoothstep(0.3, 0.75, grain);
  float near = smoothstep(0.14, 0.45, L);
  float veil = max((lanes * mix(mix(0.35, 0.16, near), 0.72, smoothstep(0.1, 0.8, L)) * mix(mix(0.6, 0.25, near), 1.0, patchy) + clumps * 0.3) * env, rim * lanes * mix(0.4, 0.22, near)) * DUST;
  vec3 color = mix(uSoot, uIndigo * 0.45, smoothstep(0.2, 1.0, L) * 0.6);
  gl_FragColor = vec4(color, veil * frame * uOpacity);
#endif
  #include <colorspace_fragment>
}
`;

export const threadVertex = `
attribute float aProgress;
attribute float aWeight;
attribute vec2 aKey;

varying float vProgress;
varying float vWeight;
varying vec2 vKey;

void main() {
  vProgress = aProgress;
  vWeight = aWeight;
  vKey = aKey;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

export const threadFragment = `
uniform float uDraw;
uniform float uOpacity;
uniform vec2 uFocus;
uniform vec3 uColor;
uniform vec3 uAccent;

varying float vProgress;
varying float vWeight;
varying vec2 vKey;

void main() {
  float drawn = 1.0 - smoothstep(uDraw - 0.04, uDraw, vProgress);
  float near = exp(-pow(distance(vKey, uFocus) / 0.22, 2.0));
  vec3 color = mix(uColor, uAccent, near * 0.7);
  gl_FragColor = vec4(color * drawn * vWeight * uOpacity * (0.5 + 1.2 * near), 1.0);
  #include <colorspace_fragment>
}
`;
