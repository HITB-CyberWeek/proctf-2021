import base64
with open("collision2.bin.request", "rb") as f:
	data = f.read()
print(base64.urlsafe_b64encode(data))
