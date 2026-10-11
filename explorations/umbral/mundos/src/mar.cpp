// Concepto A — El Mar Suspendido.
//
// Geografía (marco del planeta: y norte, la cámara orbital mira desde +z):
//   · La Fosa: cráter antiguo e irregular, sumergido y profundo. Su fondo es
//     el Jardín de Amarras: organismos-cinta anclados al lecho.
//   · La Cresta: lo que queda del borde del cráter, sólo en el lado norte y
//     este. Losas inclinadas y escarpe interior. En su punto más alto el
//     borde se volcó hacia dentro: el Gancho, un saliente que cuelga sobre
//     el agua y rompe la silueta del planeta.
//   · La Sima: pozo central del cráter, con terrazas de travertino.
//   · Los Dientes: torres de toba en un bajío de sal al suroeste.
//
// Fenómeno: donde cae la umbra de la luna, el mar se suelta del lecho y sube
// como una lámina. Las amarras siguen ancladas al fondo y sujetan la lámina
// desde abajo; por eso el techo de agua queda acolchado sobre el jardín.
//
// uso: mar <escena> <ancho> <alto> <salida.swhdr>
//   escenas: orbit, approach, transform, discover, chart, silhouette

#include "common.h"

// ---------------------------------------------------------------- escena
static v3 SUN;            // dirección hacia la estrella
static v3 F;              // centro de la Fosa
static Frame FF;          // marco local de la Fosa (t = este, b = norte)
static v3 MOON_C;         // centro de la luna
static float MOON_R = 0.17f;
static float LIFT = 0.f;  // altura máxima de la lámina
static float PULSE = 0.f; // amarra pulsada (descubrimiento)
static bool CHART = false;
static bool ECLIPSE = false;
static float ATM_K = 1.f;   // densidad de la atmósfera (menor a ras de suelo)

static const float RIM_A = 0.42f;  // radio angular del borde del cráter
static const float HOOK_PHI = 0.32f;

// Colores (lineales).
static v3 C_BASALT, C_BASALT_LT, C_SALT, C_SILT, C_SILT_DK, C_TUFA, C_TRAV, C_RUST, C_THREAD;
static v3 C_GLOW, C_DEEP, C_SHALLOW, C_MOON;

static v3 dirAt(float phi, float a) {
  // dirección a distancia angular a del centro de la Fosa, en el acimut phi
  v3 l(std::cos(phi) * std::sin(a), std::sin(phi) * std::sin(a), std::cos(a));
  return nrm(FF.toWorld(l));
}

static void polarF(const v3& d, float& a, float& phi) {
  v3 l = FF.toLocal(d);
  a = std::acos(clampf(l.z, -1.f, 1.f));
  phi = std::atan2(l.y, l.x);
}

// Fracción de umbra en un punto (1 = sombra total de la luna).
static float umbra(const v3& p, float* perpOut = nullptr) {
  v3 v = p - MOON_C;
  float along = -dot(v, SUN);
  if (along <= 0) { if (perpOut) *perpOut = 9; return 0; }
  float perp = len(v + SUN * along);
  if (perpOut) *perpOut = perp;
  float pen = 0.025f + along * 0.012f;
  return 1 - sstep(MOON_R - pen, MOON_R + pen, perp);
}

// Elevación de la lámina de agua en un punto de la superficie.
static float liftAt(const v3& d) {
  if (LIFT <= 0) return 0;
  float perp;
  umbra(d, &perp);
  // sube desde el borde de la sombra hacia dentro
  float k = sstep(MOON_R * 1.02f, MOON_R * 0.35f, perp + MOON_R * 0.18f * fbm(d * 9.f + v3(3), 3));
  return LIFT * k * k * (3 - 2 * k);
}

// --------------------------------------------------------------- la Sima
static v3 PIT;  // centro del pozo
struct Pool { v3 c; float r, h; };
static std::vector<Pool> POOLS;

static void buildPit() {
  PIT = dirAt(3.6f, 0.06f);
  Frame pf(PIT);
  for (int k = 0; k < 10; k++) {
    float psi = 0.4f + k * 0.83f;
    float rho = 0.03f + k * 0.0062f;
    v3 c = nrm(PIT + pf.t * (std::cos(psi) * rho) + pf.b * (std::sin(psi) * rho));
    Pool p{c, 0.0105f + 0.0016f * k + 0.003f * h2(k, 3), -0.134f + k * 0.0042f};
    POOLS.push_back(p);
  }
}

// ----------------------------------------------------------- relieve
// zone: 0 lecho, 1 cresta, 2 bajío de sal, 3 sima/travertino, 4 fosa
static float seabed(const v3& d, int* zone = nullptr, float* rimOut = nullptr) {
  float a, phi;
  polarF(d, a, phi);
  float aw = a + 0.05f * fbm(d * 3.1f, 3) + 0.018f * std::sin(phi * 3 + 1.3f);

  float h = -0.05f + 0.014f * fbm(d * 4.f, 4) + 0.004f * fbm(d * 15.f, 3);
  int z = 0;

  // cuenca del cráter
  float bowl = 1 - sstep(0.1f, 0.37f, aw);
  h -= 0.072f * bowl;
  // ondas de sedimento en el fondo (sólo se ven al vaciarse)
  if (bowl > 0.3f) {
    v3 l = FF.toLocal(d);
    float rip = std::sin(l.x * 520 + 6 * fbm(d * 30.f, 2)) * 0.0006f;
    h += rip * bowl;
    z = 4;
  }

  // bajío de sal de los Dientes (suroeste, fuera del cráter)
  v3 dc = dirAt(3.95f, 0.72f);
  float ds = len(d - dc);
  float shoal = 1 - sstep(0.1f, 0.3f, ds + 0.08f * fbm(d * 6.f, 3));
  if (shoal > 0) {
    float sh = -0.012f + 0.016f * fbm(d * 9.f, 4) + 0.01f * (1 - sstep(0.0f, 0.16f, ds));
    h = mixf(h, sh, shoal);
    if (h > -0.002f) z = 2;
  }

  // la Cresta: borde norte y este, escarpe interior, ladera exterior suave
  float r = aw - RIM_A;
  float dphi = phi - HOOK_PHI;
  if (dphi > 3.14159f) dphi -= 6.28318f;
  if (dphi < -3.14159f) dphi += 6.28318f;
  float mask = sstep(-1.55f, -1.15f, dphi) * sstep(2.35f, 1.85f, dphi);
  // dos brechas erosionadas
  mask *= 1 - 0.85f * std::exp(-sq((dphi - 1.05f) / 0.07f));
  mask *= 1 - 0.75f * std::exp(-sq((dphi + 0.78f) / 0.06f));
  float rimH = 0;
  float salar = 0;
  if (mask > 0.001f && r > -0.12f && r < 0.36f) {
    // cresta: varias cumbres, la más alta junto al Gancho
    float peak = 0.06f + 0.15f * std::exp(-sq(dphi / 0.45f)) +
                 0.07f * std::exp(-sq((dphi - 1.55f) / 0.28f)) +
                 0.05f * std::exp(-sq((dphi + 0.95f) / 0.22f)) + 0.03f * fbm(v3(dphi * 3.f, 1, 2), 3);
    float saw = dphi * 22.f + 1.5f * fbm(d * 7.f, 2);
    float fs = saw - std::floor(saw);
    float slab = 0.96f + 0.04f * sstep(0.0f, 0.6f, fs) - 0.04f * sstep(0.6f, 1.0f, fs);
    float crag = 0.72f + 0.42f * ridged(d * 7.f, 4) + 0.04f * fbm(d * 40.f, 3);
    float top = peak * slab * crag;
    float rn = r + 0.012f * fbm(d * 14.f, 3);
    float crest;
    if (rn < 0) crest = sstep(-0.065f, -0.008f, rn + 0.008f * fbm(d * 20.f, 2));
    else crest = 1 - sstep(0.0f, 0.075f, rn);
    // meseta de sal detrás de la cresta: costa recortada
    float coast = 1 - sstep(0.17f, 0.24f, rn + 0.07f * fbm(d * 5.f, 4));
    float plat = (0.014f + 0.01f * fbm(d * 11.f, 3)) * coast * sstep(-0.02f, 0.01f, rn);
    float hc = mixf(h, top, crest * mask);
    float hpl = mixf(h, plat, sstep(0.0f, 0.2f, coast) * mask * sstep(-0.01f, 0.02f, rn));
    rimH = std::max(hc, hpl);
    if (rimH > h) {
      h = rimH;
      if (crest * mask > 0.25f) z = 1;
      else if (h > -0.002f) { z = 5; salar = 1; }
    }
  }
  if (rimOut) *rimOut = sat(mask * (1 - sstep(0.0f, 0.1f, std::fabs(r))));
  (void)salar;

  // la Sima: rampa hacia el pozo, terrazas de travertino y pozo central
  float dp = len(d - PIT);
  if (dp < 0.13f) {
    float w = 1 - sstep(0.06f, 0.13f, dp);
    float slope = -0.112f - 0.03f * (1 - sstep(0.02f, 0.1f, dp));
    float hp = mixf(h, slope, w);
    for (auto& pl : POOLS) {
      float dd = len(d - pl.c);
      if (dd < pl.r * 1.6f) {
        float inside = 1 - sstep(pl.r * 0.82f, pl.r, dd);
        hp = mixf(hp, std::min(hp, pl.h), inside);
        hp += 0.0024f * std::exp(-sq((dd - pl.r) / 0.0022f));
      }
    }
    // pozo central
    float shaft = 1 - sstep(0.016f, 0.024f, dp + 0.003f * fbm(d * 60.f, 2));
    hp = mixf(hp, -0.4f, shaft);
    h = hp;
    if (w > 0.4f) z = 3;
  }
  if (zone) *zone = z;
  return h;
}

