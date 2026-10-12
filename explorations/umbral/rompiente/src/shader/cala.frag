#version 300 es
// UMBRAL — La Cala Interior. Las Gradas: un anfiteatro de gours bajo un jameo.
// Mismas coordenadas que rompiente.frag (metros; y = 0 pleamar, −24 bajamar).
// La sala está en el centro del brazo de la isla, sobre el túnel que nace en la
// Bóveda (boca oeste, bajo el alero) y sale a la bahía (boca este).
precision highp float;
uniform vec2 R;
uniform float L;            // nivel del mar dentro de la cala (llega por el túnel)
uniform vec3 CAM, TGT;
uniform float FOV;
uniform float STONE;        // 1 = una piedra cierra el rebosadero de la rama norte
uniform vec4 PULSE;         // (fila de origen, frente en filas, rama 0/1, intensidad)
uniform float FED;          // farolillos alimentados por el último pulso (0..1)
uniform float DBG;
out vec4 o;

const vec3 SUN = normalize(vec3(-0.62, 0.50, -0.60));

#include "common.glsl"

// ---------------------------------------------------------------- planta de la sala
const vec2 B = vec2(72.0, 404.0);          // centro de la poza madre (fondo del anfiteatro)
const vec2 K = vec2(56.0, 390.0);          // centro del jameo: el sol de la tarde cruza la sala y cae sobre las gradas altas
const float PHI0 = 0.78;                   // las gradas suben hacia el nordeste
const int NR = 8;                          // filas de gours, desiguales como en la naturaleza
// radio (desde la poza madre) del borde de cada fila y cota de su agua
const float RR[9] = float[](12.0, 19.5, 23.5, 30.0, 33.5, 40.0, 44.5, 49.5, 56.0);
const float HB[9] = float[](-20.4, -18.2, -15.2, -13.4, -10.0, -7.4, -3.4, -0.4, 2.6);
const float RIM = 0.55;                    // altura del borde sobre el fondo de la poza
const float SALT_ROW = 4.5;                // por encima, agua dulce del manantial: sin luz

float caveD(vec3 p){
  vec3 ca = vec3(-2.0, -13.0, 350.0), cb = vec3(175.0, -24.0, 470.0);
  vec3 pa = p - ca, ba = cb - ca; float hh = clamp(dot(pa, ba)/dot(ba, ba), 0.0, 1.0);
  vec3 cq = pa - ba*hh; cq.y *= 1.3;
  float rad = 12.0 + 9.0*(1.0 - smoothstep(0.0, 0.22, hh)) + 5.0*smoothstep(0.8, 1.0, hh) + 2.5*(n3(p*0.08) - 0.5);
  return length(cq) - rad;
}

// ángulo relativo al eje del anfiteatro
float rel(vec2 q){ vec2 d = q - B; return atan(d.y, d.x) - PHI0; }
float inSector(float a){ return 1.0 - smoothstep(1.25, 1.55, abs(a)); }

// borde de la fila i: una cadena de lóbulos que se curvan aguas abajo
float lobes(float a, float i, out float amp){
  float n = RR[int(i)]/(2.6 + 2.4*h21(vec2(i, 7.0)));     // lóbulos de 3 a 5 m: más numerosos cuanto más arriba
  float x = a*n + h21(vec2(i, 3.0));
  float cell = floor(x);
  float f = fract(x)*2.0 - 1.0;
  amp = 0.5 + 1.7*h21(vec2(cell, i + 11.0));                // unos vasos se adelantan mucho, otros apenas
  return sqrt(max(1.0 - f*f, 0.0));
}
// distancia "de flujo": radial desde la poza madre, deformada por el terreno
float flowR(vec2 q){
  vec2 d = q - B;
  float a = atan(d.y, d.x) - PHI0;
  // la cascada no es un círculo: baja en abanico torcido, más larga por el norte
  return length(d)*(1.0 + 0.16*sin(a*1.7 + 0.9) - 0.06*a) + 7.0*(fb2(q*0.035) - 0.5)*2.0;
}
float rimR(float a, float i){
  int k = int(i);
  float amp; float lb = lobes(a, i, amp);
  return RR[k] - amp*lb + 0.5*(n2(vec2(a*4.0, i)) - 0.5) + 2.6*sin(a*(1.3 + 0.4*h21(vec2(i, 9.0))) + i*1.7);
}
float baseH(float i){ return HB[int(clamp(i, 0.0, 8.0))]; }

