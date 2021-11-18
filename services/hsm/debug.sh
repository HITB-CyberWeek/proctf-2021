#!/bin/bash
lm32-rtems4.11-gdb /home/builder/development/rtems/kernel/lm32/lm32-rtems4.11/c/milkymist/testsuites/samples/hello/hello.exe -ex "target remote localhost:1234"
