from Crypto.PublicKey import RSA

key = RSA.generate(bits=1024)
print("Generated:")
print("n =", key.n)
print("e =", key.e)
print("d =", key.d)
print("p =", key.p)
print("q =", key.q)
print("u =", key.u)
