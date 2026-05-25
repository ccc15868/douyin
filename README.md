# 抖音视频 → OSS 转存工具

粘贴抖音分享链接，自动下载无水印视频并上传至阿里云 OSS。

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/ccc15868/douyin.git
cd douyin

# 2. 安装依赖（需要 Python 3.10+）
pip install -r requirements.txt

# 3. 创建 .env 文件，填入 OSS 凭证
```

在项目目录下创建 `.env` 文件，填入你的阿里云 OSS 信息：

```env
OSS_ACCESS_KEY_ID=你的AccessKey ID
OSS_ACCESS_KEY_SECRET=你的AccessKey Secret
OSS_ENDPOINT=oss-cn-shanghai.aliyuncs.com
OSS_BUCKET_NAME=你的Bucket名称
```

```bash
# 4. 启动
python app.py
```

浏览器打开 `http://127.0.0.1:5000`，粘贴抖音分享链接即可。

## 功能

- 支持抖音分享短链接和文案自动提取
- 无水印视频下载
- 自动上传至阿里云 OSS
- 视频在线预览
- 一键下载视频文件

## 依赖

| 依赖 | 用途 |
|------|------|
| Flask | Web 框架 |
| requests | HTTP 请求（解析链接、下载视频） |
| oss2 | 阿里云 OSS 上传 |
| python-dotenv | .env 环境变量加载 |
