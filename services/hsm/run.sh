#!/bin/bash
export QEMU_AUDIO_DRV=none
qemu-system-lm32 -M milkymist -kernel /home/builder/development/rtems/kernel/lm32/lm32-rtems4.11/c/milkymist/testsuites/samples/hello/hello.exe -nographic -monitor unix:qemu-monitor-socket,server,nowait "$@" #-gdb tcp::1234