// fila de una posición en planta (−1 = poza madre)
float rowOf(vec2 q, out float fr){
  float r = flowR(q), a = rel(q);
  float row = -1.0; fr = 0.0;
  for (int k = 0; k < NR; k++) {
    float rk = rimR(a, float(k));
    if (r >= rk) { row = float(k); fr = r - rk; }
  }
  return row;
}

// recorrido del agua: ángulo del rebosadero de cada fila (dos ramas bajo la horquilla)
float pathA(float i){ return 0.12*sin(i*1.3) + 0.05 + (i < 4.0 ? -0.34*(4.0 - i)/4.0 : 0.0); }   // rama sur
float pathB(float i){ return 0.12*sin(i*1.3) + 0.05 + (i < 4.0 ? 0.40*(4.0 - i)/4.0 : 0.0); }    // rama norte
float pathAng(float i, float branch){ return mix(pathA(i), pathB(i), branch); }
float activeBranch(){ return STONE > 0.5 ? 0.0 : 1.0; }    // sin piedra el agua baja por la rama norte

// altura del suelo (sin agua)
float floorH(vec2 q){
  float r = flowR(q), a = rel(q), sec = inSector(a);
  float fr; float row = rowOf(q, fr);
  float h;
  if (row < 0.0 || sec < 0.01) {
    h = -27.5 + 1.2*fb2(q*0.08);                           // la poza madre, abierta al túnel
  } else {
    float b = baseH(row);
    float w = rimR(a, min(row + 1.0, float(NR))) - rimR(a, row);
    // borde convexo: el labio mineral, luego el vaso de la poza
    float lip = exp(-pow(fr/0.9, 2.0));
    float bowl = sin(3.14159*clamp(fr/max(w, 1.0), 0.0, 1.0));
    h = b + RIM*lip - 1.1*bowl*(1.0 - lip) - 0.25;
    // cortina: el labio de la fila de arriba cae sobre esta poza como una colada convexa
    if (row < float(NR) - 0.5) {
      float bu = baseH(row + 1.0);
      float c = clamp((fr - (w - 2.6))/2.6, 0.0, 1.0);
      c = 1.0 - (1.0 - c)*(1.0 - c);                         // convexa, sin pendiente infinita
      h = max(h, mix(h, bu + RIM*0.9, c));
    }
    if (row >= float(NR)) h = b + 0.5*fb2(q*0.2) + 0.4*max(r - 56.0, 0.0);   // el manantial, sobre la última fila
  }
  // a los lados las gradas se funden en una colada mineral que sube por la pared
  float side = smoothstep(0.8, 1.2, abs(a))*(1.0 - smoothstep(1.45, 1.8, abs(a)));
  float slope = -26.0 + 0.62*max(r - 8.0, 0.0) + 2.0*fb2(q*0.1);
  h = mix(h, max(h, slope), side);
  h = mix(-27.5 + 1.2*fb2(q*0.08), h, max(sec, side));
  return h;
}

// nivel del agua en la poza de esta fila (rebosando apenas)
float poolLevel(vec2 q){
  float a = rel(q);
  float fr; float row = rowOf(q, fr);
  float lv = -1e3;
  if (row >= 0.0 && row < float(NR) && inSector(a) > 0.5 && abs(a) < 0.95 && fr > 0.6) lv = baseH(row) + RIM - 0.12;
  return max(lv, L);
}

// ---------------------------------------------------------------- volumen
float topH(vec2 q){
  float dk = length(q - K);
  return 54.0 + 6.0*fb2(q*0.02) - 30.0*(1.0 - smoothstep(16.0, 52.0, dk));   // dolina del jameo
}
float cavity(vec3 p){
  vec2 q = p.xz;
  float r = length(q - B), a = rel(q);
  float Rc = mix(30.0, 56.0, inSector(a)) + 4.0*(fb2(vec2(a*2.0, p.y*0.05)) - 0.5);
  vec4 bd = bed(p);
  Rc -= bedRelief(bd)*0.9;                                 // los mismos bancos de La Rompiente
  float hc = 25.0 - 15.0*pow(clamp(r/56.0, 0.0, 1.0), 2.0) + 2.5*(fb2(q*0.05) - 0.5);
  float ch = max(max(r - Rc, p.y - hc), -45.0 - p.y);
  float op = max(length(q - K) - 15.0 - 3.5*(fb2(vec2(atan(q.y - K.y, q.x - K.x)*2.0, p.y*0.05)) - 0.5)*2.0 + 0.2*min(p.y - 18.0, 0.0), 6.0 - p.y);
  return min(min(ch, op), caveD(p));
}

