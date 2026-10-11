// Concepto B — El Archipiélago del Reverso.
//
// Umbral como una planta: un núcleo pequeño y húmedo (el Sotobosque) del que
// salen pecíolos fibrosos. Cada pecíolo sostiene una isla por su borde, como
// una hoja. Entre el pecíolo y la isla hay un pulvínulo: una articulación
// hinchada que, en sombra, pierde presión y deja que la isla gire hacia fuera
// como una tapa.
//
// Cara exterior (al sol): roca blanqueada, grietas, rosetas de liquen.
// Cara interior (hacia el núcleo): musgo violeta y farolillos plegados que
// sólo se despliegan cuando la cara se expone a la noche.
//
//   0 · La Meseta   — la mayor, en terrazas. Debajo, en el núcleo: la Umbría.
//   1 · El Atolón   — un anillo; por su hueco se ve el núcleo.
//   2 · La Copa     — pequeña y muy abombada.
//   3 · Las Gemelas — dos hojas sobre un pecíolo bifurcado.
//   5 · La Concha   — alargada, nervada.
//
// uso: rev <escena> <ancho> <alto> <salida.swhdr>
//   escenas: orbit, silhouette, approach, transform, discover

#include "common.h"

static v3 SUN;
static v3 MOON_C;
static float MOON_R = 0.3f;
static bool ECLIPSE = false;
static float ATM_K = 1.f;
static float PODS_OPEN = 0.f;

static v3 C_BONE, C_BONE_DK, C_LICHEN, C_HUMUS, C_HUMUS_LT, C_MOSS, C_STEM, C_STEM_DK, C_GLOW, C_AMBER, C_MOON;

static const float CORE_R = 0.58f;

static v3 sph(float lon, float lat) {
  return v3(std::cos(lat) * std::sin(lon), std::sin(lat), std::cos(lat) * std::cos(lon));
}

// ------------------------------------------------------------------ islas
struct Island {
  int kind;      // 0 meseta, 1 atolón, 2 copa, 3 gemela, 4 concha
  v3 pivot;      // pulvínulo: donde el pecíolo toca el borde de la isla
  v3 base, ctrl; // pecíolo (bézier desde el núcleo)
  Frame fr;      // t: del pivote hacia el centro de la isla; n: fuera
  float off;     // distancia del pivote al centro de la isla
  float R, H, thick, dome, elong, seed, stemR;
  float angle;   // giro del pulvínulo (0 en reposo, π volteada)
  v3 axis;
  float open() const { return sat((angle - 0.35f) / 1.4f); }
};
static std::vector<Island> IS;

static void buildIslands() {
  // lon/lat: dirección del pivote; hdg: hacia dónde se extiende la isla
  auto add = [&](int kind, float lon, float lat, float dist, float hdg, float R, float H, float thick, float dome,
                 float elong, float seed, float stemR, v3 baseOverride = v3(0)) {
    Island I;
    I.kind = kind;
    v3 dir = sph(lon, lat);
    I.pivot = dir * dist;
    Frame f(dir, v3(0, 1, 0));
    v3 t = rotAxis(f.t, dir, hdg);
    I.fr.n = dir;
    I.fr.t = t;
    I.fr.b = cross(dir, t);
    I.off = R * elong * 0.88f;
    I.R = R; I.H = H; I.thick = thick; I.dome = dome; I.elong = elong; I.seed = seed; I.stemR = stemR;
    // el pecíolo nace detrás del pivote y se inclina hacia fuera
    I.base = (len(baseOverride) > 0) ? baseOverride : nrm(dir - t * 0.32f) * (CORE_R - 0.03f);
    v3 mid = (I.base + I.pivot) * 0.5f;
    I.ctrl = nrm(mid) * (len(I.pivot) * 0.93f) - t * 0.04f;
    I.angle = 0;
    I.axis = -I.fr.b;  // ángulo positivo: la isla se abre hacia fuera
    IS.push_back(I);
  };
  //   kind lon     lat     dist  hdg    R      H      thick  dome   elong seed stemR
  add(0, 0.05f, 0.1f, 0.88f, 2.55f, 0.38f, 0.075f, 0.11f, 0.05f, 1.25f, 1.f, 0.075f);   // Meseta
  add(1, -1.4f, 0.6f, 0.85f, 0.9f, 0.31f, 0.045f, 0.065f, 0.03f, 1.0f, 2.f, 0.055f);    // Atolón
  add(2, 1.75f, 0.52f, 0.84f, -0.4f, 0.2f, 0.04f, 0.07f, 0.13f, 1.05f, 3.f, 0.05f);     // Copa
  v3 gb = nrm(sph(-0.55f, -0.78f)) * (CORE_R - 0.03f);
  add(3, -0.95f, -0.6f, 0.86f, 3.6f, 0.2f, 0.04f, 0.06f, 0.04f, 1.0f, 4.f, 0.045f, gb);   // Gemela a
  add(3, -0.22f, -0.98f, 0.86f, 5.2f, 0.17f, 0.04f, 0.055f, 0.04f, 1.0f, 5.f, 0.04f, gb); // Gemela b
  add(4, 1.5f, -0.42f, 0.86f, 1.2f, 0.26f, 0.05f, 0.075f, 0.12f, 1.6f, 6.f, 0.055f);    // Concha
}

