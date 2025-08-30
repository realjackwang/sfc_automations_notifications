import os
import json
import requests

# 从环境变量中获取 KV REST API 的连接信息
KV_REST_API_URL = os.environ.get('KV_REST_API_URL')
KV_REST_API_TOKEN = os.environ.get('KV_REST_API_TOKEN')

def handler(request):
    """
    处理 POST 请求，将任务执行信息存入 Vercel KV 数据库。
    """
    if request.method != 'POST':
        return {
            "statusCode": 405,
            "body": "Method Not Allowed"
        }

    try:
        data = json.loads(request.body)
        
        # 验证必需的参数
        required_params = ['source', 'task_name', 'status', 'message']
        if not all(p in data for p in required_params):
            return {
                "statusCode": 400,
                "body": "Missing required parameters"
            }
        
        # 构造要存入的数据
        timestamp = data.get('timestamp', str(os.time()))
        # 使用 REST API 的 SET 命令来存储数据
        # 键使用 `task:` 作为前缀，方便管理
        key = f"task:{timestamp}"
        
        # 构造 REST API 请求
        headers = {
            'Authorization': f'Bearer {KV_REST_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "command": ["SET", key, json.dumps(data)]
        }
        
        # 发送请求到 Upstash KV
        response = requests.post(KV_REST_API_URL, headers=headers, data=json.dumps(payload))
        
        # 检查响应状态码
        if response.status_code != 200:
            return {
                "statusCode": response.status_code,
                "body": f"Failed to store data: {response.text}"
            }

        return {
            "statusCode": 200,
            "body": "Data collected successfully"
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Internal Server Error: {str(e)}"
        }