// farolillos: colonias de anémonas en el labio de cada rebosadero.
// Sus posiciones se calculan una vez por píxel (initLanterns) y el mapa solo las lee.
vec4 LAN[12];          // xyz centro, w = fila + 0.5·rama
int NL = 0;
void initLanterns(){
  NL = 0;
  for (int k = 0; k < NR; k++) {
    float i = float(k);
    for (int bch = 0; bch < 2; bch++) {
      float br = float(bch);
      if (i >= 4.0 && bch == 1) continue;                  // por encima de la horquilla el camino es uno
      float an = pathAng(i, br) + PHI0;
      // el labio está donde la distancia de flujo alcanza el borde: dos pasos de punto fijo
      vec2 dir = vec2(cos(an), sin(an));
      float target = rimR(an - PHI0, i) + 0.2, rr = target;
      rr += target - flowR(B + dir*rr);
      rr += target - flowR(B + dir*rr);
      if (NL < 12) { LAN[NL] = vec4(B.x + dir.x*rr, baseH(i) + RIM + 0.15, B.y + dir.y*rr, i + br*0.5); NL++; }
    }
  }
}
float lanterns(vec3 p, out float which){
  float best = 1e5; which = -1.0;
  for (int j = 0; j < 12; j++) {
    if (j >= NL) break;
    vec3 d = p - LAN[j].xyz;
    if (dot(d, d) > 9.0) { best = min(best, length(d) - 1.2); continue; }
    float i = LAN[j].w;
    for (int m = 0; m < 7; m++) {
      float fm = float(m);
      vec3 off = vec3(cos(fm*2.4 + i)*0.25*sqrt(fm + 1.0), -0.05 + 0.03*fm, sin(fm*2.4 + i)*0.25*sqrt(fm + 1.0));
      float sd = length((d - off)*vec3(1.0, 0.8, 1.0)) - (0.10 + 0.05*h21(vec2(fm, i)));
      if (sd < best) { best = sd; which = i; }
    }
  }
  return best;
}

// mapa: distancia + material  (1 roca · 2 gours · 3 agua · 4 farolillo)
vec2 map(vec3 p){
  vec2 q = p.xz;
  float rock = max(p.y - topH(q), -cavity(p));
  vec2 res = vec2(rock*0.6, 1.0);
  float r = length(q - B);
  if (r < 66.0 && p.y < 8.0) {
    float fh = floorH(q);
    float wl = poolLevel(q);
    float top = max(fh, wl);
    float d = (p.y - top)*0.22;
    if (d < res.x) res = vec2(d, wl > fh + 0.01 ? 3.0 : 2.0);
    float wch; float ln = lanterns(p, wch);
    if (ln < res.x) res = vec2(ln, 4.0);
  }
  return res;
}

vec3 normal(vec3 p, float t){
  float e = 0.01 + t*0.0006;
  vec2 k = vec2(1, -1);
  return normalize(k.xyy*map(p + k.xyy*e).x + k.yyx*map(p + k.yyx*e).x + k.yxy*map(p + k.yxy*e).x + k.xxx*map(p + k.xxx*e).x);
}

// normal del suelo de las gradas a partir del gradiente de la altura: estable en las cortinas
float topAt(vec2 q){ return max(floorH(q), poolLevel(q)); }
vec3 heightNormal(vec2 q){
  float e = 0.06;
  float hx = topAt(q + vec2(e, 0.0)) - topAt(q - vec2(e, 0.0));
  float hz = topAt(q + vec2(0.0, e)) - topAt(q - vec2(0.0, e));
  return normalize(vec3(-hx, 2.0*e, -hz));
}