static v3 islandCenterWorld(const Island& I) {
  v3 c = I.fr.t * I.off;
  if (I.angle != 0) c = rotAxis(c, I.axis, I.angle);
  return I.pivot + c;
}
// Punto del mundo → coordenadas locales de la isla (x a lo largo, y fuera).
static v3 toIsland(const Island& I, const v3& p) {
  v3 q = p - I.pivot;
  if (I.angle != 0) q = rotAxis(q, I.axis, -I.angle);
  return v3(dot(q, I.fr.t) - I.off, dot(q, I.fr.n), dot(q, I.fr.b));
}
static v3 fromIslandDir(const Island& I, const v3& l) {
  v3 w = I.fr.t * l.x + I.fr.n * l.y + I.fr.b * l.z;
  if (I.angle != 0) w = rotAxis(w, I.axis, I.angle);
  return w;
}

struct CapInfo { float yt, yb, outline, rr; };
static CapInfo capSurf(const Island& I, const v3& q) {
  float x = q.x / I.elong, z = q.z;
  float r = std::sqrt(x * x + z * z);
  float ang = std::atan2(z, x);
  float s = I.seed;
  float lobe = 1 + 0.15f * std::sin(3 * ang + s) + 0.08f * std::sin(5 * ang + 2 * s) + 0.04f * std::sin(9 * ang + s * 3);
  float Rr = I.R * lobe;
  CapInfo c;
  c.rr = r / Rr;
  float u = sat(c.rr);
  c.outline = (r - Rr) * 0.8f;
  float dome = I.dome * (1 - u * u);
  if (I.kind == 0) {
    // terrazas: tres o cuatro escalones de bordes erosionados
    float uu = u + 0.07f * fbm(q * 3.5f + v3(2), 3) + 0.015f * fbm(q * 14.f, 2);
    float e = sat(1 - uu);
    float lv = e * 3.4f;
    float fl = std::floor(lv), fr = lv - fl;
    float eq = (fl + sstep(0.72f, 1.f, fr)) / 3.4f;
    float h = 0.02f + (I.H + I.dome) * eq;
    c.yt = h + 0.004f * fbm(q * 16.f, 3);
  } else if (I.kind == 4) {
    float rib = std::fabs(std::sin(ang * 10.f));
    c.yt = I.H + dome + 0.01f * (1 - rib) * u;
  } else {
    c.yt = I.H + dome + 0.005f * fbm(q * 20.f, 3);
  }
  float th = I.thick * (1 - 0.7f * u * u) + 0.014f;
  // la cara interior es cóncava: un nicho
  c.yb = c.yt - th - 0.02f * (1 - u * u);
  return c;
}

static float sdIslandLocal(const Island& I, const v3& q) {
  CapInfo c = capSurf(I, q);
  float rock = 0.008f * (ridged(q * 9.f + v3(I.seed), 3) - 0.5f) + 0.003f * (ridged(q * 34.f, 3) - 0.5f);
  float cap;
  if (I.kind == 1) {
    float r = std::sqrt(q.x * q.x + q.z * q.z);
    float ring = std::fabs(r - I.R * 0.75f) - I.R * 0.25f * (1 + 0.25f * std::sin(std::atan2(q.z, q.x) * 4 + 1));
    cap = std::max(ring * 0.8f, std::max(q.y - c.yt, c.yb - q.y) * 0.6f);
  } else {
    cap = std::max(c.outline, std::max(q.y - c.yt, c.yb - q.y) * 0.35f);
  }
  return cap + rock;
}

