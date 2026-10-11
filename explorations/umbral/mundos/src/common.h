// Núcleo compartido del trazador de Small Worlds.
//
// Un raymarcher de campos de distancia (SDF) muy pequeño: vectores, ruido,
// cámara, utilidades de iluminación y salida HDR en PFM. Cada mundo define su
// geometría y sus materiales en su propio archivo; este núcleo no sabe nada
// de planetas.
#pragma once
#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <functional>
#include <string>
#include <thread>
#include <vector>

// ------------------------------------------------------------------ vectores
struct v3 {
  float x, y, z;
  v3() : x(0), y(0), z(0) {}
  v3(float a) : x(a), y(a), z(a) {}
  v3(float a, float b, float c) : x(a), y(b), z(c) {}
  v3 operator+(const v3& o) const { return {x + o.x, y + o.y, z + o.z}; }
  v3 operator-(const v3& o) const { return {x - o.x, y - o.y, z - o.z}; }
  v3 operator*(const v3& o) const { return {x * o.x, y * o.y, z * o.z}; }
  v3 operator/(const v3& o) const { return {x / o.x, y / o.y, z / o.z}; }
  v3 operator*(float s) const { return {x * s, y * s, z * s}; }
  v3 operator/(float s) const { return {x / s, y / s, z / s}; }
  v3 operator-() const { return {-x, -y, -z}; }
  v3& operator+=(const v3& o) { x += o.x; y += o.y; z += o.z; return *this; }
  v3& operator*=(float s) { x *= s; y *= s; z *= s; return *this; }
  v3& operator*=(const v3& o) { x *= o.x; y *= o.y; z *= o.z; return *this; }
};
inline v3 operator*(float s, const v3& v) { return v * s; }
inline float dot(const v3& a, const v3& b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
inline v3 cross(const v3& a, const v3& b) {
  return {a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x};
}
inline float len(const v3& a) { return std::sqrt(dot(a, a)); }
inline v3 nrm(const v3& a) { float l = len(a); return l > 0 ? a / l : v3(0, 1, 0); }
inline float clampf(float x, float a, float b) { return x < a ? a : (x > b ? b : x); }
inline float sat(float x) { return clampf(x, 0.f, 1.f); }
inline float sq(float x) { return x * x; }
inline v3 sat(const v3& v) { return {sat(v.x), sat(v.y), sat(v.z)}; }
inline float mixf(float a, float b, float t) { return a + (b - a) * t; }
inline v3 mix(const v3& a, const v3& b, float t) { return a + (b - a) * t; }
inline float sstep(float a, float b, float x) {
  float t = sat((x - a) / (b - a));
  return t * t * (3 - 2 * t);
}
inline v3 vabs(const v3& a) { return {std::fabs(a.x), std::fabs(a.y), std::fabs(a.z)}; }
inline v3 vmax(const v3& a, float b) { return {std::max(a.x, b), std::max(a.y, b), std::max(a.z, b)}; }
inline float vmaxc(const v3& a) { return std::max(a.x, std::max(a.y, a.z)); }
inline v3 vexp(const v3& a) { return {std::exp(a.x), std::exp(a.y), std::exp(a.z)}; }
inline v3 reflect(const v3& i, const v3& n) { return i - n * (2 * dot(i, n)); }
inline float smin(float a, float b, float k) {
  float h = sat(0.5f + 0.5f * (b - a) / k);
  return mixf(b, a, h) - k * h * (1 - h);
}
inline float smax(float a, float b, float k) { return -smin(-a, -b, k); }

// Color desde hexadecimal, devuelto en lineal (aprox. gamma 2.2).
inline v3 hex(uint32_t c) {
  auto ch = [](uint32_t v) { return std::pow(v / 255.f, 2.2f); };
  return {ch((c >> 16) & 255), ch((c >> 8) & 255), ch(c & 255)};
}

// Rotación de v alrededor del eje unitario k (Rodrigues).
inline v3 rotAxis(const v3& v, const v3& k, float a) {
  float c = std::cos(a), s = std::sin(a);
  return v * c + cross(k, v) * s + k * (dot(k, v) * (1 - c));
}

// Base ortonormal a partir de un vector "arriba" n.
struct Frame {
  v3 t, b, n;
  Frame() {}
  Frame(v3 nn, v3 hint = v3(0, 1, 0)) {
    n = nrm(nn);
    if (std::fabs(dot(n, hint)) > 0.95f) hint = v3(1, 0, 0);
    t = nrm(cross(hint, n));
    b = cross(n, t);
  }
  v3 toLocal(const v3& p) const { return {dot(p, t), dot(p, b), dot(p, n)}; }
  v3 toWorld(const v3& p) const { return t * p.x + b * p.y + n * p.z; }
};

// -------------------------------------------------------------------- ruido
inline float hash1(float n) {
  float s = std::sin(n) * 43758.5453f;
  return s - std::floor(s);
}
inline uint32_t ihash(uint32_t x) {
  x ^= x >> 16; x *= 0x7feb352dU; x ^= x >> 15; x *= 0x846ca68bU; x ^= x >> 16;
  return x;
}
inline float h3(int x, int y, int z) {
  uint32_t h = ihash((uint32_t)x * 73856093u ^ ihash((uint32_t)y * 19349663u ^ ihash((uint32_t)z * 83492791u)));
  return (h & 0xffffff) / float(0xffffff);
}
inline float h2(int x, int y, int seed = 0) { return h3(x, y, seed * 7919 + 13); }

// Ruido de valor 3D con interpolación quíntica, en [-1, 1].
inline float vnoise(v3 p) {
  float fx = std::floor(p.x), fy = std::floor(p.y), fz = std::floor(p.z);
  int ix = (int)fx, iy = (int)fy, iz = (int)fz;
  float ux = p.x - fx, uy = p.y - fy, uz = p.z - fz;
  ux = ux * ux * ux * (ux * (ux * 6 - 15) + 10);
  uy = uy * uy * uy * (uy * (uy * 6 - 15) + 10);
  uz = uz * uz * uz * (uz * (uz * 6 - 15) + 10);
  float a = h3(ix, iy, iz), b = h3(ix + 1, iy, iz), c = h3(ix, iy + 1, iz), d = h3(ix + 1, iy + 1, iz);
  float e = h3(ix, iy, iz + 1), f = h3(ix + 1, iy, iz + 1), g = h3(ix, iy + 1, iz + 1), h = h3(ix + 1, iy + 1, iz + 1);
  float k0 = mixf(mixf(a, b, ux), mixf(c, d, ux), uy);
  float k1 = mixf(mixf(e, f, ux), mixf(g, h, ux), uy);
  return mixf(k0, k1, uz) * 2 - 1;
}
inline float fbm(v3 p, int oct = 5, float lac = 2.03f, float gain = 0.5f) {
  float s = 0, a = 0.5f, norm = 0;
  for (int i = 0; i < oct; i++) {
    s += a * vnoise(p);
    norm += a;
    p = p * lac + v3(1.7f, 9.2f, 3.1f);
    a *= gain;
  }
  return s / norm;
}
// Ruido de crestas (valores altos en las líneas).
inline float ridged(v3 p, int oct = 5) {
  float s = 0, a = 0.5f, norm = 0, w = 1;
  for (int i = 0; i < oct; i++) {
    float n = 1 - std::fabs(vnoise(p));
    n *= n * w;
    w = sat(n * 1.6f);
    s += a * n;
    norm += a;
    p = p * 2.07f + v3(4.3f, 1.1f, 7.7f);
    a *= 0.5f;
  }
  return s / norm;
}
// Voronoi 3D: devuelve F1, F2 y un id de celda.
struct Vor { float f1, f2; float id; v3 c; };
inline Vor voronoi(v3 p, float jitter = 0.85f) {
  v3 fp(std::floor(p.x), std::floor(p.y), std::floor(p.z));
  Vor r{9, 9, 0, v3(0)};
  for (int k = -1; k <= 1; k++)
    for (int j = -1; j <= 1; j++)
      for (int i = -1; i <= 1; i++) {
        int cx = (int)fp.x + i, cy = (int)fp.y + j, cz = (int)fp.z + k;
        v3 o(h3(cx, cy, cz), h3(cx + 11, cy + 3, cz + 5), h3(cx + 7, cy + 17, cz + 1));
        v3 c = v3((float)cx, (float)cy, (float)cz) + v3(0.5f) + (o - v3(0.5f)) * jitter;
        float d = len(c - p);
        if (d < r.f1) { r.f2 = r.f1; r.f1 = d; r.id = h3(cx, cy, cz + 99); r.c = c; }
        else if (d < r.f2) r.f2 = d;
      }
  return r;
}
// Voronoi 2D para patrones de superficie (columnas, placas).
struct Vor2 { float f1, f2, id; float cx, cy; };
inline Vor2 voronoi2(float x, float y, float jitter = 0.9f, int seed = 0) {
  float fx = std::floor(x), fy = std::floor(y);
  Vor2 r{9, 9, 0, 0, 0};
  for (int j = -1; j <= 1; j++)
    for (int i = -1; i <= 1; i++) {
      int cx = (int)fx + i, cy = (int)fy + j;
      float ox = 0.5f + (h2(cx, cy, seed) - 0.5f) * jitter;
      float oy = 0.5f + (h2(cx, cy, seed + 31) - 0.5f) * jitter;
      float dx = cx + ox - x, dy = cy + oy - y;
      float d = std::sqrt(dx * dx + dy * dy);
      if (d < r.f1) { r.f2 = r.f1; r.f1 = d; r.id = h2(cx, cy, seed + 77); r.cx = cx + ox; r.cy = cy + oy; }
      else if (d < r.f2) r.f2 = d;
    }
  return r;
}

// ------------------------------------------------------------------ formas
inline float sdSphere(v3 p, float r) { return len(p) - r; }
inline float sdBox(v3 p, v3 b) {
  v3 q = vabs(p) - b;
  return len(vmax(q, 0)) + std::min(vmaxc(q), 0.f);
}
inline float sdRoundBox(v3 p, v3 b, float r) { return sdBox(p, b - v3(r)) - r; }
inline float sdEllipsoid(v3 p, v3 r) {
  float k0 = len(p / r), k1 = len(p / (r * r));
  return k0 * (k0 - 1) / std::max(k1, 1e-6f);
}
inline float sdCapsule(v3 p, v3 a, v3 b, float r) {
  v3 pa = p - a, ba = b - a;
  float h = sat(dot(pa, ba) / dot(ba, ba));
  return len(pa - ba * h) - r;
}
// Cápsula con radio variable.
inline float sdCone2(v3 p, v3 a, v3 b, float ra, float rb, float* th = nullptr) {
  v3 pa = p - a, ba = b - a;
  float h = sat(dot(pa, ba) / dot(ba, ba));
  if (th) *th = h;
  return len(pa - ba * h) - mixf(ra, rb, h);
}
// Bézier cuadrática: distancia aproximada por muestreo + refinamiento.
inline float sdBezier(v3 p, v3 a, v3 b, v3 c, float* tOut) {
  float best = 1e9f, bt = 0;
  const int N = 12;
  for (int i = 0; i <= N; i++) {
    float t = i / float(N);
    v3 q = a * ((1 - t) * (1 - t)) + b * (2 * (1 - t) * t) + c * (t * t);
    float d = dot(q - p, q - p);
    if (d < best) { best = d; bt = t; }
  }
  // refinamiento de Newton
  for (int it = 0; it < 3; it++) {
    v3 q = a * ((1 - bt) * (1 - bt)) + b * (2 * (1 - bt) * bt) + c * (bt * bt);
    v3 d1 = (b - a) * (2 * (1 - bt)) + (c - b) * (2 * bt);
    v3 d2 = (a - b * 2 + c) * 2;
    v3 r = q - p;
    float num = dot(r, d1), den = dot(d1, d1) + dot(r, d2);
    if (std::fabs(den) > 1e-8f) bt = sat(bt - num / den);
  }
  v3 q = a * ((1 - bt) * (1 - bt)) + b * (2 * (1 - bt) * bt) + c * (bt * bt);
  if (tOut) *tOut = bt;
  return len(p - q);
}
inline v3 bez(v3 a, v3 b, v3 c, float t) {
  return a * ((1 - t) * (1 - t)) + b * (2 * (1 - t) * t) + c * (t * t);
}
inline v3 bezd(v3 a, v3 b, v3 c, float t) { return (b - a) * (2 * (1 - t)) + (c - b) * (2 * t); }

// Intersección rayo-esfera (devuelve t cercano y lejano).
inline bool raySphere(v3 ro, v3 rd, v3 c, float r, float& t0, float& t1) {
  v3 oc = ro - c;
  float b = dot(oc, rd), cc = dot(oc, oc) - r * r, h = b * b - cc;
  if (h < 0) return false;
  h = std::sqrt(h);
  t0 = -b - h;
  t1 = -b + h;
  return true;
}

// ------------------------------------------------------------------- cámara
struct Camera {
  v3 pos, fwd, right, up;
  float tanHalf, aspect;
  Camera(v3 p, v3 target, v3 upHint, float fovDeg, float asp) {
    pos = p;
    fwd = nrm(target - p);
    right = nrm(cross(fwd, upHint));
    up = cross(right, fwd);
    tanHalf = std::tan(fovDeg * 0.5f * 3.14159265f / 180.f);
    aspect = asp;
  }
  // u, v en [-1, 1]; v hacia arriba.
  v3 dir(float u, float v) const {
    return nrm(fwd + right * (u * tanHalf * aspect) + up * (v * tanHalf));
  }
  // Proyección de un punto a coordenadas de imagen [0,1] (para anclas).
  bool project(v3 p, float& sx, float& sy) const {
    v3 d = p - pos;
    float z = dot(d, fwd);
    if (z <= 0) return false;
    float u = dot(d, right) / (z * tanHalf * aspect);
    float v = dot(d, up) / (z * tanHalf);
    sx = 0.5f + 0.5f * u;
    sy = 0.5f - 0.5f * v;
    return true;
  }
};

// ------------------------------------------------------------------- imagen
struct Image {
  int w, h;
  std::vector<float> px;  // RGB lineal + alfa (máscara de planeta)
  Image(int W, int H) : w(W), h(H), px(size_t(W) * H * 4, 0.f) {}
  void set(int x, int y, v3 c, float a) {
    float* p = &px[(size_t(y) * w + x) * 4];
    p[0] = c.x; p[1] = c.y; p[2] = c.z; p[3] = a;
  }
  // Formato propio: cabecera de texto + float32 RGBA.
  void save(const std::string& path) const {
    FILE* f = fopen(path.c_str(), "wb");
    if (!f) { perror(path.c_str()); return; }
    fprintf(f, "SWHDR %d %d\n", w, h);
    fwrite(px.data(), sizeof(float), px.size(), f);
    fclose(f);
  }
};

// Recorre la imagen en paralelo; fn(x, y) devuelve color y alfa.
template <class F>
void renderParallel(Image& img, F fn, bool progress = true) {
  std::atomic<int> next(0), done(0);
  int nt = std::max(1u, std::thread::hardware_concurrency());
  std::vector<std::thread> th;
  for (int t = 0; t < nt; t++)
    th.emplace_back([&]() {
      for (;;) {
        int y = next++;
        if (y >= img.h) break;
        for (int x = 0; x < img.w; x++) {
          float a = 0;
          v3 c = fn(x, y, a);
          img.set(x, y, c, a);
        }
        int d = ++done;
        if (progress && d % 50 == 0) { fprintf(stderr, "\r%3d%%", d * 100 / img.h); fflush(stderr); }
      }
    });
  for (auto& t : th) t.join();
  if (progress) fprintf(stderr, "\r100%%\n");
}

// Estrellas procedurales en una dirección (fondo de espacio).
inline v3 starfield(v3 rd, float density = 1.f, float bright = 1.f) {
  v3 col(0);
  for (int layer = 0; layer < 3; layer++) {
    float sc = 140.f + layer * 170.f;
    v3 p = rd * sc + v3(layer * 31.7f);
    v3 fp(std::floor(p.x), std::floor(p.y), std::floor(p.z));
    int ix = (int)fp.x, iy = (int)fp.y, iz = (int)fp.z;
    float r = h3(ix, iy, iz + layer * 101);
    if (r < 0.06f * density) {
      v3 o(h3(ix + 3, iy, iz), h3(ix, iy + 5, iz), h3(ix, iy, iz + 9));
      v3 c = fp + v3(0.2f) + o * 0.6f;
      float d = len(p - c);
      float b = std::pow(h3(ix + 9, iy + 1, iz), 6.f) * 3.f + 0.15f;
      float tint = h3(ix + 2, iy + 8, iz);
      v3 sc3 = mix(v3(0.75f, 0.8f, 1.f), v3(1.f, 0.88f, 0.8f), tint);
      col += sc3 * (b * bright * std::exp(-d * d * 60.f));
    }
  }
  return col;
}