static float sdTerrain(const v3& p) {
  float r = len(p);
  float hr = r - 1;
  if (hr > 0.36f) return hr - 0.34f;
  return (hr - seabed(p / r)) * 0.24f;
}

// --------------------------------------------------------------- el Gancho
static v3 HK[5];  // dos béziers encadenadas: base, c1, medio, c2, punta
static v3 HK_W;
static void buildHook() {
  // marco local en la base: R radial, T a lo largo del borde, I hacia la Fosa
  v3 base = dirAt(HOOK_PHI, RIM_A + 0.015f);
  v3 R = base;
  v3 T = nrm(dirAt(HOOK_PHI + 0.01f, RIM_A + 0.015f) - base);
  v3 I = nrm(F - R * dot(F, R));
  auto P = [&](float t_, float r_, float i_) { return R * r_ + T * t_ + I * i_; };
  HK[0] = P(0.0f, 1.14f, 0.0f);
  HK[1] = P(-0.05f, 1.38f, 0.01f);
  HK[2] = P(0.09f, 1.52f, 0.035f);
  HK[3] = P(0.24f, 1.61f, 0.06f);
  HK[4] = P(0.29f, 1.44f, 0.1f);
  HK_W = I;  // el saliente es ancho en la dirección de la Fosa: una lámina
}
static float sdHook(const v3& p, float* tt = nullptr) {
  v3 mid = HK[2];
  float bd = len(p - mid);
  if (bd > 0.55f) return bd - 0.5f;
  float t1, t2;
  float d1 = sdBezier(p, HK[0], HK[1], HK[2], &t1);
  float d2 = sdBezier(p, HK[2], HK[3], HK[4], &t2);
  float t;
  v3 q, tan;
  if (d1 < d2) { t = t1 * 0.5f; q = bez(HK[0], HK[1], HK[2], t1); tan = nrm(bezd(HK[0], HK[1], HK[2], t1)); }
  else { t = 0.5f + t2 * 0.5f; q = bez(HK[2], HK[3], HK[4], t2); tan = nrm(bezd(HK[2], HK[3], HK[4], t2)); }
  v3 off = p - q;
  v3 w = nrm(cross(tan, HK_W));  // ancho en el plano de la curva: una ola de piedra
  float ow = dot(off, w);
  v3 rest = off - w * ow;
  float rad = mixf(0.034f, 0.004f, std::pow(t, 0.75f));
  float aspect = mixf(3.2f, 2.6f, t);
  float e = std::sqrt(ow * ow / (aspect * aspect) + dot(rest, rest));
  // estratos longitudinales: el saliente es una losa volcada, no un tubo
  float ang = std::atan2(dot(rest, cross(tan, w)), ow);
  float strata = 0.0025f * sstep(0.1f, 0.9f, std::fabs(std::sin(ang * 4.f + t * 3.f + 1.5f * vnoise(p * 14.f)))) * (1 - 0.7f * t);
  float rough = 0.009f * (ridged(p * 11.f, 3) - 0.5f) * (1 - 0.6f * t);
  if (tt) *tt = t;
  return (e - rad - strata - rough) * 0.6f;
}

// ------------------------------------------------------------ los Dientes
struct Tower { v3 d; float h, r; };
static std::vector<Tower> TOWERS;
static void buildTowers() {
  const float pa[7][4] = {
      {3.95f, 0.69f, 0.135f, 0.019f}, {4.12f, 0.74f, 0.09f, 0.015f}, {3.78f, 0.76f, 0.105f, 0.017f},
      {4.02f, 0.81f, 0.06f, 0.013f},   {3.86f, 0.64f, 0.07f, 0.012f}, {4.25f, 0.67f, 0.045f, 0.011f},
      {3.62f, 0.70f, 0.038f, 0.010f}};
  for (auto& q : pa) TOWERS.push_back({dirAt(q[0], q[1]), q[2], q[3]});
}
static float sdTowers(const v3& p, int* id = nullptr, float* hy = nullptr) {
  v3 dc = dirAt(3.95f, 0.73f);
  if (len(p - dc) > 0.35f) return len(p - dc) - 0.3f;
  float best = 1e9f;
  for (size_t i = 0; i < TOWERS.size(); i++) {
    const Tower& T = TOWERS[i];
    v3 q = p - T.d * 0.985f;
    float y = dot(q, T.d);
    float rr = len(q - T.d * y);
    float yn = sat(y / (T.h + 0.015f));
    float rad = T.r * (1.05f - 0.4f * yn * yn) * (1 + 0.05f * std::sin(y * 300 + i * 2.f) + 0.22f * fbm(p * 140.f, 3));
    float cap = y - (T.h + 0.015f) + 0.004f * vnoise(p * 60.f);
    float dd = std::max(rr - rad, std::max(cap, -y - 0.02f)) * 0.7f;
    if (dd < best) { best = dd; if (id) *id = (int)i; if (hy) *hy = y; }
  }
  return best;
}

// --------------------------------------------------------------- el agua
static float waterTop(const v3& d, float L) { return L; }
// Fondo de la lámina: el lecho elevado, acolchado por las amarras.
static float threadCell(const v3& d, float& cx, float& cy, float& dist2, float& idv);
static float waterLow(const v3& d, float sb, float L) {
  if (L <= 0) return sb;
  float low = sb + L;
  float cx, cy, d2, id;
  float g = threadCell(d, cx, cy, d2, id);
  if (g > 0) {
    // copete: el techo baja en cono hacia el punto de anclaje
    float tuft = 0.012f * g * std::exp(-d2 / (0.0042f * 0.0042f));
    low -= tuft * sat(L / 0.06f);
  }
  return low;
}
static float sdWater(const v3& p, float* lowOut = nullptr, float* LOut = nullptr) {
  float r = len(p);
  float hr = r - 1;
  if (hr > 0.25f) return hr - 0.2f;
  v3 d = p / r;
  float sb = seabed(d);
  float L = liftAt(d) * sstep(-0.006f, -0.03f, sb);
  float top = waterTop(d, L);
  // la lámina no baja al pozo: su fondo sigue el lecho recortado
  float low = waterLow(d, std::max(sb, -0.138f), L);
  if (lowOut) *lowOut = low;
  if (LOut) *LOut = L;
  float sheet = std::max(hr - top, low - hr) * 0.35f;
  // la Sima sigue llena: una columna une el techo con el pozo
  if (L > 0.002f) {
    float rad = 0.0165f + 0.004f * sstep(0.f, 0.05f, hr - (low - 0.01f)) * sstep(-0.12f, -0.2f, hr);
    float col = std::max(len(d - PIT) - rad, std::max(hr - top, -0.4f - hr));
    sheet = smin(sheet, col, 0.006f);
  }
  return sheet;
}