// Farolillos: plegados contra la cara interior, se alargan al abrirse.
static float sdLanterns(const Island& I, const v3& q, float* glow = nullptr) {
  CapInfo c0 = capSurf(I, q);
  float op = I.open();
  float maxL = 0.012f + 0.07f * op;
  {
    float vb = std::max(q.y - c0.yb - 0.01f, c0.yb - maxL - 0.02f - q.y);
    float bnd = std::max(vb * 0.6f, c0.outline);
    if (bnd > 0.01f) return bnd;
  }
  const float cell = 0.04f;
  float cx = std::floor(q.x / cell), cz = std::floor(q.z / cell);
  float fx = q.x / cell - cx, fz = q.z / cell - cz;
  float edge = std::min(std::min(fx, 1 - fx), std::min(fz, 1 - fz)) * cell + 0.002f;
  int ix = (int)cx, iz = (int)cz;
  if (h2(ix, iz, (int)I.seed * 13) > 0.6f) return edge;
  float ox = (cx + 0.3f + 0.4f * h2(ix, iz, 2)) * cell, oz = (cz + 0.3f + 0.4f * h2(ix, iz, 3)) * cell;
  v3 top(ox, 0, oz);
  CapInfo c = capSurf(I, top);
  if (c.rr > 0.9f) return edge;
  if (I.kind == 1 && std::fabs(std::sqrt(ox * ox + oz * oz) - I.R * 0.75f) > I.R * 0.2f) return edge;
  top.y = c.yb + 0.004f;
  float L = (0.25f + 0.75f * h2(ix, iz, 4)) * maxL;
  // los tallos se curvan un poco hacia el borde
  v3 bend = v3(ox, 0, oz) * (0.15f * op);
  v3 bot = top - v3(0, L, 0) + bend;
  float d = sdCapsule(q, top, bot, 0.0016f);
  float bs = (0.6f + 0.6f * h2(ix, iz, 5)) * (0.55f + 0.45f * op);
  float bulb = sdEllipsoid(q - bot, v3(0.0065f, 0.009f, 0.0065f) * bs);
  if (glow) *glow = (bulb < d) ? 1.f : 0.3f;
  return std::min(std::min(d, bulb), edge);
}

// ------------------------------------------------------------------ tallos
static float sdStem(const Island& I, const v3& p, float* tOut = nullptr) {
  float t;
  float d = sdBezier(p, I.base, I.ctrl, I.pivot, &t);
  v3 q = bez(I.base, I.ctrl, I.pivot, t);
  v3 tg = nrm(bezd(I.base, I.ctrl, I.pivot, t));
  Frame f(tg);
  v3 o = f.toLocal(p - q);
  float ang = std::atan2(o.y, o.x);
  float braid = 0.2f * std::cos(3 * (ang - t * 7.f - I.seed));
  float fib = 0.05f * std::fabs(std::sin(ang * 17 + t * 30 + I.seed));
  float flare = 1 + 1.3f * std::exp(-t * 10.f);
  float knuckle = 0.75f * std::exp(-sq((t - 0.94f) / 0.05f));  // pulvínulo
  float rad = I.stemR * (flare + knuckle) * (1 - 0.3f * t) * (1 + braid * (1 - knuckle) - fib);
  if (tOut) *tOut = t;
  return (d - rad) * 0.75f;
}

// ------------------------------------------------------------------- núcleo
static v3 UMB;  // centro de la Umbría (bajo la Meseta en reposo)
static float sdCore(const v3& p, float* basin = nullptr) {
  float r = len(p);
  if (r > CORE_R + 0.15f) return r - CORE_R - 0.1f;
  v3 d = p / r;
  float roots = 0.03f * ridged(d * 5.f, 4);
  float pits = 0.018f * fbm(d * 3.f, 3);
  // la Umbría: una hondonada que sólo ve el cielo cuando la Meseta se abre
  float du = len(d - UMB);
  float bowl = 1 - sstep(0.06f, 0.26f, du + 0.03f * fbm(d * 9.f, 3));
  float h = roots - pits - 0.07f * bowl * bowl * (3 - 2 * bowl) + 0.012f * bowl * fbm(d * 30.f, 3);
  if (basin) *basin = bowl;
  return (r - CORE_R - h) * 0.7f;
}