vec2 march(vec3 ro, vec3 rd, float tmax){
  float t = 0.05, tp = 0.05;
  for (int i = 0; i < 800; i++) {
    vec3 p = ro + rd*t;
    vec2 h = map(p);
    if (h.x < min(0.0015*t, 0.05)) {
      // en las gradas, afinar el corte con la altura por bisección (las cortinas son casi verticales)
      if (h.y == 2.0 || h.y == 3.0) {
        float a = tp, b = t;
        for (int k = 0; k < 10; k++) {
          float m = 0.5*(a + b);
          vec3 q = ro + rd*m;
          if (q.y - topAt(q.xz) > 0.0) a = m; else b = m;
        }
        t = b;
        vec3 q = ro + rd*t;
        h.y = poolLevel(q.xz) > floorH(q.xz) + 0.01 ? 3.0 : 2.0;
      }
      return vec2(t, h.y);
    }
    tp = t;
    t += h.x*0.9;
    if (t > tmax) break;
  }
  return vec2(-1.0, 0.0);
}

// sombra dura: por un tragaluz el sol recorta con nitidez (y evita bandas en las cortinas)
float shadow(vec3 ro, vec3 rd, float tmax){
  float t = 1.2;
  for (int i = 0; i < 90; i++) {
    float h = map(ro + rd*t).x;
    if (h < 0.004 + 0.004*t) return 0.0;
    t += clamp(h, 0.25, 8.0);
    if (t > tmax) break;
  }
  return 1.0;
}

float ao(vec3 p, vec3 n){
  float o = 0.0, s = 1.0;
  for (int i = 1; i <= 5; i++) { float h = 0.6*float(i)*float(i); o += (h - map(p + n*h).x)*s; s *= 0.6; }
  return clamp(1.0 - 0.08*o, 0.0, 1.0);
}

vec3 sky(vec3 rd){
  float y = max(rd.y, 0.0);
  vec3 c = mix(vec3(0.70, 0.70, 0.82), vec3(0.30, 0.42, 0.66), smoothstep(0.0, 0.5, y));
  c = mix(c, vec3(0.13, 0.20, 0.40), smoothstep(0.5, 1.0, y));
  float sd = max(dot(rd, SUN), 0.0);
  c += vec3(1.0, 0.72, 0.48)*(0.6*pow(sd, 12.0) + 3.0*smoothstep(0.9993, 0.9997, sd));
  return c;
}

// ---------------------------------------------------------------- luz viva
// pulso: la luz de la deriva viaja con el agua, de rebosadero en rebosadero
float pulseAt(vec2 q, float row){
  if (PULSE.w <= 0.0) return 0.0;
  float origin = PULSE.x, front = PULSE.y, br = PULSE.z;
  if (row > origin + 0.01) return 0.0;
  if (origin - row > front) return 0.0;
  float a = rel(q);
  float salty = 1.0 - smoothstep(SALT_ROW - 0.5, SALT_ROW + 0.5, row);   // sin sal no hay deriva
  if (row < 0.0) {                                                       // la poza madre: se acumula y se queda
    float r = length(q - B);
    return salty*PULSE.w*(1.0 - smoothstep(4.0, 14.0, r))*step(origin - row, front + 0.5);
  }
  // si la fila está bajo el mar, el pulso se abre en la laguna alrededor del punto donde la cascada entra en ella
  if (baseH(max(row, 0.0)) + RIM < L) {
    float entry = -1.0;
    for (int k = 0; k < NR; k++) { if (baseH(float(k)) + RIM >= L) { entry = float(k); break; } }
    if (entry < 0.0 || origin < entry) return 0.0;
    float an = pathAng(entry, br) + PHI0;
    vec2 ep = B + vec2(cos(an), sin(an))*rimR(an - PHI0, entry);
    float reach = (front - (origin - entry))*4.5;
    return salty*PULSE.w*0.9*(1.0 - smoothstep(reach*0.6, reach, length(q - ep)))*step(0.0, reach);
  }
  float pa = pathAng(row, br);
  float w = 0.22 + 0.04*row;
  float onPath = 1.0 - smoothstep(w*0.5, w, abs(a - pa));
  // en la fila de origen la luz se abre como una mancha alrededor del punto removido
  float head = smoothstep(1.2, 0.0, abs(origin - row - front));
  return salty*PULSE.w*onPath*(0.55 + 0.45*head);
}

// el manantial: un hilo de agua dulce cae de la pared sobre la última fila
vec3 springPos(){ float an = pathAng(float(NR) - 1.0, 0.0) + PHI0; return vec3(B.x + cos(an)*60.0, 4.0, B.y + sin(an)*60.0); }
// luz que no viene de ninguna lámpara: el rebote cálido del charco de sol y el resplandor de la deriva
const vec3 SUNPOOL = vec3(B.x + 23.0, -6.0, B.y + 24.0);
vec3 fills(vec3 p){
  float ds = length(p - SUNPOOL);
  vec3 warm = vec3(1.0, 0.70, 0.42)*0.5/(1.0 + ds*ds/110.0);
  float dm = length(p.xz - B) + 0.6*max(p.y + 20.0, 0.0);
  vec3 cyan = vec3(0.15, 0.75, 0.80)*0.45*exp(-dm/16.0);
  return warm + cyan;
}

