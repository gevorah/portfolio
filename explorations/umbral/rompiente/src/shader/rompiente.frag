#version 300 es
// UMBRAL — La Rompiente. Un solo lugar, dos niveles de agua.
// Metros: x lateral, y altura sobre la pleamar (0), z profundidad. Bajamar en −24.
precision highp float;
uniform vec2 R;
uniform float L;          // nivel del mar
uniform vec3 CAM, TGT;
uniform float FOV;
uniform float DBG;
out vec4 o;

#define LOWW -24.0
const vec3 SUN = normalize(vec3(-0.62, 0.50, -0.60));

// ---------------------------------------------------------------- ruido
float h21(vec2 p){ p = fract(p*vec2(123.34, 456.21)); p += dot(p, p+45.32); return fract(p.x*p.y); }
float h31(vec3 p){ p = fract(p*0.3183099 + 0.1); p *= 17.0; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
float n2(vec2 p){ vec2 i = floor(p), f = fract(p); f = f*f*(3.0-2.0*f);
  return mix(mix(h21(i), h21(i+vec2(1,0)), f.x), mix(h21(i+vec2(0,1)), h21(i+vec2(1,1)), f.x), f.y); }
float n3(vec3 p){ vec3 i = floor(p), f = fract(p); f = f*f*(3.0-2.0*f);
  return mix(mix(mix(h31(i), h31(i+vec3(1,0,0)), f.x), mix(h31(i+vec3(0,1,0)), h31(i+vec3(1,1,0)), f.x), f.y),
             mix(mix(h31(i+vec3(0,0,1)), h31(i+vec3(1,0,1)), f.x), mix(h31(i+vec3(0,1,1)), h31(i+vec3(1,1,1)), f.x), f.y), f.z); }
float fb2(vec2 p){ float s = 0.0, a = 0.5; for (int i = 0; i < 5; i++){ s += a*n2(p); p = p*2.03 + 7.1; a *= 0.5; } return s; }
float fb3(vec3 p){ float s = 0.0, a = 0.5; for (int i = 0; i < 4; i++){ s += a*n3(p); p = p*2.07 + 3.3; a *= 0.5; } return s; }

float segd(vec2 p, vec2 a, vec2 b){ vec2 pa = p-a, ba = b-a; float h = clamp(dot(pa,ba)/dot(ba,ba), 0.0, 1.0); return length(pa - ba*h); }

// ---------------------------------------------------------------- geografía
// La isla en planta: un cuerpo y un brazo que se curva hacia el suroeste.
// La Rompiente es la costa oeste del brazo; los farallones prolongan su curva.
const vec2 A0 = vec2(300.0, 700.0), A1 = vec2(110.0, 470.0), A2 = vec2(55.0, 330.0), A3 = vec2(25.0, 240.0);
const vec2 S0 = vec2(-20.0, 440.0), S1 = vec2(-58.0, 432.0), S2 = vec2(-92.0, 482.0), S3 = vec2(-130.0, 542.0);

float smin(float a, float b, float k){ float h = clamp(0.5 + 0.5*(b - a)/k, 0.0, 1.0); return mix(b, a, h) - k*h*(1.0 - h); }

float armCx(float z){
  if (z < 330.0) return mix(A3.x, A2.x, clamp((z - A3.y)/(A2.y - A3.y), 0.0, 1.0)) - 30.0*max(A3.y - z, 0.0)/90.0;
  if (z < 470.0) return mix(A2.x, A1.x, (z - A2.y)/(A1.y - A2.y));
  return mix(A1.x, A0.x, clamp((z - A1.y)/(A0.y - A1.y), 0.0, 1.0));
}
float sdIsland(vec2 q){
  float arm = min(min(segd(q, A0, A1) - 64.0, segd(q, A1, A2) - 62.0), segd(q, A2, A3) - mix(44.0, 60.0, clamp((q.y - 240.0)/90.0, 0.0, 1.0)));
  float body = length((q - vec2(600.0, 820.0))/vec2(1.0, 0.8)) - 300.0;
  float d = smin(arm, body, 90.0);
  return d + 16.0*(fb2(q*0.006) - 0.5) + 5.0*(n2(q*0.04) - 0.5);
}
// "oestidad": 1 en la cara de La Rompiente, 0 en el resto de la costa
float westness(vec2 q){ return smoothstep(10.0, -30.0, q.x - armCx(q.y))*smoothstep(640.0, 520.0, q.y); }
// vuelo del alero: nace en la punta, culmina y se apaga hacia el cuerpo de la isla
float overhang(vec2 q){ return 54.0*westness(q)*smoothstep(225.0, 430.0, q.y)*(1.0 - smoothstep(470.0, 600.0, q.y)); }
float crestH(vec2 q, float O){ return 38.0 + 40.0*(O/54.0) + 10.0*(fb2(vec2(q.y*0.012, 7.0)) - 0.5); }
float landH(vec2 q, float s){
  return 34.0 + 24.0*smoothstep(0.0, 55.0, s) + 70.0*smoothstep(480.0, 850.0, q.y)*smoothstep(30.0, 220.0, s)
       + 16.0*(fb2(q*0.012) - 0.5);
}

// estratos: misma serie en todo el lugar (acantilado, farallones, isleta)
float strataQ(vec3 p){ float q = (p.y + 0.035*p.z - 0.02*p.x)/7.0 + 0.35*n2(p.xz*0.012); return q + 0.22*sin(q*1.9); }
float softLayer(vec3 p){ float f = fract(strataQ(p)); return smoothstep(0.0, 0.12, f)*(1.0 - smoothstep(0.5, 0.62, f)); }

// la rasa mareal: plataforma tallada por el mar al pie del acantilado
const vec2 CH0 = vec2(-100.0, 296.0), CH1 = vec2(-66.0, 318.0), CH2 = vec2(-34.0, 334.0), CH3 = vec2(-4.0, 350.0);
float channel(vec2 q){ return min(min(segd(q, CH0, CH1), segd(q, CH1, CH2)), segd(q, CH2, CH3)); }
float stackLine(vec2 q){ return min(min(segd(q, S0, S1), segd(q, S1, S2)), segd(q, S2, S3)); }
// distancia (negativa dentro) al borde exterior de la rasa
float rasaIn(vec2 q, float s){
  float W = 24.0 + 72.0*westness(q)*smoothstep(200.0, 290.0, q.y) + 14.0*n2(q*0.02);
  float a = -(s + W);
  float b = stackLine(q) - 46.0 - 14.0*n2(q*0.03);
  return min(a, b);
}
// costillas de estrato: la rasa corta capas inclinadas y deja crestas paralelas
float ribQ(vec2 q){ return dot(q, normalize(vec2(0.82, -0.57)))/4.2 + 1.8*n2(q*0.012) + 0.6*n2(q*0.05); }
float rasaH(vec2 q, float e){
  // casi plana, con una leve pendiente hacia el mar
  float h = -17.6 - 2.6*(1.0 - smoothstep(0.0, 60.0, e)) + 0.5*fb2(q*0.03);
  float f = fract(ribQ(q));
  float hard = step(0.45, h21(vec2(floor(ribQ(q)), 1.0)));
  h += (0.10 + 0.32*hard)*smoothstep(0.0, 0.25, f)*(1.0 - smoothstep(0.5, 0.8, f));   // costillas bajas
  h += 0.7*smoothstep(0.42, 0.58, n2(q*0.012 + 4.0));          // escalones de abrasión, suaves
  // cabezas de arrecife: asoman apenas en pleamar y rompen la ola
  float heads = smoothstep(0.70, 0.85, n2(q*0.035 + 31.0))*exp(-pow((e - 12.0)/12.0, 2.0));
  h += heads*12.0;
  h -= 1.3*smoothstep(0.62, 0.66, n2(q*0.045 + 11.0));         // pozas
  float c = channel(q);                                          // canal hacia la cueva
  h = mix(h, -27.0, 1.0 - smoothstep(3.0, 8.0, c + 3.0*n2(q*0.1)));
  return h;
}

// cueva: túnel que atraviesa el brazo bajo el alero y baja hacia la bahía; luz al fondo
float caveD(vec3 p){
  vec3 ca = vec3(-2.0, -13.0, 350.0), cb = vec3(175.0, -24.0, 470.0);
  vec3 pa = p - ca, ba = cb - ca; float hh = clamp(dot(pa, ba)/dot(ba, ba), 0.0, 1.0);
  vec3 cq = pa - ba*hh; cq.y *= 1.3;
  float rad = 12.0 + 9.0*(1.0 - smoothstep(0.0, 0.22, hh)) + 5.0*smoothstep(0.8, 1.0, hh) + 2.5*(n3(p*0.08) - 0.5);
  return length(cq) - rad;
}

// barra de arena: une la rasa con la isleta
const vec2 B0 = vec2(-130.0, 542.0), B1 = vec2(-70.0, 650.0), B2 = vec2(30.0, 760.0), B3 = vec2(110.0, 822.0);
float barD(vec2 q){ return min(min(segd(q, B0, B1), segd(q, B1, B2)), segd(q, B2, B3)); }
const vec2 ISLETA = vec2(160.0, 840.0);

// farallones: lo que quedó de la punta derrumbada de La Rompiente
float stack(vec3 p, vec2 c, float r, float top, float seed){
  vec2 d = p.xz - c;
  d -= vec2(0.10, 0.04)*max(p.y + 18.0, 0.0);               // inclinación del estrato
  float q = strataQ(p);
  float k = floor(q), f = fract(q);
  // cada capa resiste distinto: unas sobresalen, otras se vacían
  float lr = 0.80 + 0.45*h21(vec2(k, seed));
  float lr2 = 0.80 + 0.45*h21(vec2(k + 1.0, seed));
  float layer = mix(lr, lr2, smoothstep(0.82, 1.0, f));
  vec2 off = (vec2(h21(vec2(k, seed + 3.0)), h21(vec2(k, seed + 5.0))) - 0.5)*r*0.35*smoothstep(-2.0, 12.0, p.y);
  d -= off;
  float ft = clamp((p.y + 18.0)/(top + 18.0), 0.0, 1.0);
  float rr = r*layer*(1.2 - 0.5*ft*ft);
  rr *= 1.0 + 0.3*smoothstep(-4.0, -20.0, p.y);             // pie ancho
  rr *= 1.0 - 0.28*smoothstep(-6.0, 1.0, p.y)*smoothstep(4.0, -2.0, p.y); // muesca de marea
  float ang = atan(d.y, d.x);
  rr *= 1.0 + 0.22*(n2(vec2(ang*1.6 + seed, k*0.7)) - 0.5)*2.0 + 0.12*sin(ang*2.0 + seed);
  float side = length(d*vec2(1.0, 1.25)) - rr + 1.2*(n3(p*0.25) - 0.5);
  float tp = p.y - (top + 5.0*n2(p.xz*0.08 + seed) - 0.06*dot(d, d));
  return max(side*0.6, tp);
}

float islandDome(vec2 q, vec2 c, vec2 r, float h){
  float d = length((q - c)/r);
  float sh = 1.0 - smoothstep(0.3, 1.0, d + 0.25*(fb2(q*0.01) - 0.5));
  return -40.0 + (h + 40.0)*sh + 6.0*fb2(q*0.02)*sh;
}

// mapa: distancia + material
// 1 roca · 2 rasa · 3 arena · 4 farallón · 5 isleta · 6 islas lejanas · 7 bloques · 9 fondo
vec2 map(vec3 p){
  vec2 res = vec2(1e5, 0.0);
  vec2 q = p.xz;
  float isl = sdIsland(q);
  float s = -isl;                                   // >0 tierra adentro
  // --- la isla y La Rompiente
  if (s > -95.0) {
    float O = overhang(q);
    float ct = crestH(q, O);
    float t = clamp((p.y + 18.0)/(ct + 18.0), 0.0, 1.0);
    float face = -O*pow(t, 3.6);
    face += 0.30*max(p.y, 0.0)*(1.0 - westness(q));        // fuera de la cara oeste, acantilado tendido
    face += 5.0*exp(-pow((p.y + 1.0)/3.5, 2.0));            // muesca de pleamar
    face += 4.0*exp(-pow((p.y + 15.0)/3.0, 2.0));           // muesca de bajamar
    face += (0.3 + 1.8*h21(vec2(floor(strataQ(p)), 9.0)))*softLayer(p);   // estratos: cada capa se vacía distinto
    face += 7.0*(n2(vec2(p.z*0.045 + p.x*0.02, p.y*0.012)) - 0.5);   // contrafuertes
    face += 5.0*(fb3(p*0.025) - 0.5) + 2.0*(n3(p*0.12) - 0.5) + 9.0*t*t*(fb3(p*vec3(0.05, 0.02, 0.05) + 3.0) - 0.5);
    float jz = p.z/53.0 + 0.012*p.y + 0.6*n2(vec2(p.y*0.015, p.z*0.006));
    float j = abs(fract(jz) - 0.5)*53.0;
    face += (0.5 + 2.0*h21(vec2(floor(jz), 4.0)))*(1.0 - smoothstep(0.0, 4.0, j));            // diaclasas irregulares
    float dSide = face - s;
    // dorso de ola: la cresta justo detrás del labio, el lomo baja hacia la isla
    float lh = landH(q, max(s, 0.0));
    float wv = O/54.0;
    float bump = 1.0 - smoothstep(0.0, 75.0, s);
    float top = mix(lh, ct + 6.0*wv*(1.0 - smoothstep(-O, 0.0, s)), bump*smoothstep(0.0, 0.3, wv)) - 7.0*wv*(1.0 - smoothstep(-O - 2.0, -O + 10.0, s))*(0.6 + 0.8*n2(q*0.06))
              - 4.0*exp(-pow(s/5.0, 2.0))*(1.0 - wv) + 4.0*(fb2(q*0.03) - 0.5);
    float dTop = p.y - top;
    float d = max(dSide*0.6, dTop*0.7);
    // labio: un borde grueso que se vence ligeramente hacia abajo
    if (O > 1e9) {
      vec2 sy = vec2(s, p.y);
      vec2 la = vec2(-O + 6.0, ct - 4.0), lb = vec2(-O + 8.0, ct - 13.0 - 0.08*O);
      vec2 pa2 = sy - la, ba2 = lb - la; float h2 = clamp(dot(pa2, ba2)/dot(ba2, ba2), 0.0, 1.0);
      float lip = length(pa2 - ba2*h2) - (7.0 - 2.0*h2) + 2.0*(n3(p*0.1) - 0.5);
      lip = max(lip, -(O - 18.0));
      d = smin(d, lip*0.7, 7.0);
    }
    d = max(d, -caveD(p)*0.8);
    if (d < res.x) res = vec2(d, 1.0);
  } else res = vec2((-s - 80.0)*0.6, 1.0);
  // --- rasa mareal
  if (p.y > 3.0) res.x = min(res.x, p.y - 2.0);
  else {
    float e = -rasaIn(q, s);
    float d = 1e5;
    if (e > -45.0) {
      float rh = mix(-36.0, rasaH(q, e), smoothstep(-22.0 + 8.0*n2(q*0.05), 4.0, e));
      d = (p.y - rh)*0.32;
      d = max(d, -caveD(p)*0.8);
    } else d = (-e - 45.0)*0.5 + max(p.y + 38.0, 0.0)*0.0 + 2.0;
    if (d < res.x) res = vec2(d, 2.0);
  }
  // --- bloques caídos de la punta
  {
    vec3 bq0 = p - vec3(-30.0, -17.0, 300.0);
    if (length(bq0) < 70.0) {
      vec2 cell = floor(bq0.xz/9.0);
      float best = 1e5;
      for (int i = -1; i <= 1; i++) for (int k = -1; k <= 1; k++) {
        vec2 c = cell + vec2(i, k);
        vec2 cw = (c + 0.5)*9.0;
        float near = 1.0 - smoothstep(14.0, 34.0, segd(cw + vec2(-30.0, 300.0), vec2(-20.0, 270.0), vec2(-40.0, 320.0)));
        if (h21(c + 5.5) > 0.15 + 0.5*(1.0 - near) || length(cw) > 60.0) continue;
        if (sdIsland(cw + vec2(-30.0, 300.0)) > 30.0) continue;      // solo al pie del acantilado
        float r = 1.8 + 4.0*h21(c + 3.1);
        vec2 off = (vec2(h21(c), h21(c + 9.7)) - 0.5)*5.0;
        vec3 cc = vec3(cw.x + off.x, -0.5 + r*0.3, cw.y + off.y);
        vec3 bq = bq0 - cc; float an = h21(c + 2.2)*6.28; bq.xz = mat2(cos(an), -sin(an), sin(an), cos(an))*bq.xz;
        vec3 bx = vec3(r, r*(0.5 + 0.4*h21(c + 4.4)), r*(0.6 + 0.5*h21(c + 6.6)));
        vec3 qq = abs(bq) - bx*0.55;
        best = min(best, length(max(qq, 0.0)) + min(max(qq.x, max(qq.y, qq.z)), 0.0) - bx.y*0.45);
      }
      best += 1.0*(n3(p*0.25) - 0.5);
      if (best*0.7 < res.x) res = vec2(best*0.7, 7.0);
    }
  }
  // --- farallones
  {
    float d = stack(p, S1, 7.0, -4.0, 7.0);
    d = min(d, stack(p, S2, 12.0, 48.0, 4.0));
    d = min(d, stack(p, S3, 9.0, 30.0, 1.0));
    if (d < res.x) res = vec2(d, 4.0);
  }
  // --- barra de arena
  if (p.y > -10.0) res.x = min(res.x, (p.y + 19.0)*0.9);
  else {
    float bd = barD(q);
    float w = 24.0 + 10.0*n2(q*0.02);
    float bh = -20.5 - 9.0*pow(bd/w, 2.0) + 0.5*n2(q*0.2);
    float d = (p.y - bh)*0.5;
    if (d < res.x) res = vec2(d, 3.0);
  }
  // --- isleta
  {
    vec2 iq = q - ISLETA;
    float r = length(iq*vec2(1.0, 1.4));
    float body = r - (58.0 + 10.0*fb3(p*0.03) - 4.0*softLayer(p) - 0.25*max(p.y, 0.0));
    float top = p.y - (26.0 + 8.0*fb2(q*0.03) - 0.004*r*r);
    float d = max(body*0.6, top*0.6);
    float ring = max((p.y - (-18.5 + 1.5*fb2(q*0.05)))*0.6, (r - 104.0 - 12.0*n2(q*0.03))*0.6);
    d = min(d, ring);
    if (d < res.x) res = vec2(d, 5.0);
  }
  // --- archipiélago: un arco de islas sobre la misma dorsal
  if (p.z > 900.0) {
    float hgt = -40.0;
    hgt = max(hgt, islandDome(q, vec2(-120.0, 1150.0), vec2(130.0, 90.0), 48.0));
    hgt = max(hgt, islandDome(q, vec2(-420.0, 1500.0), vec2(170.0, 110.0), 62.0));
    hgt = max(hgt, islandDome(q, vec2(-820.0, 1700.0), vec2(150.0, 90.0), 40.0));
    hgt = max(hgt, islandDome(q, vec2(-1250.0, 1750.0), vec2(220.0, 120.0), 34.0));
    hgt = max(hgt, islandDome(q, vec2(-1700.0, 1600.0), vec2(160.0, 90.0), 24.0));
    hgt = max(hgt, islandDome(q, vec2(-2100.0, 1350.0), vec2(120.0, 70.0), 18.0));
    float d = (p.y - hgt)*0.5;
    if (d < res.x) res = vec2(d, 6.0);
  }
  // --- fondo marino
  {
    float d = p.y - (-46.0 + 6.0*n2(q*0.01));
    if (d < res.x) res = vec2(d, 9.0);
  }
  return res;
}

vec3 normal(vec3 p, float t){
  float e = 0.02 + t*0.0008;
  vec2 k = vec2(1, -1);
  return normalize(k.xyy*map(p + k.xyy*e).x + k.yyx*map(p + k.yyx*e).x + k.yxy*map(p + k.yxy*e).x + k.xxx*map(p + k.xxx*e).x);
}

vec2 march(vec3 ro, vec3 rd, float tmax, int n){
  float t = 0.5;
  for (int i = 0; i < 700; i++) {
    if (i >= n) break;
    vec3 p = ro + rd*t;
    vec2 h = map(p);
    if (h.x < min(0.002*t, 0.4)) return vec2(t, h.y);
    t += h.x*0.9;
    if (t > tmax) break;
  }
  return vec2(-1.0, 0.0);
}

float shadow(vec3 ro, vec3 rd){
  float res = 1.0, t = 0.8;
  for (int i = 0; i < 70; i++) {
    float h = map(ro + rd*t).x;
    res = min(res, 10.0*h/t);
    t += clamp(h, 0.6, 30.0);
    if (res < 0.001 || t > 700.0) break;
  }
  return clamp(res, 0.0, 1.0);
}

float ao(vec3 p, vec3 n){
  float o = 0.0, s = 1.0;
  for (int i = 1; i <= 5; i++) { float h = 1.5*float(i)*float(i); o += (h - map(p + n*h).x)*s; s *= 0.6; }
  return clamp(1.0 - 0.035*o, 0.0, 1.0);
}

// ---------------------------------------------------------------- cielo
vec3 fogc(vec3 rd){ return mix(vec3(0.62, 0.63, 0.78), vec3(0.96, 0.76, 0.64), 0.7*pow(max(dot(rd, SUN), 0.0), 3.0)); }
vec3 sky(vec3 rd){
  float y = max(rd.y, 0.0);
  float sd = max(dot(rd, SUN), 0.0);
  vec3 hor = fogc(rd);
  vec3 c = mix(hor, vec3(0.36, 0.45, 0.66), smoothstep(0.0, 0.22, y));
  c = mix(c, vec3(0.11, 0.17, 0.36), smoothstep(0.18, 0.75, y));
  c += vec3(1.0, 0.62, 0.38)*0.45*pow(sd, 10.0) + vec3(1.0, 0.72, 0.52)*0.22*pow(sd, 2.0)*(1.0 - smoothstep(0.0, 0.4, y));
  // nubes: bancos altos, peinados por el viento
  vec2 uv = rd.xz/(rd.y + 0.12);
  float cl = fb2(uv*vec2(0.9, 2.6) + vec2(3.0, 0.0));
  cl = smoothstep(0.50, 0.80, cl)*smoothstep(0.03, 0.12, rd.y)*(1.0 - smoothstep(0.30, 0.6, rd.y));
  vec3 cc = mix(vec3(0.56, 0.56, 0.72), vec3(1.0, 0.80, 0.66), 0.25 + 0.75*pow(sd, 2.0));
  c = mix(c, cc, cl*0.6);
  // luna
  vec3 md = normalize(vec3(0.39, 0.37, 0.84));
  float m = dot(rd, md);
  vec3 moon = vec3(0.90, 0.90, 0.95)*(0.85 + 0.15*n2(rd.xy*900.0));
  c = mix(c, moon, smoothstep(0.99975, 0.99985, m));
  c += vec3(0.5, 0.55, 0.75)*0.10*pow(max(m, 0.0), 300.0);
  return c;
}


// ---------------------------------------------------------------- materiales
vec3 layerCol(float k){
  // paquetes de estratos: basalto, pizarra, toba clara y un nivel mineral cálido
  float r = n2(vec2(k*0.45, 2.0))*0.7 + h21(vec2(k, 2.0))*0.3;
  vec3 basalt = vec3(0.30, 0.33, 0.40), slate = vec3(0.45, 0.49, 0.56), pale = vec3(0.60, 0.61, 0.64), rust = vec3(0.58, 0.46, 0.40);
  vec3 c = mix(basalt, slate, smoothstep(0.25, 0.5, r));
  c = mix(c, pale, smoothstep(0.62, 0.75, r));
  c = mix(c, rust, smoothstep(0.80, 0.9, r));
  return c;
}
vec3 rockCol(vec3 p, vec3 n){
  float q = strataQ(p);
  float k = floor(q), f = fract(q);
  vec3 c = mix(layerCol(k), layerCol(k + 1.0), smoothstep(0.75, 1.0, f));
  c *= 1.0 - 0.10*softLayer(p);
  c *= 0.90 + 0.10*n3(p*0.15) + 0.08*n3(p*0.7);
  // regueros de escorrentía bajo los salientes
  float streak = smoothstep(0.55, 0.9, n2(vec2(p.x*0.3 + p.z*0.3, p.y*0.012)));
  c *= 1.0 - 0.22*streak*smoothstep(0.3, -0.2, n.y);
  return c;
}

// franja intermareal: lo que siempre queda escrito en la roca
vec3 tidal(vec3 c, vec3 p, vec3 n){
  float y = p.y;
  if (y > 9.0) return c;
  // líquenes naranjas en la zona de salpicadura (encima de la pleamar)
  float lich = 0.0*smoothstep(0.62, 0.72, n3(p*0.9))*smoothstep(9.0, 3.0, y)*step(0.0, y);
  c = mix(c, vec3(0.86, 0.64, 0.42), lich*0.4);
  if (y > 0.0) return c;
  vec3 w = c*0.55 + vec3(0.015, 0.025, 0.035);
  float flr = smoothstep(0.55, 0.8, n.y);
  // paredes: zonación por bandas (lo que siempre queda escrito en la roca)
  float barn = smoothstep(-4.0, -1.5, y)*smoothstep(0.6, -0.5, y);
  float alg = smoothstep(-5.0, -8.0, y)*smoothstep(-17.0, -13.0, y)*smoothstep(0.42, 0.62, n3(p*vec3(0.35, 0.9, 0.35)));
  float kelp = smoothstep(-15.0, -19.0, y)*smoothstep(0.5, 0.7, n3(p*vec3(0.5, 0.12, 0.5)));
  // suelos: manchas nítidas, no camuflaje
  float rq = fract(ribQ(p.xz));
  float mats = (1.0 - smoothstep(0.55, 0.75, rq)*(1.0 - smoothstep(0.92, 1.0, rq)))*0.0 + smoothstep(0.6, 0.8, rq)*smoothstep(0.35, 0.55, n2(p.xz*0.06 + 5.0));
  float crust = smoothstep(0.66, 0.70, n2(p.xz*0.11 + 9.0));
  barn = mix(barn, crust*0.7, flr);
  alg = mix(alg, mats*smoothstep(-10.0, -13.0, y), flr);
  kelp = mix(kelp, smoothstep(0.66, 0.70, n2(p.xz*0.05 + 17.0))*smoothstep(-19.0, -22.0, y), flr);
  w = mix(w, vec3(0.64, 0.64, 0.60), barn*(0.3 + 0.4*n3(p*1.2)));
  w = mix(w, vec3(0.20, 0.32, 0.22), alg*0.8);
  w = mix(w, vec3(0.30, 0.27, 0.16), kelp*0.85);
  float cor = smoothstep(-16.0, -20.0, y)*smoothstep(0.74, 0.8, n3(p*0.9));
  w = mix(w, vec3(0.70, 0.52, 0.56), cor*0.25);
  return w;
}

vec3 shade(vec3 p, vec3 n, vec3 rd, float mat, float t, bool cheap){
  vec3 c;
  bool wetSurf = p.y < 0.0;
  if (mat == 3.0) {
    c = vec3(0.80, 0.73, 0.58);
    c *= 0.9 + 0.12*sin(p.x*0.9 + p.z*0.5 + 2.0*n2(p.xz*0.1));    // ripples
    if (p.y < -20.0) c *= 0.75;
  } else if (mat == 9.0) {
    c = vec3(0.35, 0.40, 0.38);
  } else if (mat == 6.0) {
    c = mix(vec3(0.30, 0.36, 0.33), vec3(0.42, 0.52, 0.36), smoothstep(0.5, 0.9, n.y));
    if (p.y < -16.0) c = vec3(0.78, 0.72, 0.58);
  } else {
    c = rockCol(p, n);
    if (mat == 2.0) {
      float rq = ribQ(p.xz);
      float hard = step(0.45, h21(vec2(floor(rq), 1.0)));
      c = mix(vec3(0.27, 0.30, 0.33), vec3(0.46, 0.48, 0.50), hard*smoothstep(0.1, 0.2, fract(rq))*(1.0 - smoothstep(0.55, 0.7, fract(rq))));
    }
    if (mat == 7.0) c = mix(c, vec3(0.62, 0.62, 0.62), 0.25);
    c = tidal(c, p, n);
    // vegetación contenida: solo donde hay suelo, lejos del agua
    float veg = smoothstep(0.70, 0.9, n.y)*smoothstep(6.0, 14.0, p.y);
    // abrigo: la cresta expuesta queda desnuda, la hierba se refugia en el lomo y las vaguadas
    float exposed = mat == 1.0 ? westness(p.xz)*smoothstep(-overhang(p.xz) + 40.0, -overhang(p.xz) + 5.0, -sdIsland(p.xz)) : 0.0;
    veg *= smoothstep(0.42, 0.55, fb2(p.xz*0.025) + 0.15*n2(p.xz*0.3)) * (1.0 - 0.9*exposed);
    vec3 g = mix(vec3(0.20, 0.30, 0.21), vec3(0.40, 0.52, 0.32), n3(p*0.2));
    g = mix(g, vec3(0.56, 0.58, 0.34), 0.3*smoothstep(0.6, 0.8, n3(p*0.07 + 3.0)));
    c = mix(c, g, veg);
    // pozas y canal en bajamar
    if (mat == 2.0 && p.y < -12.0 && p.y > L) {
      float pool = smoothstep(0.655, 0.665, n2(p.xz*0.045 + 11.0)) + (1.0 - step(5.5, channel(p.xz)));
      if (pool > 0.5 && n.y > 0.93) {
        vec3 rf = reflect(rd, vec3(0, 1, 0));
        c = mix(vec3(0.16, 0.42, 0.42), sky(rf)*0.9, 0.55);
        // anémonas y estrellas en los bordes
        float an = smoothstep(0.90, 0.97, n2(p.xz*1.3))*smoothstep(0.66, 0.68, n2(p.xz*0.045 + 11.0) + 0.02);
        c = mix(c, vec3(0.95, 0.45, 0.45), an*0.8);
        // bajo el alero, en la sombra, las pozas guardan luz propia
        float sI = -sdIsland(p.xz), Ov = overhang(p.xz);
        float under = smoothstep(14.0, 28.0, Ov)*smoothstep(-Ov - 10.0, -Ov + 10.0, sI);
        c += vec3(0.22, 0.95, 0.80)*0.75*under*(0.6 + 0.4*n2(p.xz*0.5));
        return c;
      }
    }
  }
  // dentro de la cueva: vida que brilla en la penumbra (solo visible en bajamar)
  float glowCave = 0.0;
  if (p.y < -6.0 && p.y > L - 0.5) {
    float cd = caveD(p);
    if (cd > -2.0 && cd < 3.0 && p.x > -6.0) glowCave = smoothstep(0.55, 0.8, n3(p*0.35))*smoothstep(-6.0, -20.0, p.y);
  }
  // luz
  float dif = max(dot(n, SUN), 0.0);
  float sh = cheap ? 1.0 : shadow(p + n*0.3, SUN);
  float a = cheap ? 1.0 : ao(p, n);
  dif = smoothstep(0.0, 0.45, dif)*sh;
  vec3 sunc = vec3(1.0, 0.78, 0.58)*1.8;
  vec3 skyc = mix(vec3(0.26, 0.31, 0.52), vec3(0.42, 0.50, 0.72), 0.5 + 0.5*n.y)*0.62;
  vec3 bounce = vec3(0.12, 0.46, 0.46)*clamp(-n.y + 0.25, 0.0, 1.0)*0.6;        // el mar ilumina el alero
  vec3 col = c*(sunc*dif + skyc*a + bounce*a);
  // brillo húmedo en bajamar
  if (wetSurf && p.y > L) {
    vec3 h = normalize(SUN - rd);
    col += vec3(1.0, 0.85, 0.7)*0.35*pow(max(dot(n, h), 0.0), 40.0)*sh;
  }
  col += vec3(0.25, 0.95, 0.82)*0.9*glowCave;
  // borde cálido
  col += vec3(1.0, 0.7, 0.5)*0.12*pow(1.0 - max(dot(n, -rd), 0.0), 3.0)*dif;
  return col;
}

// ---------------------------------------------------------------- agua
float waveH(vec2 q, float t){
  float h = 0.0;
  h += 0.30*sin(dot(q, vec2(0.08, 0.05)) + 1.0);
  h += 0.20*sin(dot(q, vec2(-0.05, 0.11)) + 2.0);
  h += 0.15*sin(dot(q, vec2(0.17, 0.13)));
  h += 0.25*(n2(q*0.25) - 0.5) + 0.12*(n2(q*0.9) - 0.5);
  return h;
}

vec3 water(vec3 p, vec3 rd, float t){
  float e = 0.15 + t*0.004;
  float amp = 0.8/(1.0 + t*0.02);
  float hx = (waveH(p.xz + vec2(e, 0), t) - waveH(p.xz - vec2(e, 0), t))/(2.0*e);
  float hz = (waveH(p.xz + vec2(0, e), t) - waveH(p.xz - vec2(0, e), t))/(2.0*e);
  vec3 n = normalize(vec3(-hx*amp, 1.0, -hz*amp));
  float depth = max(map(p).x, 0.0);                    // distancia al fondo/orilla más cercano
  vec3 deep = vec3(0.03, 0.15, 0.20), mid = vec3(0.12, 0.42, 0.44), shal = vec3(0.36, 0.72, 0.66);
  vec3 wc = mix(deep, mid, exp(-depth/16.0));
  wc = mix(wc, shal, exp(-depth/5.0));
  // lo que hay debajo se adivina: el lecho tiñe el agua
  float fres = 0.02 + 0.98*pow(1.0 - max(dot(n, -rd), 0.0), 5.0);
  vec3 rf = reflect(rd, n);
  vec3 refl = sky(rf);
  // reflejo de la roca
  if (rf.y > 0.0) {
    vec2 hr = march(p + vec3(0, 0.5, 0), rf, 900.0, 120);
    if (hr.x > 0.0) {
      vec3 q = p + rf*hr.x;
      refl = shade(q, normal(q, hr.x), rf, hr.y, hr.x, true);
      refl = mix(refl, fogc(rf), 1.0 - exp(-hr.x*0.0012));
    }
  }
  vec3 col = mix(wc*0.9, refl, clamp(fres, 0.0, 1.0));
  float spec = pow(max(dot(reflect(rd, n), SUN), 0.0), 220.0);
  col += vec3(1.0, 0.82, 0.6)*spec*1.6;
  col += vec3(1.0, 0.7, 0.5)*0.12*pow(max(dot(reflect(rd, n), SUN), 0.0), 12.0);
  // espuma: orillas y bajos
  float fo = exp(-depth/1.6);
  float pat = n2(p.xz*vec2(0.25, 0.6)) * 0.7 + 0.3*n2(p.xz*1.5);
  float foam = smoothstep(0.35, 0.7, fo*1.2 + pat*0.5 - 0.35);
  // líneas de rompiente paralelas al arrecife
  float lines = smoothstep(0.75, 0.95, sin(depth*1.6 - pat*3.0)*0.5 + 0.5)*exp(-depth/5.0);
  foam = max(foam, lines*0.8);
  col = mix(col, vec3(0.90, 0.93, 0.94), foam*0.85);
  return col;
}

// ---------------------------------------------------------------- render
void main(){
  if (DBG < -1.5) { vec2 q = gl_FragCoord.xy/R; vec3 ro = vec3(-450.0 + q.x*900.0, 200.0, q.y*900.0);
    float t = 0.0; vec2 m; for (int i = 0; i < 400; i++) { m = map(ro - vec3(0, t, 0)); if (m.x < 0.03) break; t += m.x*0.7; if (t > 260.0) break; }
    float v = clamp((200.0 - t + 60.0)/200.0, 0.0, 1.0); float hi = floor(v*255.0)/255.0;
    o = vec4(hi, fract(v*255.0), m.y/10.0, 1.0); return; }
  if (DBG < 0.0) { vec2 q = gl_FragCoord.xy/R; vec3 ro = vec3(-450.0 + q.x*900.0, 200.0, q.y*900.0);
    float t = 0.0; vec2 m; for (int i = 0; i < 300; i++) { m = map(ro - vec3(0, t, 0)); if (m.x < 0.05) break; t += m.x*0.8; if (t > 260.0) break; }
    float hgt = 200.0 - t; vec3 c = hgt > -24.0 ? (hgt > 0.0 ? mix(vec3(0.3,0.5,0.3), vec3(0.95), hgt/90.0) : vec3(0.75, 0.65, 0.45)) : vec3(0.1, 0.2, 0.4);
    if (abs(hgt + 18.0) < 0.6 || abs(hgt) < 0.8 || abs(hgt + 24.0) < 0.6) c *= 0.4;
    if (fract(q.x*9.0) < 0.01 || fract(q.y*9.0) < 0.01) c = vec3(1, 0, 0);
    vec2 wq = ro.xz; if (length(wq - CAM.xz) < 8.0) c = vec3(1, 1, 0);
    vec2 fd = normalize(TGT.xz - CAM.xz); vec2 rel = wq - CAM.xz; float ang = acos(clamp(dot(normalize(rel), fd), -1.0, 1.0));
    if (abs(ang - radians(FOV)*0.5*R.x/R.y*0.0 - atan(tan(radians(FOV)*0.5)*1.6)) < 0.004) c = vec3(1, 1, 0);
    o = vec4(c, 1); return; }
  if (DBG > 1.5) { vec2 q = gl_FragCoord.xy/R; vec3 p = vec3(-120.0 + q.x*380.0, -40.0 + q.y*237.5, DBG);
    vec2 m = map(p); o = vec4(m.x < 0.0 ? vec3(0.2 + m.y*0.08) : vec3(0.8, 0.85, 0.9) - 0.3*step(p.y, 0.0), 1.0);
    if (abs(p.y) < 0.4 || abs(p.y + 24.0) < 0.4) o.rgb = vec3(0, 0.5, 1); return; }
  vec2 uv = (gl_FragCoord.xy - 0.5*R)/R.y;
  vec3 fw = normalize(TGT - CAM);
  vec3 rt = normalize(cross(vec3(0, 1, 0), fw));
  vec3 up = cross(fw, rt);
  vec3 rd = normalize(fw*(0.5/tan(radians(FOV)*0.5)) + uv.x*rt + uv.y*up);
  vec3 ro = CAM;

  vec3 col;
  vec2 h = march(ro, rd, 4500.0, 640);
  float tw = rd.y < 0.0 ? (L - ro.y)/rd.y : 1e9;
  if (DBG > 0.5 && DBG < 1.5) { vec3 pp = ro + rd*h.x; o = vec4(h.y/10.0, clamp((pp.y + 40.0)/80.0, 0.0, 1.0), clamp(h.x/1000.0, 0.0, 1.0), 1.0); if (h.x < 0.0 || h.x > tw) o = vec4(1.0, 1.0, clamp(tw/1000.0, 0.0, 1.0), 1.0); return; }
  if (h.x > 0.0 && h.x < tw) {
    vec3 p = ro + rd*h.x;
    vec3 n = normal(p, h.x);
    col = shade(p, n, rd, h.y, h.x, false);
    col = mix(col, fogc(rd), 1.0 - exp(-h.x*0.00055));
  } else if (tw < 1e8) {
    vec3 p = ro + rd*tw;
    col = water(p, rd, tw);
    col = mix(col, fogc(rd), 1.0 - exp(-tw*0.00045));
  } else {
    col = sky(rd);
  }
  // grano y tono
  col = pow(col, vec3(0.95));
  col = mix(col, col*vec3(0.95, 0.97, 1.05), 0.5);
  col += (h21(gl_FragCoord.xy) - 0.5)*0.025;
  vec2 q = gl_FragCoord.xy/R;
  col *= 0.82 + 0.18*pow(16.0*q.x*q.y*(1.0 - q.x)*(1.0 - q.y), 0.2);
  o = vec4(clamp(col, 0.0, 1.0), 1.0);
}