// Vainas de la Umbría: semillas en el fondo de la hondonada.
static float sdPods(const v3& p, float* openOut = nullptr) {
  float r = len(p);
  if (r > CORE_R + 0.06f) return r - CORE_R - 0.04f;
  v3 d = p / r;
  if (len(d - UMB) > 0.22f) return std::max(len(d - UMB) - 0.2f, 0.01f);
  Frame uf(UMB);
  v3 l = uf.toLocal(d);
  const float cell = 0.028f;
  float cx = std::floor(l.x / cell), cy = std::floor(l.y / cell);
  float fx = l.x / cell - cx, fy = l.y / cell - cy;
  float edge = std::min(std::min(fx, 1 - fx), std::min(fy, 1 - fy)) * cell * CORE_R + 0.002f;
  int ix = (int)cx, iy = (int)cy;
  float px = (cx + 0.3f + 0.4f * h2(ix, iy, 31)) * cell, py = (cy + 0.3f + 0.4f * h2(ix, iy, 32)) * cell;
  float rad = std::sqrt(px * px + py * py);
  if (rad > 0.17f || h2(ix, iy, 33) > 0.75f - rad * 2) return edge;
  v3 pd = nrm(uf.toWorld(v3(px, py, 1)));
  // altura del suelo en ese punto
  float lo = CORE_R - 0.08f, hi = CORE_R + 0.05f;
  for (int it = 0; it < 12; it++) {
    float mid = 0.5f * (lo + hi);
    if (sdCore(pd * mid) < 0) lo = mid; else hi = mid;
  }
  v3 c = pd * lo;
  Frame pf(pd);
  v3 q = pf.toLocal(p - c);
  float sc = (0.7f + 0.6f * h2(ix, iy, 34)) * 0.6f;
  float op = PODS_OPEN;
  // vaina cerrada: ojiva. Abierta: se rasga en tres y deja ver un núcleo encendido.
  float ang = std::atan2(q.y, q.x);
  float split = op * 0.006f * sc * sstep(0.f, 0.02f, q.z) * std::fabs(std::sin(ang * 1.5f));
  float dd = sdEllipsoid(q - v3(0, 0, 0.012f * sc), v3(0.008f, 0.008f, 0.016f) * sc) + split;
  if (openOut) *openOut = op * (1 - sstep(0.0f, 0.004f, len(v3(q.x, q.y, 0)) - 0.0035f * sc));
  return std::min(dd * 0.7f, edge);
}

static float sdMoon(const v3& p) { return len(p - MOON_C) - MOON_R; }

// --------------------------------------------------------------------- mapa
enum { M_NONE, M_CORE, M_STEM, M_CAP, M_LANTERN, M_MOON, M_POD };
struct Hit { float d; int m; int id; };
static Hit mapAll(const v3& p) {
  Hit h{sdCore(p), M_CORE, -1};
  float dp = sdPods(p);
  if (dp < h.d) h = {dp, M_POD, -1};
  for (size_t i = 0; i < IS.size(); i++) {
    const Island& I = IS[i];
    float sd = sdStem(I, p);
    if (sd < h.d) h = {sd, M_STEM, (int)i};
    float bd = len(p - islandCenterWorld(I)) - (I.R * I.elong * 1.3f + 0.12f);
    if (bd > h.d) continue;
    v3 q = toIsland(I, p);
    float d = sdIslandLocal(I, q);
    if (d < h.d) h = {d, M_CAP, (int)i};
    float dl = sdLanterns(I, q);
    if (dl < h.d) h = {dl, M_LANTERN, (int)i};
  }
  float dm = sdMoon(p);
  if (dm < h.d) h = {dm, M_MOON, -1};
  return h;
}
static float mapSolid(const v3& p) { return mapAll(p).d; }

static float sdOf(const v3& p, int m, int id) {
  switch (m) {
    case M_CORE: return sdCore(p);
    case M_POD: return sdPods(p);
    case M_STEM: return sdStem(IS[id], p);
    case M_CAP: return sdIslandLocal(IS[id], toIsland(IS[id], p));
    case M_LANTERN: return sdLanterns(IS[id], toIsland(IS[id], p));
    case M_MOON: return sdMoon(p);
  }
  return 1e9f;
}
static v3 normalOf(const v3& p, int m, int id, float e) {
  v3 n(sdOf(p + v3(e, 0, 0), m, id) - sdOf(p - v3(e, 0, 0), m, id),
       sdOf(p + v3(0, e, 0), m, id) - sdOf(p - v3(0, e, 0), m, id),
       sdOf(p + v3(0, 0, e), m, id) - sdOf(p - v3(0, 0, e), m, id));
  return nrm(n);
}

static bool CAST = true;  // la luna proyecta sombra (no en la vista orbital)
static float umbra(const v3& p) {
  if (!CAST) return 0;
  v3 v = p - MOON_C;
  float along = -dot(v, SUN);
  if (along <= 0) return 0;
  float perp = len(v + SUN * along);
  float pen = 0.05f + along * 0.02f;
  return 1 - sstep(MOON_R - pen, MOON_R + pen, perp);
}

static float softShadow(v3 ro, v3 rd, float tmin, float tmax, float k) {
  float res = 1, t = tmin;
  for (int i = 0; i < 90 && t < tmax; i++) {
    float h = mapSolid(ro + rd * t);
    res = std::min(res, k * h / t);
    if (res < 0.002f) return 0;
    t += clampf(h, 0.003f, 0.12f);
  }
  return sat(res);
}
static float ambOcc(v3 p, v3 n, float sc) {
  float o = 0, w = 1;
  for (int i = 1; i <= 5; i++) {
    float h = sc * i;
    o += w * (h - mapSolid(p + n * h));
    w *= 0.6f;
  }
  return sat(1 - o * 2.0f / sc);
}

