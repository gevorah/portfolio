#!/bin/sh
# compila y renderiza: ./build.sh mar orbit 640 400 a1
set -e
g++ -O3 -march=native -ffast-math -std=c++17 -pthread src/$1.cpp -o out/$1
./out/$1 $2 $3 $4 out/$5.swhdr