// --------------------------------------------------- el Jardín de Amarras
static const float CELL = 0.0155f;
static float gardenMask(const v3& d) {
  float a, phi;
  polarF(d, a, phi);
  float m = 1 - sstep(0.22f, 0.33f, a + 0.03f * fbm(d * 5.f, 3));
  m *= sstep(0.07f, 0.12f, len(d - PIT) + 0.05f * fbm(d * 16.f, 3) + 0.03f * std::sin(std::atan2(dot(d - PIT, FF.b), dot(d - PIT, FF.t)) * 2 + 1));  // claro irregular alrededor de la Sima
  m *= sstep(-0.25f, 0.25f, fbm(d * 7.f, 3) + 0.35f);
  // canal de corriente hacia la Sima: ahí no ancla nada
  {
    v3 l = FF.toLocal(d);
    float ax = 0.073f, ay = 0.068f, bx = -0.054f, by = -0.0265f;
    float vx = bx - ax, vy = by - ay;
    float h = sat(((l.x - ax) * vx + (l.y - ay) * vy) / (vx * vx + vy * vy));
    float dx = l.x - ax - vx * h, dy = l.y - ay - vy * h;
    float dc = std::sqrt(dx * dx + dy * dy) + 0.006f * fbm(d * 40.f, 2);
    m *= sstep(0.012f, 0.026f, dc - 0.02f * sq(1 - h));
  }
  return m;
}
// Devuelve >0 si la celda tiene amarra; cx, cy en coordenadas locales.
static float threadCell(const v3& d, float& cx, float& cy, float& dist2, float& idv) {
  v3 l = FF.toLocal(d);
  float u = l.x / CELL, v = l.y / CELL;
  float iu = std::floor(u), iv = std::floor(v);
  int ix = (int)iu, iy = (int)iv;
  float jx = 0.5f + (h2(ix, iy, 5) - 0.5f) * 0.5f;
  float jy = 0.5f + (h2(ix, iy, 9) - 0.5f) * 0.5f;
  cx = (iu + jx) * CELL;
  cy = (iv + jy) * CELL;
  dist2 = (l.x - cx) * (l.x - cx) + (l.y - cy) * (l.y - cy);
  idv = h2(ix, iy, 21);
  v3 cd = nrm(FF.toWorld(v3(cx, cy, std::sqrt(std::max(0.f, 1 - cx * cx - cy * cy)))));
  float g = gardenMask(cd);
  return (idv < g * 0.42f) ? 1.f : 0.f;
}
static float MU = 0.026f, MV = 0.012f;  // la Amarra Madre (coordenadas locales de la Fosa)
static v3 motherDir() { return nrm(FF.toWorld(v3(MU, MV, std::sqrt(1 - MU * MU - MV * MV)))); }
static float sdMother(const v3& p, float* hfrac = nullptr) {
  if (LIFT <= 0) return 1e9f;
  v3 md = motherDir();
  float r = len(p);
  v3 d = p / r;
  float hr = r - 1;
  float sb = seabed(md);
  float L = liftAt(md);
  float hi = waterLow(md, std::max(sb, -0.138f), L) + 0.004f;
  float y = sat((hr - sb) / std::max(hi - sb, 1e-4f));
  float off = len(d - md);
  // trenza: dos hebras enroscadas + ancla de óxido
  v3 l = FF.toLocal(d);
  float ax = l.x - MU, ay = l.y - MV;
  float tw = y * 26.f;
  float c = std::cos(tw), s_ = std::sin(tw);
  float r1 = std::sqrt(sq(ax - 0.001f * c) + sq(ay - 0.001f * s_));
  float r2 = std::sqrt(sq(ax + 0.001f * c) + sq(ay + 0.001f * s_));
  float rr = std::min(r1, r2) - 0.0008f * (1 + 2.5f * std::exp(-y * 18.f));
  float bulb = sdEllipsoid(FF.toLocal(p - md * (1 + sb)), v3(0.004f, 0.004f, 0.0025f));
  float dv = std::max(sb - 0.003f - hr, hr - hi);
  if (hfrac) *hfrac = y;
  (void)off;
  return std::min(std::max(rr * 0.8f, dv), bulb);
}
static float sdThreads(const v3& p, float* hfrac = nullptr, float* idOut = nullptr) {
  if (LIFT <= 0) return 1e9f;
  float r = len(p);
  float hr = r - 1;
  if (hr > LIFT + 0.02f || hr < -0.16f) return 1e9f;
  v3 d = p / r;
  if (len(d - F) > 0.5f) return len(d - F) - 0.45f;
  float cx, cy, d2, id;
  float g = threadCell(d, cx, cy, d2, id);
  v3 l = FF.toLocal(d);
  // distancia a la frontera de la celda (cota para no saltarse vecinas)
  float fu = l.x / CELL - std::floor(l.x / CELL), fv = l.y / CELL - std::floor(l.y / CELL);
  float edge = std::min(std::min(fu, 1 - fu), std::min(fv, 1 - fv)) * CELL + 0.0008f;
  if (g <= 0) return edge;
  v3 cd = nrm(FF.toWorld(v3(cx, cy, std::sqrt(std::max(0.f, 1 - cx * cx - cy * cy)))));
  float L = liftAt(cd);
  if (L < 0.002f) return edge;
  float sb = seabed(cd);
  float lo = sb, hi = waterLow(cd, sb, L) + 0.004f;
  float y = sat((hr - lo) / std::max(hi - lo, 1e-4f));
  // cinta: ligera torsión y vaivén
  float tw = id * 6.28f + y * 5.f;
  float sway = 0.003f * std::sin(y * 3.14159f) * (id - 0.5f) * 2;
  float dx = l.x - cx - sway, dy = l.y - cy;
  float ax = dx * std::cos(tw) + dy * std::sin(tw);
  float ay = -dx * std::sin(tw) + dy * std::cos(tw);
  float base = 1 + 1.6f * std::exp(-y * 22.f);  // ancla engrosada
  float thick = 0.45f + 1.1f * h2((int)(cx * 977), (int)(cy * 977), 3);
  float taper = 1 - 0.55f * sstep(0.6f, 1.f, y);
  float w = 0.00034f * base * thick * taper, th = 0.00011f * base * thick * taper;
  float e = std::sqrt((ax / w) * (ax / w) + (ay / th) * (ay / th));
  float dr = (e - 1) * std::min(w, th) * 0.9f;
  float dv = std::max(lo - hr, hr - hi);
  if (hfrac) *hfrac = y;
  if (idOut) *idOut = id;
  return std::min(std::max(dr, dv), edge);
}

// ---------------------------------------- lentes flotantes sobre las pozas
static float sdLenses(const v3& p) {
  if (LIFT <= 0) return 1e9f;
  if (len(p - PIT) > 0.2f) return len(p - PIT) - 0.15f;
  float best = 1e9f;
  for (size_t k = 0; k < POOLS.size(); k++) {
    const Pool& pl = POOLS[k];
    float L = liftAt(pl.c);
    float hov = pl.h + 0.004f + L * 0.04f * (0.5f + h2((int)k, 7));
    v3 c = pl.c * (1 + hov);
    Frame lf(pl.c);
    v3 q = lf.toLocal(p - c);
    float wob = 1 + 0.08f * std::sin(std::atan2(q.y, q.x) * 3 + k);
    float dd = sdEllipsoid(q, v3(pl.r * 0.7f * wob, pl.r * 0.7f, 0.0012f));
    best = std::min(best, dd);
  }
  return best;
}

// ---------------------------------------------------------------- la luna
static float sdMoon(const v3& p) { return len(p - MOON_C) - MOON_R; }

