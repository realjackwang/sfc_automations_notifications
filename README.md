# Vercel Notifications 项目说明

## 概述

这是一个用于自动收集任务执行状态并发送微信通知的 Vercel Serverless Function 项目。

## API 端点

* **POST `/api/collect`**: 用于接收任务执行信息。

* **GET `/api/send_notification`**: 手动触发发送微信通知。

## 定时任务 (`vercel.json`)

我们使用 Vercel 的 Cron Jobs 功能，每天定时自动触发通知 API。

```
{
"crons": [
{
"path": "/api/send_notification",
"schedule": "30 0 * * *"
}
]
}
```

* **`"schedule": "30 0 * * *"`**: 这个表达式表示任务会在 **UTC 时间 00:30** 自动运行。

**对应北京时间（UTC+8）为：每天早上 08:30。**