// Luz de los farolillos abiertos sobre lo que tienen cerca.
static v3 lanternLight(const v3& p, const v3& n) {
  v3 acc(0);
  for (const Island& I : IS) {
    float op = I.open();
    if (op <= 0) continue;
    v3 q = toIsland(I, p);
    CapInfo c = capSurf(I, q);
    float below = c.yb - q.y;
    if (below < -0.03f || below > 0.6f) continue;
    v3 down = fromIslandDir(I, v3(0, -1, 0));
    float facing = 0.35f + 0.65f * sat(dot(n, -down));
    float k = std::exp(-std::max(below, 0.f) * 6.f) * (1 - sstep(0.8f, 1.3f, c.rr)) * facing;
    acc += mix(C_GLOW, C_AMBER, 0.4f) * (1.1f * k * op);
  }
  // la Umbría encendida por sus vainas
  if (PODS_OPEN > 0) {
    float du = len(nrm(p) - UMB);
    float hgt = len(p) - CORE_R;
    acc += mix(C_AMBER, C_GLOW, 0.3f) * (1.2f * PODS_OPEN * (1 - sstep(0.12f, 0.32f, du)) * std::exp(-std::max(hgt, 0.f) * 6.f));
  }
  return acc;
}

// ------------------------------------------------------------------- cielo
static v3 skyCol(v3 ro, v3 rd) {
  v3 c = hex(0x0e0c13) * 0.6f;
  float neb = fbm(rd * 2.2f + v3(3, 1, 0), 5);
  float band = std::exp(-sq(dot(rd, nrm(v3(0.5f, 1, 0.2f))) / 0.4f));
  c += mix(hex(0x23202c), hex(0x4a2f50), 0.5f + 0.5f * neb) * (0.5f * band * sat(neb + 0.6f));
  c += starfield(rd, 1.f, 0.9f) * 0.9f;
  float sunAng = std::acos(clampf(dot(rd, SUN), -1, 1));
  float vis = 1;
  if (ECLIPSE) {
    float t0, t1;
    if (raySphere(ro, rd, MOON_C, MOON_R, t0, t1) && t1 > 0) vis = 0;
  }
  c += hex(0xfff0dc) * (sstep(0.016f, 0.013f, sunAng) * 40.f * vis);
  c += hex(0xffd9b0) * (0.45f * std::exp(-sunAng * 20.f) + 0.1f * std::exp(-sunAng * 5.f)) * (ECLIPSE ? 0.3f : 1.f);
  if (ECLIPSE) {
    float ring = std::exp(-sq((sunAng - 0.047f) / 0.006f)) * 2.f + std::exp(-std::max(sunAng - 0.045f, 0.f) * 22.f) * 0.35f;
    float rays = 0.6f + 0.4f * vnoise(nrm(rd - SUN * dot(rd, SUN)) * 12.f);
    c += hex(0xffe6c8) * (ring * rays * sstep(0.044f, 0.05f, sunAng));
  }
  return c;
}

static v3 haze(v3 ro, v3 rd, float tEnd, v3& trans) {
  trans = v3(1);
  float t0, t1;
  if (!raySphere(ro, rd, v3(0), 1.6f, t0, t1)) return v3(0);
  t0 = std::max(t0, 0.f);
  t1 = std::min(t1, tEnd);
  if (t1 <= t0) return v3(0);
  const int N = 16;
  float dt = (t1 - t0) / N;
  v3 acc(0);
  float tr = 1;
  for (int i = 0; i < N; i++) {
    v3 p = ro + rd * (t0 + (i + 0.5f) * dt);
    float r = len(p);
    float dens = std::exp(-std::max(r - CORE_R, 0.f) / 0.12f) * 0.35f * ATM_K;
    float lit = sstep(-0.3f, 0.3f, dot(p / r, SUN)) * (1 - umbra(p) * 0.9f);
    float mu = dot(rd, SUN);
    float ph = 0.6f + 0.8f * std::pow(sat(mu), 8.f);
    float st = dens * dt;
    acc += (hex(0xb59ad8) * (lit * ph) + hex(0x2a1e3c) * 0.3f) * (st * tr);
    tr *= std::exp(-st * 1.2f);
  }
  trans = v3(tr);
  return acc * 0.5f;
}