// ------------------------------------------------------------------ mapa
enum { M_NONE, M_TERRAIN, M_HOOK, M_TOWER, M_WATER, M_THREAD, M_LENS, M_MOON, M_MOTHER };
struct Hit { float d; int m; };
static Hit mapAll(const v3& p, bool withWater = true) {
  Hit h{sdTerrain(p), M_TERRAIN};
  float d;
  if ((d = sdHook(p)) < h.d) h = {d, M_HOOK};
  if ((d = sdTowers(p)) < h.d) h = {d, M_TOWER};
  if (withWater && (d = sdWater(p)) < h.d) h = {d, M_WATER};
  if ((d = sdThreads(p)) < h.d) h = {d, M_THREAD};
  if ((d = sdMother(p)) < h.d) h = {d, M_MOTHER};
  if (withWater && (d = sdLenses(p)) < h.d) h = {d, M_LENS};
  if ((d = sdMoon(p)) < h.d) h = {d, M_MOON};
  return h;
}
static float mapSolid(const v3& p) {
  return std::min(std::min(sdTerrain(p), sdHook(p)), std::min(sdTowers(p), sdMoon(p)));
}

static v3 normalOf(const v3& p, int m, float e) {
  auto f = [&](const v3& q) {
    switch (m) {
      case M_HOOK: return sdHook(q);
      case M_TOWER: return sdTowers(q);
      case M_THREAD: return sdThreads(q);
      case M_MOTHER: return sdMother(q);
      case M_LENS: return sdLenses(q);
      case M_MOON: return sdMoon(q);
      case M_WATER: return sdWater(q);
      default: return sdTerrain(q);
    }
  };
  v3 n(f(p + v3(e, 0, 0)) - f(p - v3(e, 0, 0)), f(p + v3(0, e, 0)) - f(p - v3(0, e, 0)),
       f(p + v3(0, 0, e)) - f(p - v3(0, 0, e)));
  return nrm(n);
}

