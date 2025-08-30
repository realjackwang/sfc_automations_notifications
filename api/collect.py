import os
import json
import redis

# 从环境变量中获取 Upstash Redis 的连接信息
REDIS_URL = os.environ.get('UPSTASH_REDIS_REST_URL')
REDIS_TOKEN = os.environ.get('UPSTASH_REDIS_REST_TOKEN')

# 使用 URL 和 Token 创建一个 Redis 客户端实例
# 注意: Vercel 的环境变量 UPSTASH_REDIS_REST_URL 和 UPSTASH_REDIS_REST_TOKEN 
# 已经包含了认证信息，所以直接传入即可
r = redis.Redis.from_url(
    url=REDIS_URL,
    password=REDIS_TOKEN
)

def handler(request):
    """
    处理 POST 请求，将任务执行信息存入 Redis。
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
        
        # 使用时间戳作为键，存储任务信息
        key = f"task:{data['timestamp'] or os.time()}"
        
        # 存储到 Redis，如果 timestamp 已存在则覆盖
        r.set(key, json.dumps(data))

        return {
            "statusCode": 200,
            "body": "Data collected successfully"
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Internal Server Error: {str(e)}"
        }