// ---------------------------------------------------------------- materiales
vec3 wallCol(vec3 p, vec3 n){
  vec4 b = bed(p);
  float ci = BC[int(b.x)];
  vec3 basalt = vec3(0.14, 0.15, 0.20), slate = vec3(0.22, 0.24, 0.30), pale = vec3(0.36, 0.36, 0.40), rust = vec3(0.36, 0.26, 0.23);
  vec3 c = ci < 0.5 ? basalt : ci < 1.5 ? slate : ci < 2.5 ? pale : rust;
  c *= 0.9 + 0.2*n3(p*0.4);
  // franjas de humedad y regueros minerales bajo las goteras
  float drip = smoothstep(0.6, 0.85, n2(vec2(atan(p.z - B.y, p.x - B.x)*18.0, p.y*0.03)));
  c = mix(c, vec3(0.62, 0.58, 0.52), 0.35*drip*smoothstep(-0.3, 0.3, -n.y + 0.6));
  // la franja intermareal también está escrita aquí dentro
  if (p.y < 0.0) c *= 0.55;
  if (p.y < -1.0 && p.y > -4.0) c = mix(c, vec3(0.60, 0.60, 0.56), 0.35*n3(p*1.5));
  // el hilo del manantial
  vec3 sp = springPos();
  float sw = length((p.xz - sp.xz)) ;
  float thread = (1.0 - smoothstep(0.6, 1.4, sw))*smoothstep(14.0, 4.0, p.y)*step(-1.0, p.y);
  c = mix(c, vec3(0.85, 0.92, 0.95), thread*(0.6 + 0.4*n2(vec2(sw*3.0, p.y*2.0))));
  // helechos colgando del borde del jameo
  float fern = smoothstep(14.0, 26.0, p.y)*smoothstep(0.45, 0.65, n3(p*0.5))*smoothstep(26.0, 18.0, length(p.xz - K));
  c = mix(c, vec3(0.30, 0.46, 0.24), fern);
  return c;
}

vec3 rimCol(vec3 p, float row){
  // las constructoras: costra mineral crema y rosada, con anillos de crecimiento
  float growth = 0.5 + 0.5*sin(flowR(p.xz)*2.2 + 2.0*n2(p.xz*0.4));
  vec3 c = mix(vec3(0.86, 0.76, 0.60), vec3(0.80, 0.62, 0.50), 0.25 + 0.3*growth);
  c *= 0.85 + 0.15*n3(p*3.0);
  return c;
}

