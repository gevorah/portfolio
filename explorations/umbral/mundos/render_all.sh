#!/bin/sh
# Renderiza todas las láminas finales. Uso: ./render_all.sh [ancho] [alto]
set -e
W=${1:-2000}; H=${2:-1250}
mkdir -p out renders
g++ -O3 -march=native -ffast-math -std=c++17 -pthread src/mar.cpp -o out/mar
g++ -O3 -march=native -ffast-math -std=c++17 -pthread src/rev.cpp -o out/rev
for s in orbit approach transform discover; do
  ./out/mar $s $W $H out/a-$s.swhdr > out/a-$s.anchors
  ./out/rev $s $W $H out/b-$s.swhdr > out/b-$s.anchors
done
./out/mar chart 1200 1200 out/a-chart.swhdr > out/a-chart.anchors
./out/rev chart 1200 1200 out/b-chart.swhdr > out/b-chart.anchors
./out/mar silhouette 1200 1200 out/a-sil.swhdr > /dev/null
SD=6.4 FV=28 ./out/rev silhouette 1200 1200 out/b-sil.swhdr > /dev/null
