# forvolution
This service is am image storage what allows to apply a user-defined [convolutions](https://en.wikipedia.org/wiki/Kernel_(image_processing)) to stored images. The service is written in fortran with bindings to c code. Its uses filesystem as database to save images with meta.

## API

The service listens TCP port 12345 for commands. Every command contains its name and sizes of various-size parameters. The name and each sizes are ended with semicolon. Each size are limited by 2 symbols. After sizes the service waits its parameters without any delimiters in raw format. For each command the service returns status message and result in the same form.

The service have 3 commands: UPLOAD, DOWNLOAD and CONVOLUTION

### UPLOAD

It allows to upload image with description and access key to service and returns an ID of the uploaded image. The ID consists 32 hexadecimal digits.

#### Example request
`UPLOAD;2;3;4;6;abcdefdescsecret` will upload image

|     |     |     |
|-----|-----|-----|
|  97 |  99 | 101 |
|  98 | 100 | 102 |

with description `desc` and access key `secret` to service.

---

**NOTE #1**

In fortran [array elements are stored in column-major order](https://docs.oracle.com/cd/E19957-01/805-4939/6j4m0vn6r/index.html).

---

#### Example response
`ok;0123456789abcdef0123456789abcdef`. Image is uploaded successfully and received ID `0123456789abcdef0123456789abcdef`

### DOWNLOAD

It allows to download image by ID and access key. 

#### Example request
`DOWNLOAD;5;0123456789abcdef0123456789abcdefsecret` will try to download image with ID `0123456789abcdef0123456789abcdef` using access key `secret`

#### Example response
`ok;2;3;abcdef`. Image download successfully. It has 2 rows and 3 columns

### CONVOLUTION

It applies chosen convolution to chosen image. It requires ID of image and kernel of convolutions. Kernel must be square. Result will be returned by 4 bits per element little-endian.

#### Example request
`CONVOLUTION;2;2;0123456789abcdef0123456789abcdef\1\1\0\0` will apply convolution with kernel

|   |   |
|---|---|
| 1 | 0 |
| 1 | 0 |

to image with ID `0123456789abcdef0123456789abcdef`

#### Example response
`ok;1;2;\0\0\0\195\0\0\0\199\0\0\0\203`
It corresponds to convolution

|   |   |   |
|---|---|---|
|195|199|203|

## Vulnerability:
Weak check of convolution sizes equality what allows to read data outsize the image. 

## Vulnerability details and way to hack:

### Hack step I: Request `CONVOLUTION;2;2 ;...` bypasses equality checking of sides

Explanation: 
[Code what try to check if kernel is square](https://github.com/HITB-CyberWeek/proctf-2021/blob/main/services/forvolution/src/src/connection_handler.f90#L460-L465), looks like:

```fortran
    ns = to_string(self%buffer(1:npos-1), npos-1)
    ms = to_string(self%buffer(npos+1:mpos-1), mpos-npos-1)
    if (ns.ne.ms) then
      call self%set_error('kernel is not square')
      return
    end if
```

where function [to_string](https://github.com/HITB-CyberWeek/proctf-2021/blob/main/services/forvolution/src/src/string_utils.f90#L48-L65) just converts array of character to string of equal length and [`ns` and `ms` declared](https://github.com/HITB-CyberWeek/proctf-2021/blob/main/services/forvolution/src/src/connection_handler.f90#L443-L444) as

```fortran
    character(len=2) :: ns
    character(len=2) :: ms
```

what means "string with length two exactly".

---

**NOTE 2**

In fortran if value of string is less that declared length then string is [padding with spaces](https://fortranwiki.org/fortran/files/character_handling_in_Fortran.html)

---

`to_sting(self%buffer(1:npos-1), npos-1)` returns `'2'`, but when this value assigned to variable `ns` it is padded and goes to `'2 '`. Value `ns` is equal to `ms` after it.

Funtion [parse_int](https://github.com/HITB-CyberWeek/proctf-2021/blob/main/services/forvolution/src/src/string_utils.f90#L116-L126) does not check input and returns 2 to `'2'` and 4 for `'2 '`

### Hack step II: read outsize the image in function convolution
Function [convolution](https://github.com/HITB-CyberWeek/proctf-2021/blob/main/services/forvolution/src/src/matrix.f90#L9-L31) has problem with size of result. It [uses count of rows for kernel](https://github.com/HITB-CyberWeek/proctf-2021/blob/main/services/forvolution/src/src/matrix.f90#L23) to calculate count of columns for result. It is not problem if kernel is square, but after step I it is false.

After [loading image](https://github.com/HITB-CyberWeek/proctf-2021/blob/main/services/forvolution/src/src/database.f90#L83-L156) description is laid right after content. It means that function `convolution` will read description when try to get items outsize the matrix.

Example:

For image

|   |   |   |   |
|---|---|---|---|
| 1 | 3 | 5 | 7 |
| 2 | 4 | 6 | 8 |

memory looks like

|   |   |        |         |         |         |         |         |         |         |        |      |      |      |      |
|---|---|--------|---------|---------|---------|---------|---------|---------|---------|--------|------|------|------|------|
| 2 | 3 |     1  |       2 |       3 |       4 |       5 |       6 |       7 |       8 |      4 |  100 |  101 |  115 |   99 |
| n | m | a(1,1) | a(2, 1) | a(1, 2) | a(2, 2) | a(1, 3) | a(2, 3) | a(1, 4) | a(2, 4) | len(d) | d(1) | d(2) | d(3) | d(4) |

After using kernel

|   |   |   |   |
|---|---|---|---|
| 1 | 0 | 0 | 0 |
| 0 | 0 | 0 | 1 |

convolution will be equal to

|                   |                   |                   |
|-------------------|-------------------|-------------------|
| a(1, 1) + a(2, 4) | a(1, 2) + a(2, 5) | a(1, 3) + a(2, 6) |

what means

|                   |                 |                |
|-------------------|-----------------|----------------|
| a(1, 1) + a(2, 4) | a(1, 2) +  d(1) | a(1, 3) + d(3) |

### Hack step III: reconstruct description

Each item of convolution is linear combination of items original matrix. For take original image by convolution result and kernel It simple needs solve [system of linear equations](https://en.wikipedia.org/wiki/System_of_linear_equations). As example there is Gauss's methods to solve it. But one convolution result is not enough to it. Author's sploit use three different kernels for reconstructing one image and memory after it.

## Patching

For fix vulnerability it needs to replace compairing of `ns` and `ms` to compairing `n` and `m`
