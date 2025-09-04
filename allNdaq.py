#get list of all stocks on nasdaq - also returns companies that may not exist
import requests, json
from bs4 import BeautifulSoup

cs = {}

for i in range(65,91): #ASCII A-Z
  print(chr(i),end=" - ",flush=True)
  r = requests.get(f"http://www.advfn.com/nasdaq/nasdaq.asp?companies={chr(i)}",headers={"User-Agent":'test/1.0'},timeout=500).text

  table = r.split("Info</th>")[1].split("</table")[0]
  s = BeautifulSoup(table, features="html.parser")


  for r in s.find_all('tr'):
    o = []
    for d in r.find_all('td'):
      o.append(d.get_text())
    cs[o[1]] = o[0]
  

  print(f"total: {len(cs)}")

print(len(cs))

with open('allSymbs.json','w') as f:
  f.write(json.dumps(cs,indent=2))