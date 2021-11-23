#!/bin/bash
set -ex
gcc -o encrypt encrypt.c -Iinc -Lbuild -lbearssl
