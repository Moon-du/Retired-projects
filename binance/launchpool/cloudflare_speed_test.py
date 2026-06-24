import csv
import os

import requests
from jsonpath import jsonpath

# 执行CloudflareST shell脚本
os.chdir("/etc/cf")
os.system("./CloudflareST -n 1000 -dd")

# 读取IP列表获取最优 ip
with open("result.csv", 'r') as file:
    csv_reader = csv.reader(file)  # 创建reader对象
    best_ip = list(csv_reader)[1][0]  # 获取最优 ip


# 调用 cloudflare api 修改 DNS解析记录
zone_id ="30dbbcc9cd44871652d4a92d3100f522"
dns_record_id = "8cea9adf4c22f0eaf2f95e230293b6c3"
url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{dns_record_id}"
headers = {
    'Content-Type': 'application/json',
'X-Auth-Email': '243062737@qq.com',
'X-Auth-Key': '5935eaa68d41dc2d8307438d3bdcbb86c40f3',
}
params = {
  "content": best_ip,
  "name": "cdn.yunm.org",
  "proxied": False,
  "type": "A",
  "ttl": 1
}
update_dns_info = requests.put(url=url, headers=headers, json=params).json()
update_dns_result = jsonpath(update_dns_info, "$.success")[0]
if update_dns_result:
    print("更新 DNS 解析记录成功！")
else:
    print("更新 DNS 解析记录失败！")


