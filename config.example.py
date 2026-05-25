# 配置模板 — 复制为 config.py 并填入你的阿里云 OSS 信息

import os

OSS_CONFIG = {
    "access_key_id": os.environ.get("OSS_ACCESS_KEY_ID", ""),
    "access_key_secret": os.environ.get("OSS_ACCESS_KEY_SECRET", ""),
    "endpoint": os.environ.get("OSS_ENDPOINT", "oss-cn-shanghai.aliyuncs.com"),
    "bucket_name": os.environ.get("OSS_BUCKET_NAME", "douyi-media"),
}

OSS_BASE_URL = os.environ.get("OSS_BASE_URL", "")


def is_oss_configured():
    return all(OSS_CONFIG.values())
