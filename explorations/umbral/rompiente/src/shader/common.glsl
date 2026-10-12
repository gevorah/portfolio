// Umbral · código compartido por La Rompiente y La Cala Interior:
// ruido, utilidades y la columna estratigráfica (los mismos bancos en todo el lugar).

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

float smin(float a, float b, float k){ float h = clamp(0.5 + 0.5*(b - a)/k, 0.0, 1.0); return mix(b, a, h) - k*h*(1.0 - h); }

// ---------------------------------------------------------------- estratos
// Columna estratigráfica por paquetes, de −46 m hacia arriba: finos y blandos abajo
// (donde trabaja la marea), un banco duro cuyo techo es la rasa (−18), alternancias,
// cornisas duras, una cintura blanda que deja una sombra horizontal, más cornisas,
// un banco masivo y el remate que forma el techo del alero.
const int NB = 61;
const float BT[61] = float[](1.00, 1.06, 1.38, 0.60, 0.60, 1.56, 1.41, 0.54, 1.36, 1.15, 1.20, 1.23, 0.95, 0.85, 0.53, 0.57, 1.20, 10.80, 0.95, 1.27, 1.63, 0.96, 1.54, 0.83, 1.10, 0.93, 2.30, 1.92, 2.22, 1.73, 0.63, 0.89, 5.43, 0.89, 4.49, 0.77, 4.23, 1.26, 4.05, 0.65, 1.15, 0.63, 1.05, 0.98, 0.59, 0.69, 0.84, 0.73, 0.60, 0.72, 1.10, 0.86, 0.73, 0.57, 6.44, 1.17, 3.61, 1.33, 1.45, 14.00, 78.00);
const float BB[62] = float[](0.00, 1.00, 2.06, 3.44, 4.04, 4.64, 6.20, 7.61, 8.15, 9.51, 10.66, 11.86, 13.09, 14.04, 14.89, 15.42, 15.99, 17.19, 27.99, 28.94, 30.21, 31.84, 32.80, 34.34, 35.17, 36.27, 37.20, 39.50, 41.42, 43.64, 45.37, 46.00, 46.89, 52.32, 53.21, 57.70, 58.47, 62.70, 63.96, 68.01, 68.66, 69.81, 70.44, 71.49, 72.47, 73.06, 73.75, 74.59, 75.32, 75.92, 76.64, 77.74, 78.60, 79.33, 79.90, 86.34, 87.51, 91.12, 92.45, 93.90, 107.90, 185.90);
const float BH[61] = float[](0.55, 0.15, 0.55, 0.25, 0.10, 0.15, 0.10, 0.15, 0.25, 0.15, 0.55, 0.55, 0.10, 0.15, 0.10, 0.25, 0.15, 0.95, 0.15, 0.15, 0.75, 0.30, 0.65, 0.75, 0.15, 0.75, 0.30, 0.30, 0.15, 0.30, 0.65, 0.13, 0.77, 0.10, 0.81, 0.09, 0.87, 0.08, 0.86, 0.06, 0.07, 0.14, 0.10, 0.10, 0.12, 0.15, 0.18, 0.06, 0.11, 0.19, 0.04, 0.04, 0.12, 0.05, 0.88, 0.24, 0.75, 0.24, 0.76, 1.00, 0.80);
const float BC[61] = float[](3.00, 1.00, 1.00, 1.00, 3.00, 0.00, 0.00, 0.00, 3.00, 1.00, 0.00, 1.00, 1.00, 1.00, 3.00, 3.00, 0.00, 0.00, 0.00, 3.00, 3.00, 2.00, 2.00, 0.00, 0.00, 1.00, 3.00, 3.00, 3.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 2.00, 0.00, 2.00, 0.00, 0.00, 0.00, 2.00, 1.00, 3.00, 3.00, 2.00, 1.00, 1.00, 0.00, 2.00, 0.00, 0.00, 2.00, 1.00, 0.00, 2.00, 1.00, 0.00, 0.00, 1.00);
// cota estratigráfica: los estratos buzan suave y ondulan en pliegues amplios
float bedY(vec3 p){ return p.y + 0.014*(p.z - 400.0) - 0.012*p.x + 2.5*(n2(p.xz*0.009) - 0.5)*2.0; }
// devuelve (índice, fracción dentro del banco, espesor, dureza efectiva)
vec4 bed(vec3 p){
  float y = clamp(bedY(p) + 46.0, 0.0, BB[NB] - 0.01);
  int lo = 0, hi = NB - 1;                                   // búsqueda binaria en las bases acumuladas
  for (int k = 0; k < 7; k++) {
    int mid = (lo + hi + 1)/2;
    if (BB[mid] <= y) lo = mid; else hi = mid - 1;
  }
  int i = lo;
  float t = BT[i];
  float hard = BH[i] + 0.45*(n2(vec2(p.z*0.012 + float(i)*3.1, p.x*0.012)) - 0.5)*2.0;   // los bancos se acuñan
  return vec4(float(i), clamp((y - BB[i])/t, 0.0, 1.0), t, clamp(hard, 0.0, 1.0));
}
// perfil de un banco en la pared. Los bancos finos apenas se marcan: el relieve lo
// hacen los paquetes (la cintura blanda se vacía, las cornisas duras asoman).
float packageRecess(vec3 p){
  float y = bedY(p);
  return 3.2*smoothstep(20.0, 24.0, y)*(1.0 - smoothstep(32.0, 35.0, y))     // cintura
       + 1.6*(1.0 - smoothstep(-32.0, -29.0, y))                              // paquete fino de la base
       + 0.6*smoothstep(-18.0, -16.0, y)*(1.0 - smoothstep(-1.0, 1.0, y));    // alternancia
}
float bedRelief(vec4 b){
  float f = b.y, hard = b.w;
  float amp = smoothstep(0.8, 3.5, b.z);
  float soft = (1.2 + 1.2/max(b.z, 0.7))*pow(sin(3.14159*f), 0.6);
  float nose = -1.1*pow(sin(3.14159*f), 0.35);
  return mix(0.04, 1.0, amp)*mix(soft, nose, smoothstep(0.35, 0.65, hard));
}
float strataQ(vec3 p){ return bed(p).x + bed(p).y; }
float softLayer(vec3 p){ vec4 b = bed(p); return (1.0 - smoothstep(0.35, 0.65, b.w))*pow(sin(3.14159*b.y), 0.6); }