void main(){
  if (DBG > 99.0) { vec2 q = gl_FragCoord.xy/R; vec3 p = vec3(-110.0 + q.x*300.0, -45.0 + q.y*135.0, DBG);
    initLanterns();
    float rock = max(p.y - topH(p.xz), -cavity(p));
    float fh = length(p.xz - B) < 66.0 ? floorH(p.xz) : -1e3;
    float wl = length(p.xz - B) < 66.0 ? poolLevel(p.xz) : -1e3;
    o = vec4(rock < 0.0 ? 1.0 : 0.0, p.y < fh ? 1.0 : 0.0, (p.y < wl && p.y >= fh) ? 1.0 : 0.0, 1.0); return; }
  initLanterns();
  vec2 uv = (gl_FragCoord.xy - 0.5*R)/R.y;
  vec3 fw = normalize(TGT - CAM);
  vec3 rt = normalize(cross(vec3(0, 1, 0), fw));
  vec3 up = cross(fw, rt);
  vec3 rd = normalize(fw*(0.5/tan(radians(FOV)*0.5)) + uv.x*rt + uv.y*up);
  vec3 ro = CAM;

  vec2 h = march(ro, rd, 400.0);
  if (DBG > 2.5 && DBG < 3.5) { vec3 pp = ro + rd*h.x; o = vec4((pp.x - 20.0)/120.0, (pp.y + 40.0)/60.0, (pp.z - 360.0)/120.0, 1.0); return; }
  if (DBG > 1.5 && h.x > 0.0) { vec3 pp = ro + rd*h.x; o = vec4(normal(pp, h.x)*0.5 + 0.5, 1.0); return; }
  if (DBG > 0.5 && DBG < 1.5) { o = vec4(h.x < 0.0 ? 1.0 : fract(h.x/20.0), h.y/4.0, isnan(h.x) ? 1.0 : 0.0, 1.0); return; }
  vec3 col;
  vec3 sunc = vec3(1.0, 0.80, 0.58)*3.4;
  vec3 amb = vec3(0.10, 0.09, 0.10);
  vec3 skyP = vec3(K.x, 40.0, K.y);
  if (h.x < 0.0) {
    col = sky(rd);
  } else {
    vec3 p = ro + rd*h.x;
    float mat = h.y;
    vec3 n = (mat == 2.0) ? heightNormal(p.xz) : (mat == 3.0 ? vec3(0.0, 1.0, 0.0) : normal(p, h.x));
    float fr; float row = rowOf(p.xz, fr);
    vec3 base;
    vec3 emit = vec3(0.0);
    if (mat == 1.0) base = wallCol(p, n);
    else if (mat == 2.0) {
      base = rimCol(p, row);
      float lipZone = (1.0 - smoothstep(0.6, 1.6, fr))*smoothstep(0.4, 0.8, n.y);
      base = mix(base*vec3(0.78, 0.66, 0.52), base, lipZone);   // labios crema, el resto ocre
      float steep = 1.0 - smoothstep(0.35, 0.8, n.y);
      float drape = smoothstep(0.35, 0.75, n2(vec2(rel(p.xz)*24.0, p.y*0.25)));
      base *= 1.0 - 0.22*steep*drape;                       // cortinas con regueros verticales
      base *= mix(1.0, 0.58, steep);                        // la cara del salto, mojada y más oscura que el labio

      base = mix(base, vec3(0.30, 0.31, 0.30), smoothstep(0.6, 0.95, n.y)*0.35*(1.0 - smoothstep(0.0, 1.4, fr)));
      // agua corriendo por la cara del salto, solo bajo los rebosaderos activos
      if (row >= -0.5) {
        float a = rel(p.xz);
        float rr = row + 1.0;
        float pa = pathAng(rr, activeBranch());
        float sheet = (1.0 - smoothstep(0.03, 0.08, abs(a - pa)))*step(n.y, 0.6);
        base = mix(base, vec3(0.82, 0.92, 0.92), 0.6*sheet);
      }
    } else if (mat == 4.0) {
      base = vec3(0.95, 0.55, 0.28);
    } else base = vec3(0.0);

    if (mat == 3.0) {
      // agua: fondo visto a través, reflejo del jameo, luz de la deriva
      float depth = max(poolLevel(p.xz) - floorH(p.xz), 0.0);
      float upper = smoothstep(SALT_ROW - 1.0, SALT_ROW + 1.0, row);          // filas dulces, al sol
      vec3 bottom = mix(vec3(0.05, 0.20, 0.22), vec3(0.42, 0.50, 0.24), upper); // algas de luz arriba
      vec3 wc = mix(bottom*0.9, vec3(0.02, 0.07, 0.10), 1.0 - exp(-depth/2.2));
      vec3 rf = reflect(rd, vec3(0, 1, 0));
      float toSky = smoothstep(0.92, 0.985, dot(rf, normalize(skyP - p)));
      // el agua refleja las cortinas de arriba (ocre, más claras si les da el sol) y el hueco del jameo
      float sunCurt = 1.0/(1.0 + pow(length(p.xz - SUNPOOL.xz)/16.0, 2.0));
      vec3 env = mix(vec3(0.10, 0.08, 0.07), vec3(0.95, 0.70, 0.45), sunCurt);
      vec3 refl = mix(env, sky(rf)*1.2, toSky);
      float fres = 0.06 + 0.94*pow(1.0 - max(-rd.y, 0.0), 4.0);
      float sh = shadow(p + vec3(0, 0.3, 0), SUN, 80.0);
      wc += vec3(0.35, 0.75, 0.62)*0.55*sh + vec3(0.9, 0.7, 0.4)*0.25*sh*upper;   // el sol enciende el agua clara
      wc = mix(wc, vec3(0.10, 0.36, 0.40), 0.35*exp(-depth/0.6));                // orillas someras
      col = mix(wc, refl, fres);
      col += vec3(1.0, 0.85, 0.65)*sh*pow(max(dot(reflect(rd, vec3(0, 1, 0)), SUN), 0.0), 300.0)*3.0;
      // deriva luminosa: un rumor azul en reposo, un río de luz cuando se remueve
      float salty = 1.0 - upper;
      float edge = exp(-max(depth - 0.2, 0.0)/0.5);                           // la deriva se acumula en las orillas
      float rest = salty*(0.04 + 0.05*n3(vec3(p.xz*0.4, 1.0)) + 0.18*edge)*(row < 0.0 ? 2.0 : 1.0);
      float pu = pulseAt(p.xz, row);
      float sparkle = 0.75 + 0.25*n3(vec3(p.xz*1.2, 2.0));
      emit += vec3(0.20, 0.85, 1.0)*(rest + 2.4*pu*sparkle);
      col += emit;
    } else {
      float dif = max(dot(n, SUN), 0.0);
      float sh = dif > 0.0 ? shadow(p + n*0.6, SUN, 80.0) : 0.0;
      vec3 toSkyV = normalize(skyP - p);
      float skyVis = shadow(p + n*0.6, toSkyV, length(skyP - p));
      float a = ao(p, n);
      if (mat == 2.0) a = 1.0;
      vec3 lit = sunc*dif*sh + vec3(0.42, 0.50, 0.66)*0.45*skyVis*max(dot(n, toSkyV)*0.6 + 0.4, 0.0) + amb*a;
      // rebote cálido desde las gradas soleadas y frío desde la poza madre
      lit += vec3(0.25, 0.16, 0.08)*0.5*a*clamp(-n.y + 0.3, 0.0, 1.0);
      lit += fills(p)*(0.6 + 0.4*a);
      col = base*lit;
      if (mat == 4.0) {
        // farolillos: translúcidos; se encienden en ámbar cuando el agua les trae comida
        float wch; lanterns(p, wch);
        float wi = floor(wch), wb = fract(wch)*2.0;
        float onA = (wi < 4.0) ? step(abs(wb - activeBranch()), 0.1) : 1.0;
        float fedHere = FED*onA*step(wi, PULSE.x)*step(PULSE.x - wi, PULSE.y)*(1.0 - smoothstep(SALT_ROW - 0.5, SALT_ROW + 0.5, wi));
        col = col*0.35 + vec3(1.0, 0.55, 0.22)*(0.05 + 2.2*fedHere);
      }
      // las gotas de agua en el labio también brillan cuando pasa el pulso
      if (mat == 2.0) col += vec3(0.20, 0.85, 1.0)*0.5*pulseAt(p.xz, row)*smoothstep(1.6, 0.0, fr);
      if (p.y < L + 0.05) col *= 0.5;
    }
    float fog = 1.0 - exp(-h.x*0.006);
    col = mix(col, vec3(0.05, 0.07, 0.11), fog*0.6);
  }
  // el haz del jameo: cilindro inclinado según el sol, con polvo y salitre suspendidos
  {
    vec3 a0 = vec3(K.x, 22.0, K.y);
    vec3 ax = -SUN;
    float tEnd = h.x < 0.0 ? 300.0 : h.x;
    float acc = 0.0;
    for (int i = 0; i < 48; i++) {
      float t = tEnd*(float(i) + 0.5)/48.0;
      vec3 p = ro + rd*t;
      vec3 v = p - a0;
      float along = dot(v, ax);
      float dist = length(v - ax*along);
      float inBeam = (1.0 - smoothstep(9.0, 13.0, dist))*step(-10.0, along)*step(along, 60.0)*step(p.y, 24.0);
      float dust = 0.6 + 0.8*smoothstep(0.55, 0.9, n3(p*0.7));
      acc += inBeam*dust*tEnd/48.0;
    }
    col += vec3(1.0, 0.78, 0.55)*acc*0.013;
  }
  col = col/(1.0 + 0.15*col);
  col = pow(col, vec3(0.92));
  col += (h21(gl_FragCoord.xy) - 0.5)*0.02;
  vec2 qq = gl_FragCoord.xy/R;
  col *= 0.78 + 0.22*pow(16.0*qq.x*qq.y*(1.0 - qq.x)*(1.0 - qq.y), 0.25);
  o = vec4(clamp(col, 0.0, 1.0), 1.0);
}
