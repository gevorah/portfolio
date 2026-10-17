const noise = `
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

export const PLANET_KIND = { umbral: 0, terra: 1, giant: 2, moon: 3 } as const;

export const planetFragment = `
uniform mat4 modelMatrix;
uniform vec3 uSunPos;
uniform vec3 uAtmosphere;
uniform float uAtmosphereStrength;
uniform float uRecede;
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
float terrain(vec3 p) {
  vec3 q = p * 1.05 + uSeed;
  float warp = fbm(q * 0.7, 2);
  return fbm(q + warp * 0.35, 5) - 0.03;
}

Surface surface(vec3 N, vec3 L) {
  vec3 p = vObj;
  float h = terrain(p);
  vec3 t1 = normalize(cross(p, vec3(0.0, 1.0, 0.001)));
  vec3 t2 = cross(p, t1);
  float e = 0.012;
  float h1 = terrain(normalize(p + t1 * e));
  float h2 = terrain(normalize(p + t2 * e));
  float land = smoothstep(0.0, 0.012, h);
  vec3 sea = mix(uColorA, uColorB, smoothstep(-0.16, 0.0, h) * 0.85);
  float relief = smoothstep(0.02, 0.36, h);
  vec3 ground = mix(uColorC, uColorD, relief);
  ground = mix(ground, ground * vec3(0.62, 0.78, 0.60), smoothstep(0.0, 0.10, h) * (1.0 - relief) * 0.55);
  vec3 albedo = mix(sea, ground, land);
  float ice = smoothstep(0.84, 0.91, abs(p.y) + 0.05 * h);
  albedo = mix(albedo, vec3(0.93, 0.91, 0.94), ice);
  vec3 objNormal = normalize(p - land * 0.3 * ((h1 - h) * t1 + (h2 - h) * t2) / e);
  vec3 normal = normalize(mat3(modelMatrix) * objNormal);
  float clouds = smoothstep(0.22, 0.62, fbm(p * vec3(1.6, 3.4, 1.6) + vec3(uTime * 0.01, 0.0, uSeed.x), 4));
  albedo = mix(albedo, vec3(0.96, 0.93, 0.92), clouds * 0.72);
  return Surface(albedo, mix(normal, N, clouds), 0.45 * (1.0 - land) * (1.0 - clouds), 70.0, 1.0);
}
#endif

#if KIND == 2
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

#if KIND == 3
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
  color *= mix(1.0, 0.36, uRecede);
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
uniform float uRecede;

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

  float alpha = density * edges * 0.82;
  color *= (0.12 + 0.88 * shadow) * mix(1.0, 0.5, uRecede);
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

varying vec3 vColor;
varying float vPhase;

void main() {
  float d = length(gl_PointCoord - 0.5) * 2.0;
  float core = 1.0 - smoothstep(uCore * 0.55, uCore, d);
  float glow = pow(max(1.0 - d, 0.0), 2.6) * uGlow;
  gl_FragColor = vec4(vColor * min(core + glow, 1.0) * uOpacity * vPhase, 1.0);
  #include <colorspace_fragment>
}
`;

export const threadVertex = `
attribute float aProgress;
attribute float aWeight;

varying float vProgress;
varying float vWeight;

void main() {
  vProgress = aProgress;
  vWeight = aWeight;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

export const threadFragment = `
uniform float uDraw;
uniform float uOpacity;
uniform vec3 uColor;

varying float vProgress;
varying float vWeight;

void main() {
  float drawn = 1.0 - smoothstep(uDraw - 0.04, uDraw, vProgress);
  gl_FragColor = vec4(uColor * drawn * vWeight * uOpacity, 1.0);
  #include <colorspace_fragment>
}
`;