static float softShadow(v3 ro, v3 rd, float tmin, float tmax, float k) {
  float res = 1, t = tmin;
  for (int i = 0; i < 90 && t < tmax; i++) {
    float h = mapSolid(ro + rd * t);
    res = std::min(res, k * h / t);
    if (res < 0.002f) return 0;
    t += clampf(h, 0.0015f, 0.06f);
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
  return sat(1 - o * 2.2f / sc);
}

// ------------------------------------------------------------ cielo
static v3 skyCol(v3 ro, v3 rd, bool stars = true) {
  v3 c = hex(0x0e0c13) * 0.6f;
  // velo de la galaxia, muy tenue
  float neb = fbm(rd * 2.2f + v3(3, 1, 0), 5);
  float band = std::exp(-sq(dot(rd, nrm(v3(0.3f, 1, -0.4f))) / 0.35f));
  c += mix(hex(0x23202c), hex(0x3a3160), 0.5f + 0.5f * neb) * (0.55f * band * sat(neb + 0.6f));
  if (stars) c += starfield(rd, 1.f, 0.9f) * 0.9f;
  // estrella (sol) y su corona
  float sd = dot(rd, SUN);
  float sunAng = std::acos(clampf(sd, -1, 1));
  float sunR = 0.016f;
  float vis = 1;
  if (ECLIPSE) {
    // la luna tapa el disco: desde dentro de la umbra se ve la corona
    float t0, t1;
    if (raySphere(ro, rd, MOON_C, MOON_R, t0, t1) && t1 > 0) vis = 0;
  }
  c += hex(0xfff3e0) * (sstep(sunR, sunR * 0.8f, sunAng) * 40.f * vis);
  c += hex(0xcfd8ff) * (0.5f * std::exp(-sunAng * 22.f) + 0.12f * std::exp(-sunAng * 5.f)) * (ECLIPSE ? 0.4f : 1.f);
  return c;
}

// Atmósfera fina: dispersión simple a lo largo del rayo.
static v3 atmosphere(v3 ro, v3 rd, float tEnd, v3& trans) {
  float t0, t1;
  trans = v3(1);
  if (!raySphere(ro, rd, v3(0), 1.09f, t0, t1)) return v3(0);
  t0 = std::max(t0, 0.f);
  t1 = std::min(t1, tEnd);
  if (t1 <= t0) return v3(0);
  const int N = 14;
  float dt = (t1 - t0) / N;
  v3 acc(0), tr(1);
  v3 beta = v3(0.7f, 0.62f, 1.25f) * 1.6f;
  for (int i = 0; i < N; i++) {
    v3 p = ro + rd * (t0 + (i + 0.5f) * dt);
    float hgt = len(p) - 1;
    float dens = std::exp(-std::max(hgt, 0.f) / 0.018f);
    float lit = sstep(-0.25f, 0.15f, dot(nrm(p), SUN));
    lit *= 1 - umbra(p) * 0.92f;
    float mu = dot(rd, SUN);
    float phase = 0.75f + 0.6f * mu * mu + 0.6f * std::pow(sat(mu), 12.f);
    v3 st = beta * (dens * dt * ATM_K);
    acc += tr * st * (lit * phase) * v3(0.95f, 1.0f, 1.0f);
    tr = tr * vexp(-st * 0.6f);
  }
  trans = tr;
  return acc * 0.55f;
}

// ----------------------------------------------------- luz del techo de agua
// Las criaturas del segundo cielo, como siluetas sobre el resplandor.
static float creatureShade(float u, float v) {
  float s = 0;
  // raya grande que gira hacia las ondas
  {
    float cx = 0.035f, cy = -0.02f, ang = 0.9f;
    float x = u - cx, y = v - cy;
    float xr = x * std::cos(ang) + y * std::sin(ang), yr = -x * std::sin(ang) + y * std::cos(ang);
    float body = std::sqrt((xr / 0.012f) * (xr / 0.012f) + (yr / 0.03f) * (yr / 0.03f));
    float wing = std::fabs(xr) / 0.05f + sq(std::fabs(yr + 0.004f - 0.25f * xr * xr / 0.05f) / 0.012f);
    float tail = (yr < 0 && std::fabs(xr) < 0.0012f && yr > -0.06f) ? 0.f : 1.f;
    s = std::max(s, 1 - sstep(0.8f, 1.0f, std::min(std::min(body, wing), tail)));
  }
  // cardumen
  for (int i = 0; i < 70; i++) {
    float a = h2(i, 1) * 6.28f, rr = 0.02f + 0.06f * h2(i, 2);
    float cx = -0.07f + std::cos(a) * rr * 0.6f + 0.02f * std::sin(i * 0.3f), cy = 0.05f + std::sin(a) * rr * 0.3f;
    float x = u - cx, y = v - cy;
    float e = (x * x) / (0.0024f * 0.0024f) + (y * y) / (0.0009f * 0.0009f);
    s = std::max(s, 1 - sstep(0.6f, 1.f, e));
  }
  return s;
}

static float STARS = 1.f;
static float WET = 0.45f;   // cuánto refleja el lecho mojado  // intensidad de los puntos de anclaje en el techo
static v3 ceilingGlow(const v3& d, float thick) {
  // El plancton del mar se enciende al agitarse: la lámina entera brilla, más
  // en el borde (donde se rasga) y alrededor de cada amarra (donde tira).
  float perp;
  umbra(d, &perp);
  float edge = sstep(MOON_R * 0.45f, MOON_R * 1.0f, perp);
  v3 l = FF.toLocal(d);
  float u = l.x, v = l.y;
  Vor2 a = voronoi2(u * 90 + 2 * fbm(d * 40.f, 2), v * 90, 0.9f, 3);
  Vor2 b = voronoi2(u * 210, v * 210 + 2 * fbm(d * 60.f, 2), 0.9f, 7);
  float ca = std::pow(sat(1 - (a.f2 - a.f1) * 6), 3.f);
  float cb = std::pow(sat(1 - (b.f2 - b.f1) * 7), 3.f);
  float caus = 0.55f * ca + 0.35f * cb;
  // velos de luz, como una aurora dentro del agua
  float veil = sat(0.45f + 1.3f * fbm(v3(u * 26, v * 9, 0.5f) + v3(fbm(d * 6.f, 2)), 4));
  float base = 0.05f + 0.55f * veil * veil + 0.6f * edge * edge;
  v3 c = mix(C_GLOW, hex(0x8a86f0) * 0.9f, 0.55f * (1 - veil)) * (base * (0.85f + 0.45f * caus));
  // estrellas del segundo cielo: los puntos de anclaje de las amarras
  {
    float cx, cy, d2, id;
    if (threadCell(d, cx, cy, d2, id) > 0) {
      float star = std::exp(-d2 / (0.0011f * 0.0011f)) * 4.f + std::exp(-d2 / (0.0045f * 0.0045f)) * 0.5f;
      c += hex(0xdffcf4) * (star * (0.6f + 0.8f * id) * STARS);
    }
  }
  // pulsos: anillos que suben desde la amarra pulsada
  if (PULSE > 0) {
    float pu = MU, pv = MV;
    float rr = std::sqrt((u - pu) * (u - pu) + (v - pv) * (v - pv));
    float ring = 0;
    for (int k = 0; k < 4; k++) {
      float R = 0.008f + k * 0.0115f;
      ring += std::exp(-sq((rr - R) / 0.0016f)) * (1 - k * 0.2f);
    }
    c += hex(0xdffcf4) * (ring * 0.9f * PULSE);
  }
  float sh = creatureShade(u, v);
  c = c * (1 - 0.82f * sh);
  return c * (0.55f + 0.45f * sat(thick / 0.06f));
}

// ------------------------------------------------------------ materiales
struct Surf { v3 alb; float rough; v3 emit; };

static Surf terrainSurf(const v3& p, const v3& n) {
  float r = len(p);
  v3 d = p / r;
  float hr = r - 1;
  int zone;
  float rim;
  seabed(d, &zone, &rim);
  Surf s{C_SILT, 0.9f, v3(0)};
  float up = dot(n, d);
  if (getenv("DBGZ")) {
    const v3 zp[6] = {v3(0.2f), v3(0.6f, 0.1f, 0.1f), v3(1), v3(1, 0.8f, 0), v3(0, 0.6f, 0), v3(0, 0, 1)};
    return Surf{zp[zone] * (rim > 0.3f ? 1.f : 0.3f), 1, v3(0)};
  }
  if (zone == 1 || (rim > 0.5f && hr > 0.02f)) {
    // basalto columnar: prismas verticales en el escarpe, cumbres meteorizadas
    float steep = 1 - sat(up);
    Vor2 vc = voronoi2(dot(d, FF.t) * 520, dot(d, FF.b) * 520, 0.8f, 4);
    float seam = sstep(0.0f, 0.09f, vc.f2 - vc.f1);
    float drum = sstep(0.0f, 0.15f, std::fabs(std::sin(hr * 260 + vc.id * 20)));
    v3 col = C_BASALT * (0.75f + 0.6f * vc.id) * (0.9f + 0.1f * drum);
    col = col * (0.45f + 0.55f * seam);
    v3 topc = mix(C_BASALT_LT * 0.8f, C_BASALT, 0.4f + 0.4f * fbm(p * 45.f, 3));
    v3 c = mix(topc, col, sstep(0.12f, 0.35f, steep));
    // sal: línea de marea y marcas altas, nítidas, sólo en el escarpe
    float salt = sstep(0.004f, 0.0f, std::fabs(hr - 0.002f)) * 0.9f;
    float marks[3] = {0.032f, 0.052f, 0.078f};
    for (int i = 0; i < 3; i++) {
      float w = 0.0006f + 0.0006f * (1 + vnoise(p * 50.f));
      float cov = 0.75f * sstep(-0.1f, 0.3f, vnoise(p * 22.f + v3(i * 3.f)));
      salt = std::max(salt, sstep(w, w * 0.4f, std::fabs(hr - marks[i] - 0.0015f * vnoise(p * 30.f))) * cov * sstep(0.15f, 0.3f, steep));
    }
    // costra en las hondonadas de la cumbre
    salt = std::max(salt, sstep(0.42f, 0.55f, fbm(p * 60.f, 3)) * (1 - steep) * 0.5f);
    c = mix(c, C_SALT, salt);
    s.alb = c;
    s.rough = 0.8f;
  } else if (zone == 2 || zone == 5) {
    float crust = sstep(-0.1f, 0.4f, fbm(p * 60.f, 4));
    s.alb = mix(mix(C_SILT, C_SALT, 0.55f), C_SALT, crust);
    // polígonos de sal
    Vor2 vv = voronoi2(dot(p, FF.t) * 400, dot(p, FF.b) * 400, 0.8f, 11);
    s.alb = s.alb * (0.82f + 0.18f * sstep(0.0f, 0.06f, vv.f2 - vv.f1));
  } else if (zone == 3) {
    float lay = 0.5f + 0.5f * std::sin(hr * 1400 + 4 * fbm(p * 50.f, 2));
    s.alb = mix(C_TRAV * 0.75f, C_TRAV, lay);
    s.alb = mix(s.alb, C_SILT_DK * 0.5f, sstep(-0.16f, -0.25f, hr));
  } else {
    // limo del lecho: más oscuro en lo hondo, motas de anclajes óxido
    float dep = sstep(-0.02f, -0.11f, hr);
    s.alb = mix(C_SILT, C_SILT_DK, dep * 0.7f + 0.3f * fbm(p * 30.f, 3));
    if (LIFT > 0) s.alb = mix(hex(0x9a94ac), hex(0x5f5a72), 0.5f + 0.5f * fbm(p * 30.f, 3));
    if (zone == 4) {
      float cx, cy, d2, id;
      if (threadCell(d, cx, cy, d2, id) > 0) {
        float hold = std::exp(-d2 / (0.0045f * 0.0045f));
        s.alb = mix(s.alb, C_RUST, hold * 0.9f);
      }
      // tallos de amarra tumbados sobre el lecho cuando hay agua
      if (LIFT <= 0) {
        float st = std::pow(sat(0.5f + 0.5f * std::sin(dot(p, FF.t) * 900 + 8 * fbm(p * 20.f, 2))), 6.f);
        s.alb = mix(s.alb, C_THREAD * 0.6f, st * gardenMask(d) * 0.5f);
        float fil = std::pow(sat(0.5f + 0.5f * std::sin(dot(d, FF.b) * 300 + 9 * fbm(d * 18.f, 3))), 5.f);
        float patch = sstep(0.0f, 0.5f, fbm(d * 13.f + v3(2, 7, 1), 4) + 0.15f);
        s.emit = C_GLOW * (0.012f * (0.3f * st + 0.7f * fil) * patch * gardenMask(d));
      }
    }
  }
  return s;
}

static v3 shadeLit(const v3& p, const v3& n, const v3& rd, const Surf& s, float aoScale) {
  float r = len(p);
  v3 up = p / r;
  float um = umbra(p);
  float sunVis = 1 - um;
  float dif = sat(dot(n, SUN));
  float sh = (dif > 0 && sunVis > 0.01f) ? softShadow(p + n * 0.002f, SUN, 0.003f, 1.2f, 18.f) : 0;
  float ao = ambOcc(p, n, aoScale);
  float dayside = sstep(-0.2f, 0.25f, dot(up, SUN));
  v3 sunCol = hex(0xfff1dc) * 3.2f;
  v3 skyAmb = mix(hex(0x1a1830), hex(0x5a7598), 0.5f + 0.5f * dot(n, up)) * (0.25f * dayside * (1 - 0.85f * um));
  v3 bounce = hex(0x2b4a5c) * (0.08f * sat(-dot(n, up) * 0.5f + 0.5f) * dayside);
  v3 col = s.alb * (sunCol * (dif * sh * sunVis) + skyAmb * ao + bounce * ao);
  // bajo la lámina: luz del techo de agua
  float L = liftAt(up);
  if (L > 0.002f) {
    v3 g = ceilingGlow(up, 0.08f);
    float topLight = 0.55f + 0.45f * dot(n, up);
    col += s.alb * g * (3.2f * topLight * ao * sat(L / 0.03f));
    // lecho mojado: refleja el segundo cielo
    v3 rr = reflect(rd, n);
    float up_r = dot(rr, up);
    if (up_r > 0.02f) {
      float hr0 = r - 1;
      float sb0 = seabed(up);
      float gap = std::max(0.002f, sb0 + L - hr0);
      v3 hitDir = nrm(p + rr * (gap / up_r));
      float fres = 0.04f + 0.96f * std::pow(1 - sat(-dot(rd, n)), 5.f);
      col += ceilingGlow(hitDir, 0.08f) * (fres * 0.9f * WET);
    }
  }
  // especular suave (roca mojada, sal)
  v3 hv = nrm(SUN - rd);
  col += sunCol * (0.04f * std::pow(sat(dot(n, hv)), 1.f / (s.rough * s.rough * 0.08f + 0.004f)) * dif * sh * sunVis * (1 - s.rough));
  return col + s.emit;
}

// ------------------------------------------------------------ trazado
static Hit march(v3 ro, v3 rd, float tmin, float tmax, float& t, bool withWater = true, int maxIt = 900) {
  t = tmin;
  Hit last{1e9f, M_NONE};
  for (int i = 0; i < maxIt && t < tmax; i++) {
    v3 p = ro + rd * t;
    Hit h = mapAll(p, withWater);
    float eps = 0.00012f + t * 0.0008f;
    if (std::fabs(h.d) < eps) return h;
    last = h;
    // si nos pasamos (dentro del sólido), retroceder
    t += (h.d < 0) ? h.d * 1.2f : std::max(h.d, eps * 0.5f);
  }
  // se agotaron los pasos rozando una pared: es un impacto
  if (t < tmax && last.d < 0.004f) return last;
  return {1e9f, M_NONE};
}

static v3 shadeThread(const v3& p, const v3& n, const v3& rd) {
  float hy, id;
  sdThreads(p, &hy, &id);
  v3 up = nrm(p);
  v3 g = ceilingGlow(up, 0.08f);
  v3 alb = mix(C_THREAD * 0.5f, C_THREAD, hy);
  float wrap = 0.5f + 0.5f * dot(n, up);
  v3 col = alb * g * (0.35f + 0.8f * wrap) * (0.25f + 0.9f * hy) * (0.5f + 0.8f * id);
  // translucidez: se funde con el techo hacia arriba
  col = mix(col, g * 1.1f, sstep(0.55f, 1.0f, hy));
  // pulso que sube por la amarra
  if (PULSE > 0) {
    v3 l = FF.toLocal(up);
    float dd = std::sqrt(sq(l.x - MU) + sq(l.y - MV));
    if (dd < 0.01f) {
      float band = std::exp(-sq((hy - 0.62f) / 0.06f)) + 0.35f * std::exp(-sq((hy - 0.3f) / 0.04f));
      col += hex(0xe8fff8) * (6.f * band * PULSE + 0.6f * PULSE * hy);
    }
  }
  return col;
}

static v3 render(v3 ro, v3 rd, float& alpha);

// Agua vista desde fuera: reflexión + refracción hacia el lecho o la lámina.
static v3 shadeWater(const v3& p, v3 n, const v3& rd, float tHit, bool fromBelow) {
  v3 up = nrm(p);
  float L = liftAt(up);
  float um = umbra(p);
  // oleaje fino en la normal
  v3 q = p * 140.f;
  float e = 0.02f;
  float w0 = fbm(q, 3), wx = fbm(q + v3(e, 0, 0), 3), wz = fbm(q + v3(0, 0, e), 3), wy = fbm(q + v3(0, e, 0), 3);
  v3 g = v3(wx - w0, wy - w0, wz - w0) / e;
  g = g - up * dot(g, up);
  float amp = fromBelow ? 0.05f : 0.022f;
  n = nrm(n - g * amp);

  if (fromBelow) {
    // techo de agua visto desde el hueco: resplandor + el eclipse a través
    float sb = seabed(up);
    float low = waterLow(up, sb, L);
    float thick = L - low;
    v3 c = ceilingGlow(up, thick);
    v3 rr = nrm(rd + n * 0.15f);
    v3 through = skyCol(p, rr, false) * 0.35f * std::exp(-thick * 8.f);
    float fres = 0.02f + 0.98f * std::pow(1 - sat(-dot(rd, n)), 5.f);
    return c + through + hex(0x0a1418) * fres;
  }

  float cosi = sat(-dot(rd, n));
  float fres = 0.02f + 0.98f * std::pow(1 - cosi, 5.f);
  // reflexión: cielo + relieve
  v3 rr = reflect(rd, n);
  v3 refl;
  {
    float tr;
    Hit h = march(p + up * 0.002f, rr, 0.002f, 1.5f, tr, false, 120);
    if (h.m != M_NONE && h.m != M_THREAD) {
      v3 hp = p + up * 0.002f + rr * tr;
      v3 hn = normalOf(hp, h.m, 0.0008f);
      Surf s = (h.m == M_TERRAIN) ? terrainSurf(hp, hn) : Surf{h.m == M_TOWER ? C_TUFA : (h.m == M_MOON ? C_MOON : C_BASALT), 0.8f, v3(0)};
      refl = shadeLit(hp, hn, rr, s, 0.01f);
    } else {
      refl = skyCol(p, rr, true);
      v3 tr3;
      refl += atmosphere(p, rr, 3.f, tr3) * 0.5f;
    }
  }
  // sol especular
  v3 hv = nrm(SUN - rd);
  float spec = std::pow(sat(dot(n, hv)), 1400.f) * 22.f + std::pow(sat(dot(n, hv)), 90.f) * 0.12f;
  v3 sunSpec = hex(0xfff1dc) * (spec * (1 - um));

  // refracción
  v3 rt = nrm(rd * 0.75f - n * (0.75f * dot(rd, n) + std::sqrt(std::max(0.f, 1 - 0.5625f * (1 - dot(rd, n) * dot(rd, n))))));
  v3 sig = v3(60.f, 30.f, 18.f);
  // el agua que sube deja el limo abajo: se vuelve clara
  sig = sig * mixf(1.f, 0.1f, sat(L / 0.012f));
  v3 trans(1), inscat(0);
  v3 body = mix(C_DEEP, C_SHALLOW, 0.15f);
  float dayside = sstep(-0.2f, 0.25f, dot(up, SUN));
  float sunIn = (1 - um) * dayside * sat(dot(up, SUN) + 0.15f);
  // marcha dentro del agua hasta el lecho o el fondo de la lámina
  float t = 0.0015f;
  v3 below(0), emitBelow(0);
  bool exitLow = false;
  v3 pe(0);
  for (int i = 0; i < 160; i++) {
    v3 pp = p + rt * t;
    float r2 = len(pp);
    v3 d2 = pp / r2;
    float sb = seabed(d2);
    float L2 = liftAt(d2);
    float low = waterLow(d2, sb, L2);
    float hr = r2 - 1;
    float dTer = (hr - sb) * 0.38f;
    float dLow = (hr - low) * 0.45f;
    float dth = sdThreads(pp);
    float dd = std::min(std::min(dTer, dLow), dth);
    if (dd < 0.0004f) {
      pe = pp;
      exitLow = (dLow < dTer - 1e-5f) && L2 > 0.0015f;
      break;
    }
    t += std::max(dd, 0.0005f);
    if (t > 0.6f) { pe = pp; break; }
  }
  if (len(pe) < 0.5f) pe = p + rt * t;  // se agotaron los pasos
  float path = t;
  trans = vexp(-sig * path);
  if (getenv("DBGW")) return v3(exitLow ? 1.f : 0.f, fres, sat(path * 5.f));
  // dispersión: el cuerpo de agua toma la luz del día y, en sombra, su resplandor
  STARS = 0.15f;
  v3 glowIn = (L > 0.002f) ? ceilingGlow(up, L) * 0.8f : v3(0);
  STARS = 1.f;
  inscat = (body * (0.18f * sunIn) + glowIn) * (v3(1) - trans);
  // emisión tenue del jardín en la Fosa, visto desde órbita
  if (!exitLow) {
    v3 pn = normalOf(pe, M_TERRAIN, 0.0008f);
    Surf s = terrainSurf(pe, pn);
    // luz del sol atenuada por la columna de agua
    float hrr = len(pe) - 1;
    float depth = std::max(0.f, liftAt(nrm(pe)) - hrr);
    v3 att = vexp(-sig * (depth / std::max(0.25f, sat(dot(nrm(pe), SUN)))));
    v3 lit = shadeLit(pe, pn, rt, s, 0.004f);
    below = lit * att;
    // las amarras dormidas brillan muy poco
    emitBelow = s.emit;
  } else {
    // sale por debajo de la lámina: hueco, amarras y lecho en sombra
    float t2;
    v3 o2 = pe - nrm(pe) * 0.001f;
    Hit h = march(o2, rt, 0.0005f, 0.6f, t2, false, 200);
    if (h.m == M_THREAD) {
      v3 hp = o2 + rt * t2;
      below = shadeThread(hp, normalOf(hp, M_THREAD, 0.0002f), rt);
    } else if (h.m != M_NONE) {
      v3 hp = o2 + rt * t2;
      v3 hn = normalOf(hp, h.m, 0.0006f);
      Surf s = (h.m == M_TERRAIN) ? terrainSurf(hp, hn) : Surf{C_TUFA, 0.8f, v3(0)};
      below = shadeLit(hp, hn, rt, s, 0.006f);
    }
  }
  v3 refr = below * trans + inscat + emitBelow * (30.f * std::exp(-path * 9.f));
  // la lámina elevada brilla desde dentro: refleja menos
  if (L > 0.002f) fres *= mixf(1.f, 0.3f, sat(L / 0.02f));
  v3 col = mix(refr, refl, fres) + sunSpec;
  // espuma de sal: las corrientes giran hacia la Sima y dibujan una espiral
  // de vetas blancas sobre el mar de tinta; orla de sal en las costas
  {
    float sb0 = seabed(up);
    float aa, phi;
    polarF(up, aa, phi);
    float spiral = phi + 2.4f * std::log(aa + 0.06f);
    float wob = 1.2f * fbm(up * 5.f, 4);
    float ph = spiral * 3.f + wob * 1.6f;
    float line = std::pow(sat(1 - std::fabs(std::sin(ph))), 7.f);
    float fine = std::pow(sat(1 - std::fabs(std::sin(ph * 4.f + 2 * fbm(up * 20.f, 2)))), 24.f) * 0.6f * line;
    float broken = 0.35f + 0.65f * sstep(-0.2f, 0.3f, fbm(up * 4.f + v3(5), 4));
    float range = sstep(0.36f, 0.5f, aa) * (1 - sstep(1.7f, 2.4f, aa));
    float streak = (line * 0.55f + fine) * broken * range;
    float coast = sstep(-0.01f, 0.0f, sb0) * (0.5f + 0.5f * vnoise(p * 300.f));
    float foam = sat(streak * 0.85f + coast) * (1 - sstep(0.0f, 0.01f, L));
    float lit = (1 - um) * sat(dot(up, SUN) + 0.1f) * 1.6f + 0.03f;
    col = mix(col, C_SALT * lit, foam * 0.8f);
  }
  return col;
}

static v3 render(v3 ro, v3 rd, float& alpha) {
  alpha = 0;
  float tb0, tb1;
  v3 col;
  float tStart = 0, tEnd = 40;
  bool hitBound = raySphere(ro, rd, v3(0), 1.75f, tb0, tb1);
  bool hitMoonB = raySphere(ro, rd, MOON_C, MOON_R * 1.05f, tb0, tb1);
  (void)hitMoonB;
  float t = 0;
  Hit h{1e9f, M_NONE};
  if (hitBound || true) {
    float a0, a1;
    float s0 = 1e9f, s1 = -1e9f;
    if (raySphere(ro, rd, v3(0), 1.75f, a0, a1) && a1 > 0) { s0 = std::min(s0, std::max(a0, 0.f)); s1 = std::max(s1, a1); }
    if (raySphere(ro, rd, MOON_C, MOON_R * 1.02f, a0, a1) && a1 > 0) { s0 = std::min(s0, std::max(a0, 0.f)); s1 = std::max(s1, a1); }
    if (s1 > 0) {
      tStart = s0;
      tEnd = s1;
      h = march(ro, rd, tStart, tEnd, t);
    }
  }
  bool inGap = false;
  {
    v3 up = nrm(ro);
    float hr = len(ro) - 1;
    float L = liftAt(up);
    if (L > 0 && hr < L && hr > seabed(up)) inGap = true;
  }
  if (h.m == M_NONE) {
    col = skyCol(ro, rd);
    if (ECLIPSE && inGap) col = col * 0.6f;
    v3 tr;
    v3 atm = atmosphere(ro, rd, 1e9f, tr);
    col = col * tr + atm;
    return col;
  }
  alpha = 1;
  v3 p = ro + rd * t;
  if (getenv("DBGM")) {
    const v3 pal[9] = {v3(0), v3(0.5f, 0.3f, 0.1f), v3(1, 0, 0), v3(1, 1, 0), v3(0, 0.3f, 1), v3(0, 1, 0), v3(0, 1, 1), v3(1, 1, 1), v3(1, 0, 1)};
    return pal[h.m] * (0.4f + 0.6f * sat(dot(normalOf(p, h.m, 0.0005f), SUN)));
  }
  if (h.m == M_MOON) {
    v3 n = nrm(p - MOON_C);
    float cr = fbm(n * 6.f, 4);
    Vor v = voronoi(n * 5.f);
    float crater = sstep(0.25f, 0.05f, v.f1) * 0.3f;
    v3 alb = C_MOON * (0.75f + 0.35f * cr - crater);
    float dif = sat(dot(n, SUN));
    // luz cenicienta del planeta
    float earth = sat(dot(n, nrm(-MOON_C))) * 0.05f;
    col = alb * (hex(0xfff1dc) * (3.f * dif) + hex(0x3e6f78) * earth);
  } else if (h.m == M_WATER) {
    v3 n = normalOf(p, M_WATER, 0.0006f);
    bool below = dot(n, rd) > 0 && inGap;
    if (below) n = -n;
    if (inGap && !below) {
      // la columna de la Sima vista desde el hueco: agua encendida
      v3 up = nrm(p);
      float fres = 0.04f + 0.96f * std::pow(1 - sat(-dot(rd, n)), 5.f);
      float hr = len(p) - 1;
      float swirl = 0.5f + 0.5f * std::sin(std::atan2(dot(up - PIT, FF.b), dot(up - PIT, FF.t)) * 5 + hr * 300 + 3 * fbm(p * 200.f, 2));
      col = ceilingGlow(up, 0.08f) * (0.9f + 0.5f * swirl) * (1.2f - 0.6f * fres) + hex(0xdffcf4) * (0.8f * fres);
      col = col * (0.6f + 0.6f * sstep(-0.2f, 0.f, hr));
    } else
    col = shadeWater(p, n, rd, t, below);
  } else if (h.m == M_THREAD) {
    col = shadeThread(p, normalOf(p, M_THREAD, 0.00015f), rd);
  } else if (h.m == M_MOTHER) {
    float hy;
    sdMother(p, &hy);
    v3 n = normalOf(p, M_MOTHER, 0.00015f);
    v3 up = nrm(p);
    v3 g = ceilingGlow(up, 0.08f);
    float wrap = 0.5f + 0.5f * dot(n, up);
    v3 alb = mix(C_RUST, C_THREAD, sstep(0.0f, 0.25f, hy));
    col = alb * g * (0.6f + 1.4f * wrap);
    float band = std::exp(-sq((hy - 0.34f) / 0.03f)) + 0.6f * std::exp(-sq((hy - 0.2f) / 0.022f)) + 0.3f * std::exp(-sq((hy - 0.09f) / 0.015f));
    col += hex(0xe8fff8) * (5.f * band * PULSE + 0.5f * PULSE * hy);
  } else if (h.m == M_LENS) {
    v3 n = normalOf(p, M_LENS, 0.0003f);
    float fres = 0.04f + 0.96f * std::pow(1 - sat(std::fabs(dot(rd, n))), 5.f);
    v3 up = nrm(p);
    v3 rr = reflect(rd, n);
    v3 refl = ceilingGlow(up, 0.08f) * (1.2f + 0.8f * sat(dot(rr, up)));
    // lo que hay debajo: el travertino en penumbra
    float t2;
    Hit hb = march(p + rd * 0.006f, rd, 0.0f, 0.3f, t2, false, 120);
    v3 under(0);
    if (hb.m != M_NONE) {
      v3 hp = p + rd * (0.006f + t2);
      v3 hn = normalOf(hp, hb.m, 0.0006f);
      under = shadeLit(hp, hn, rd, terrainSurf(hp, hn), 0.004f);
    }
    col = mix(under * v3(0.6f, 0.85f, 0.85f), refl, sat(fres + 0.25f)) + C_GLOW * 0.04f;
  } else {
    v3 n = normalOf(p, h.m, 0.0002f + t * 0.0004f);
    Surf s;
    if (h.m == M_TERRAIN) s = terrainSurf(p, n);
    else if (h.m == M_HOOK) {
      float tt;
      sdHook(p, &tt);
      float band = 0.5f + 0.5f * std::sin(tt * 90 + 3 * vnoise(p * 30.f));
      s = Surf{mix(C_BASALT, C_BASALT_LT, 0.3f + 0.5f * band) * (0.85f + 0.3f * fbm(p * 50.f, 3)), 0.8f, v3(0)};
      // sal en la cara inferior: goteo de la lámina
      float under = sat(-dot(n, nrm(p)));
      s.alb = mix(s.alb, C_SALT, sstep(0.4f, 0.9f, under) * sstep(0.0f, 0.4f, fbm(p * 70.f, 3) + 0.2f) * 0.7f);
    } else {
      int id;
      float hy;
      sdTowers(p, &id, &hy);
      float lay = 0.5f + 0.5f * std::sin(hy * 520 + 3 * vnoise(p * 70.f));
      s = Surf{mix(C_TUFA * 0.7f, C_TUFA, lay) * (0.85f + 0.25f * fbm(p * 90.f, 3)), 0.9f, v3(0)};
      float marks[3] = {0.032f, 0.052f, 0.078f};
      for (float mk : marks) s.alb = mix(s.alb, C_SALT, sstep(0.0025f, 0.f, std::fabs(hy - mk - 0.012f)) * 0.9f);
    }
    col = shadeLit(p, n, rd, s, 0.002f + 0.004f * std::min(t, 2.f));
  }
  if (CHART) return col;
  if (inGap) {
    // bruma de agua en el hueco: da profundidad al jardín
    v3 fogc = C_GLOW * 0.07f + hex(0x7f9cf0) * 0.03f;
    float k = 1 - std::exp(-t * 9.f);
    col = mix(col, fogc, k);
  }
  v3 tr;
  v3 atm = atmosphere(ro, rd, t, tr);
  return col * tr + atm;
}

// -------------------------------------------------------------- escenas
int main(int argc, char** argv) {
  std::string scene = argc > 1 ? argv[1] : "orbit";
  int W = argc > 2 ? atoi(argv[2]) : 800;
  int H = argc > 3 ? atoi(argv[3]) : 500;
  std::string out = argc > 4 ? argv[4] : "out.swhdr";

  C_BASALT = hex(0x2a2733);
  C_BASALT_LT = hex(0x5d5868);
  C_SALT = hex(0xe9ecec);
  C_SILT = hex(0x6c7a84);
  C_SILT_DK = hex(0x4a5862);
  C_TUFA = hex(0xcfc8bb);
  C_TRAV = hex(0xdcd6c9);
  C_RUST = hex(0xa4553f);
  C_THREAD = hex(0xcfe0d6);
  C_GLOW = hex(0x7fe0cf) * 0.9f;
  C_DEEP = hex(0x1c1638);
  C_SHALLOW = hex(0x2a7a72);
  C_MOON = hex(0x8a8798);

  SUN = nrm(v3(-0.5f, 0.55f, 0.55f));
  F = nrm(v3(0.42f, 0.36f, 0.83f));
  FF = Frame(F, v3(0, 1, 0));
  buildPit();
  buildHook();
  buildTowers();

  // la luna en su órbita (estado normal)
  MOON_C = v3(-1.95f, -0.95f, 1.2f);
  // posición de eclipse: entre la estrella y la Fosa
  v3 U = nrm(F + FF.b * 0.02f - FF.t * 0.03f);
  v3 moonEclipse = U * 1.0f + SUN * 3.2f;

  float aspect = float(W) / H;
  Camera cam(v3(0, 0, 6), v3(0), v3(0, 1, 0), 30, aspect);

  // cámara a ras de superficie: punto g, altura alt, mirando a target
  auto surfCam = [&](v3 g, float alt, v3 target, float fov, float roll = 0) {
    v3 up = nrm(g);
    v3 pos = up * (1 + alt);
    v3 uh = rotAxis(up, nrm(target - pos), roll);
    return Camera(pos, target, uh, fov, aspect);
  };

  v3 hookTop = HK[2];
  if (scene == "orbit" || scene == "silhouette") {
    float ca = getenv("CA") ? atof(getenv("CA")) : 0.5f;
    float cr = getenv("CR") ? atof(getenv("CR")) : 1.05f;
    v3 cd = dirAt(HOOK_PHI + 3.14159f + cr, ca);
    fprintf(stderr, "cam·sun %.2f\n", dot(cd, SUN));
    v3 upv = nrm(FF.b - cd * dot(FF.b, cd));
    float sd = getenv("SD") ? atof(getenv("SD")) : 6.4f;
    float fv = getenv("FV") ? atof(getenv("FV")) : 28.f;
    cam = Camera(cd * sd, upv * (0.15f * sd / 6.4f), upv, fv, aspect);
    MOON_C = cam.pos + nrm(cam.fwd - cam.right * 0.33f - cam.up * 0.17f) * 5.6f;
    if (scene == "silhouette") MOON_C = v3(100);
  } else if (scene == "approach") {
    ATM_K = 0.5f;
    v3 g = dirAt(HOOK_PHI + 3.3f, 0.4f);
    cam = surfCam(g, 0.1f, dirAt(HOOK_PHI, 0.25f) * 1.12f, 64);
    MOON_C = cam.pos + nrm(cam.fwd + cam.up * 0.3f - cam.right * 0.75f) * 3.0f;
  } else if (scene == "transform") {
    ATM_K = 0.5f;
    LIFT = 0.07f;
    MOON_C = moonEclipse;
    float ta = getenv("TA") ? atof(getenv("TA")) : 0.4f;
    float th = getenv("TH") ? atof(getenv("TH")) : 0.1f;
    float tf = getenv("TF") ? atof(getenv("TF")) : 0.25f;
    float tt = getenv("TT") ? atof(getenv("TT")) : 1.12f;
    float fov = getenv("TV") ? atof(getenv("TV")) : 64.f;
    v3 g = dirAt(HOOK_PHI + 3.3f, ta);
    cam = surfCam(g, th, dirAt(HOOK_PHI, tf) * tt, fov);
  } else if (scene == "chart") {
    CHART = true;
    cam = Camera(F * 6.f, v3(0), FF.b, 26, aspect);
  } else if (scene == "debug") {
    cam = surfCam(dirAt(HOOK_PHI, 0.2f), 0.5f, dirAt(HOOK_PHI, RIM_A) * 1.05f, 50);
  } else if (scene == "discover") {
    ATM_K = 0.3f;
    MOON_C = moonEclipse;
    LIFT = 0.17f;
    ECLIPSE = true;
    PULSE = 1.f;
    v3 g = dirAt(0.75f, 0.1f);
    float sg = seabed(g);
    v3 pos = g * (1 + sg + 0.03f);
    float sp = seabed(PIT);
    v3 tgt = PIT * (1 - 0.125f + 0.07f);
    (void)sp;
    cam = Camera(pos, tgt, g, 72, aspect);
    fprintf(stderr, "L cam %.3f  L pit %.3f  sb %.3f  sbpit %.3f\n", liftAt(g), liftAt(PIT), sg, sp);
  }
  (void)hookTop;

  {
    auto anc = [&](const char* nm, v3 p) {
      float x, y;
      if (cam.project(p, x, y)) printf("ANCHOR %s %.4f %.4f\n", nm, x, y);
    };
    anc("gancho", HK[3]);
    anc("cresta", dirAt(HOOK_PHI + 1.55f, RIM_A) * 1.06f);
    anc("fosa", F * 0.93f);
    anc("sima", PIT * 0.88f);
    anc("dientes", TOWERS[0].d * 1.05f);
    anc("salar", dirAt(HOOK_PHI + 0.5f, RIM_A + 0.14f));
    anc("madre", motherDir() * 0.9f);
  }
  fprintf(stderr, "%s %dx%d\n", scene.c_str(), W, H);
  Image img(W, H);
  renderParallel(img, [&](int x, int y, float& a) {
    float u = (x + 0.5f) / W * 2 - 1, v = 1 - (y + 0.5f) / H * 2;
    v3 rd = cam.dir(u, v);
    return render(cam.pos, rd, a);
  });
  img.save(out);
  return 0;
}
