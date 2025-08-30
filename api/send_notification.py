import os
import json
import requests
import time
import redis
from http.server import BaseHTTPRequestHandler

# WxPusher 配置
WXPUSHER_API_URL = "https://wxpusher.zjiecode.com/api/send/message"
# 确保在你的 Vercel 项目环境变量中设置 WXPUSHER_APP_TOKEN 和 WXPUSHER_UIDS
WXPUSHER_APP_TOKEN = os.environ.get('WXPUSHER_APP_TOKEN')
WXPUSHER_UIDS = os.environ.get('WXPUSHER_UIDS') # 格式为 "UID_xxx,UID_yyy"

# 从环境变量中获取 KV REST API 的连接信息
KV_REST_API_URL = os.environ.get('KV_REST_API_URL')
KV_REST_API_TOKEN = os.environ.get('KV_REST_API_TOKEN')

# 使用 URL 和 Token 创建一个 Redis 客户端实例
# 注意: Vercel 的环境变量 UPSTASH_REDIS_REST_URL 和 UPSTASH_REDIS_REST_TOKEN 
# 已经包含了认证信息，所以直接传入即可
r = redis.Redis.from_url(
    url=KV_REST_API_URL,
    password=KV_REST_API_TOKEN
)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 1. 从 Upstash KV 读取所有任务数据
            # 使用 Redis 的 keys 命令获取所有键，比 REST API 更可靠
            task_keys = r.keys("task:*")

            # 2. 批量读取所有任务数据并分类
            success_tasks = []
            failure_tasks = []
            
            if task_keys:
                get_results = r.mget(task_keys)
                
                # 过滤并解析有效数据
                for res in get_results:
                    if res:
                        task = json.loads(res)
                        if task.get('status') == 'success':
                            success_tasks.append(task)
                        else:
                            failure_tasks.append(task)

            # 3. 整合为 HTML 格式
            summary = "任务状态报告"
            content = "<h1>任务执行状态报告</h1>"
            
            # 失败任务部分
            if failure_tasks:
                content += "<h2 style='color:red;'>失败的任务</h2>"
                for task in failure_tasks:
                    task_name = task.get('task_name', '未知任务')
                    source = task.get('source', '未知来源')
                    message = task.get('message', '无详细信息')
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task.get('timestamp', 0)))
                    
                    content += f"<hr/><p><strong>任务名:</strong> {task_name}</p>"
                    content += f"<p><strong>来源:</strong> {source}</p>"
                    content += f"<p><strong>时间:</strong> {timestamp}</p>"
                    content += f"<p><strong>详细信息:</strong> <br/>{message}</p>"

            # 成功任务部分
            if success_tasks:
                content += "<h2 style='color:green;'>成功的任务</h2>"
                content += "<ul>"
                for task in success_tasks:
                    task_name = task.get('task_name', '未知任务')
                    source = task.get('source', '未知来源')
                    content += f"<li>{task_name} ({source})</li>"
                content += "</ul>"

            # 最终总结
            content += f"<hr/><p><strong>总计:</strong> {len(success_tasks) + len(failure_tasks)} 个任务已执行</p>"
            content += f"<p style='color:green;'><strong>成功:</strong> {len(success_tasks)} 个</p>"
            content += f"<p style='color:red;'><strong>失败:</strong> {len(failure_tasks)} 个</p>"
            
            # 4. 调用 WxPusher API 发送通知
            wxpusher_uids = [uid.strip() for uid in WXPUSHER_UIDS.split(',')]
            
            wxpusher_payload = {
                "appToken": WXPUSHER_APP_TOKEN,
                "content": content,
                "summary": summary,
                "contentType": 2, # HTML 格式
                "uids": wxpusher_uids
            }
            
            wxpusher_response = requests.post(WXPUSHER_API_URL, json=wxpusher_payload)
            wxpusher_response.raise_for_status()

            # 5. 成功发送后，删除所有已处理的键
            if task_keys:
                r.delete(*task_keys) # 使用 Redis 客户端的 delete 命令
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"message": "Notification sent successfully"}).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Internal Server Error: {str(e)}"}).encode('utf-8'))