// --------------------------------------------------------------- materiales
static v3 shade(const v3& ro, const v3& rd, const v3& p, const Hit& h, float t) {
  float e = 0.0003f + t * 0.0004f;
  v3 n = normalOf(p, h.m, h.id, e);
  v3 alb(0.5f), emit(0);
  float um = umbra(p);
  float sunVis = 1 - um;
  if (h.m == M_MOON) {
    float cr = fbm(n * 6.f, 4);
    alb = C_MOON * (0.75f + 0.35f * cr);
    return alb * hex(0xfff0dc) * (3.f * sat(dot(n, SUN)));
  }
  v3 radial = nrm(p);
  if (h.m == M_CORE) {
    float basin;
    sdCore(p, &basin);
    // sotobosque: humus oscuro, cordones de raíz y colchones de musgo
    float rr = ridged(radial * 4.f, 3);
    alb = mix(C_HUMUS, C_HUMUS_LT, sstep(0.55f, 0.95f, rr) * 0.8f);
    float mossy = sstep(0.0f, 0.4f, fbm(radial * 6.f + v3(9), 4));
    alb = mix(alb, C_MOSS * 0.4f, mossy * 0.5f);
    float root = std::pow(sat(1 - std::fabs(vnoise(radial * 6.f + v3(fbm(radial * 3.f, 3)))) * 8.f), 2.f);
    alb = mix(alb, C_STEM * 0.45f, root * 0.2f);
    Vor v = voronoi(radial * 70.f);
    float speck = sstep(0.12f, 0.0f, v.f1) * sstep(0.8f, 0.97f, v.id);
    emit = mix(C_GLOW, C_AMBER, v.id) * (speck * 0.25f);
    alb = mix(alb, hex(0x1a1420), basin * 0.6f);
  } else if (h.m == M_POD) {
    float op;
    sdPods(p, &op);
    alb = mix(hex(0x3a2c3a), hex(0x6a5560), 0.5f + 0.5f * fbm(p * 200.f, 2));
    emit = mix(C_AMBER, hex(0xffd2a0), 0.3f) * (op * 1.6f) + C_AMBER * (0.03f * PODS_OPEN);
  } else if (h.m == M_STEM) {
    float ts;
    sdStem(IS[h.id], p, &ts);
    float fib = 0.5f + 0.5f * std::sin(dot(p, v3(31, 47, 13)) * 3 + fbm(p * 40.f, 2) * 4);
    alb = mix(C_STEM_DK, C_STEM, 0.4f + 0.4f * fib);
    float kn = std::exp(-sq((ts - 0.94f) / 0.06f));
    alb = mix(alb, hex(0xb7a7b0), kn * 0.6f);
    float veins = std::pow(sat(1 - std::fabs(vnoise(p * 140.f)) * 4), 3.f);
    // el pulvínulo late cuando gira
    float act = sat(IS[h.id].angle * 2.f) + um * 0.3f;
    emit = C_GLOW * (kn * veins * (0.05f + 1.6f * act));
  } else if (h.m == M_LANTERN) {
    float g = 0;
    const Island& I = IS[h.id];
    v3 q = toIsland(I, p);
    sdLanterns(I, q, &g);
    alb = C_MOSS;
    float hue = h2((int)std::floor(q.x / 0.04f), (int)std::floor(q.z / 0.04f), 9);
    float op = I.open();
    emit = mix(C_GLOW, C_AMBER, hue) * ((g > 0.5f ? 3.5f : 0.3f) * op + (g > 0.5f ? 0.02f : 0.f));
  } else {
    const Island& I = IS[h.id];
    v3 q = toIsland(I, p);
    CapInfo c = capSurf(I, q);
    float nly = dot(n, fromIslandDir(I, v3(0, 1, 0)));
    float outer = sstep(-0.75f, -0.35f, nly) * sstep(c.yb + 0.006f, c.yb + 0.02f, q.y);
    float strata = 0.5f + 0.5f * std::sin(q.y * 520 + 5 * fbm(q * 9.f, 2));
    float grit = fbm(q * 60.f, 3);
    v3 rock = mix(C_BONE_DK, C_BONE, sat(0.35f + 0.3f * strata + 0.45f * grit));
    rock = rock * (0.75f + 0.25f * sstep(-0.5f, 0.6f, nly));
    Vor2 lv = voronoi2(q.x * 60, q.z * 60, 0.9f, (int)I.seed);
    float lich = sstep(0.28f, 0.1f, lv.f1) * sstep(0.55f, 0.8f, lv.id) * sstep(0.2f, 0.6f, nly);
    rock = mix(rock, C_LICHEN, lich * 0.7f);
    Vor2 ck = voronoi2(q.x * 16 + 0.3f * fbm(q * 20.f, 2), q.z * 16, 0.9f, (int)I.seed + 7);
    float crack = sstep(0.05f, 0.0f, ck.f2 - ck.f1);
    rock = rock * (1 - 0.55f * crack * sstep(0.2f, 0.6f, nly));
    Vor2 pv = voronoi2(q.x * 45, q.z * 45, 0.9f, (int)I.seed + 3);
    float pillow = sstep(0.0f, 0.4f, pv.f2 - pv.f1);
    v3 moss = mix(C_MOSS * 0.35f, C_MOSS, pillow);
    float spark = sstep(0.07f, 0.0f, pv.f1) * sstep(0.7f, 0.95f, pv.id);
    alb = mix(moss, rock, outer);
    float op = I.open();
    emit = mix(C_GLOW, C_AMBER, pv.id) * (spark * (0.15f + 1.4f * op) * (1 - outer));
  }
  float dif = sat(dot(n, SUN));
  float sh = (dif > 0 && sunVis > 0.01f) ? softShadow(p + n * 0.003f, SUN, 0.004f, 3.f, 14.f) : 0;
  float ao = 0.25f + 0.75f * ambOcc(p, n, 0.03f);
  v3 sunCol = hex(0xfff0dc) * 2.3f;
  v3 skyA = mix(hex(0x1c1626), hex(0x5b4a7a), 0.5f + 0.5f * dot(n, radial)) * (0.2f * (1 - 0.8f * um));
  v3 bounce = hex(0x3a2a40) * (0.1f * sat(-dot(n, radial) * 0.5f + 0.5f));
  v3 lant = lanternLight(p, n);
  v3 col = alb * (sunCol * (dif * sh * sunVis) + (skyA + bounce) * ao + lant * (0.4f + 0.6f * ao));
  return col + emit;
}

