import requests
url = 'http://localhost:5000/api'
r = requests.post(url,json={'exp':['5.9','5.1','3.5','1.8'],})
print(r.json())