static v3 render(v3 ro, v3 rd, float& alpha) {
  alpha = 0;
  float a0, a1;
  float s0 = 1e9f, s1 = -1e9f;
  if (raySphere(ro, rd, v3(0), 1.75f, a0, a1) && a1 > 0) { s0 = std::min(s0, std::max(a0, 0.f)); s1 = std::max(s1, a1); }
  if (raySphere(ro, rd, MOON_C, MOON_R * 1.02f, a0, a1) && a1 > 0) { s0 = std::min(s0, std::max(a0, 0.f)); s1 = std::max(s1, a1); }
  Hit h{1e9f, M_NONE, -1};
  float t = s0;
  if (s1 > 0) {
    Hit last{1e9f, M_NONE, -1};
    for (int i = 0; i < 700 && t < s1; i++) {
      v3 p = ro + rd * t;
      Hit hh = mapAll(p);
      float eps = 0.00015f + t * 0.0005f;
      if (std::fabs(hh.d) < eps) { h = hh; break; }
      last = hh;
      t += (hh.d < 0) ? hh.d * 1.2f : std::max(hh.d, eps * 0.5f);
    }
    if (h.m == M_NONE && t < s1 && last.d < 0.004f) h = last;
  }
  if (h.m == M_NONE) {
    v3 tr;
    v3 hz = haze(ro, rd, 1e9f, tr);
    return skyCol(ro, rd) * tr + hz;
  }
  alpha = 1;
  v3 p = ro + rd * t;
  if (getenv("DBGM")) {
    const v3 pal[7] = {v3(0), v3(0.4f, 0.2f, 0.5f), v3(0.6f, 0.4f, 0.2f), v3(0.9f), v3(1, 0.6f, 0), v3(0.5f), v3(1, 0, 0)};
    v3 n = normalOf(p, h.m, h.id, 0.001f);
    float sh = softShadow(p + n * 0.003f, SUN, 0.004f, 3.f, 14.f);
    return pal[h.m] * (0.2f + 0.8f * sat(dot(n, SUN))) * (getenv("DBGS") ? (0.3f + 0.7f * sh) : 1.f);
  }
  v3 col = shade(ro, rd, p, h, t);
  v3 tr;
  v3 hz = haze(ro, rd, t, tr);
  return col * tr + hz;
}

// ------------------------------------------------------------------ escenas
int main(int argc, char** argv) {
  std::string scene = argc > 1 ? argv[1] : "orbit";
  int W = argc > 2 ? atoi(argv[2]) : 800;
  int H = argc > 3 ? atoi(argv[3]) : 500;
  std::string out = argc > 4 ? argv[4] : "out.swhdr";
  auto envf = [](const char* k, float d) { return getenv(k) ? (float)atof(getenv(k)) : d; };

  C_BONE = hex(0xcfc4b8);
  C_BONE_DK = hex(0x8f8495);
  C_LICHEN = hex(0xc9b27a);
  C_HUMUS = hex(0x2a1f33);
  C_HUMUS_LT = hex(0x45354f);
  C_MOSS = hex(0x5a3d7a);
  C_STEM = hex(0x8a7a86);
  C_STEM_DK = hex(0x2c2233);
  C_GLOW = hex(0xb08cff);
  C_AMBER = hex(0xffad66);
  C_MOON = hex(0x8a8798);

  SUN = nrm(v3(0.7f, 0.42f, 0.58f));
  buildIslands();
  // la Umbría queda justo bajo el centro de la Meseta en reposo
  UMB = nrm(islandCenterWorld(IS[0]));

  MOON_C = v3(-2.2f, 1.3f, -1.2f);
  float aspect = float(W) / H;
  Camera cam(v3(0, 0, 6), v3(0), v3(0, 1, 0), 30, aspect);

  // estados del fenómeno
  float aM = 0, aG = 0, aC = 0;
  if (scene == "transform") { aM = envf("AM", 0.75f); aG = 0.35f; aC = 0.2f; PODS_OPEN = 0.f; }
  if (scene == "discover") { aM = envf("AM", 1.5f); aG = 0.9f; aC = 0.7f; PODS_OPEN = 1.f; ECLIPSE = true; }
  IS[0].angle = aM;
  IS[3].angle = aG;
  IS[4].angle = aG;
  IS[5].angle = aC;
  v3 moonEclipse = UMB * 1.0f + SUN * 3.6f;

  if (scene == "orbit" || scene == "silhouette" || scene == "chart") {
    v3 cd = sph(envf("CY", 0.6f), envf("CP", 0.5f));
    cam = Camera(cd * envf("SD", 5.6f), v3(0), v3(0, 1, 0), envf("FV", 30.f), aspect);
    if (scene == "chart") cam = Camera(nrm(UMB) * 6.f, v3(0), v3(0, 1, 0), 26, aspect);
    MOON_C = cam.pos + nrm(cam.fwd - cam.right * 0.34f + cam.up * 0.16f) * 9.f;
    CAST = false;
    if (scene == "silhouette") MOON_C = v3(100);
  } else {
    const Island& M = IS[0];
    v3 c0 = M.pivot + M.fr.t * M.off;  // centro de la Meseta en reposo
    if (scene == "approach" || scene == "transform") {
      v3 pos = c0 + M.fr.n * envf("AN", 0.3f) + M.fr.t * envf("AT", 1.1f) + M.fr.b * envf("AB", -0.6f);
      v3 tgt = M.pivot * envf("AK", 0.4f);
      cam = Camera(pos, tgt, M.fr.n, envf("AF", 62.f), aspect);
      MOON_C = cam.pos + nrm(cam.fwd + cam.up * 0.35f - cam.right * 0.6f) * 4.f;
      if (scene == "transform") {
        // de perfil, mirando a lo largo de la bisagra: el giro ocurre en el plano de la imagen
        MOON_C = moonEclipse;
        v3 hp = M.pivot + M.fr.b * envf("SB", -1.4f) + M.fr.n * envf("SN", 0.0f) + M.fr.t * envf("ST", 0.4f);
        v3 ht = M.pivot + M.fr.t * envf("SX", 0.3f) + M.fr.n * envf("SY", 0.0f);
        cam = Camera(hp, ht, M.fr.n, envf("SF", 62.f), aspect);
      }
    } else if (scene == "discover") {
      MOON_C = moonEclipse;
      v3 g = nrm(UMB + M.fr.t * envf("DT", 0.3f) + M.fr.b * envf("DB", 0.05f));
      v3 pos = g * (CORE_R + envf("DH", 0.03f));
      v3 tgt = mix(UMB * CORE_R, islandCenterWorld(M), envf("DM", 0.4f)) + M.fr.b * envf("DX", 0.f);
      cam = Camera(pos, tgt, g, envf("DF", 82.f), aspect);
      MOON_C = cam.pos + SUN * 6.5f;
    }
  }

  {
    const char* names[6] = {"meseta", "atolon", "copa", "gemela_a", "gemela_b", "concha"};
    auto anc = [&](const char* nm, v3 p) {
      float x, y;
      if (cam.project(p, x, y)) printf("ANCHOR %s %.4f %.4f\n", nm, x, y);
    };
    for (int i = 0; i < 6; i++) anc(names[i], islandCenterWorld(IS[i]));
    anc("pulvinulo", IS[0].pivot);
    anc("umbria", UMB * CORE_R);
    anc("nucleo", v3(0));
  }
  fprintf(stderr, "%s %dx%d\n", scene.c_str(), W, H);
  Image img(W, H);
  renderParallel(img, [&](int x, int y, float& a) {
    float u = (x + 0.5f) / W * 2 - 1, v = 1 - (y + 0.5f) / H * 2;
    return render(cam.pos, cam.dir(u, v), a);
  });
  img.save(out);
  return 0;
}
