import os
import oss2
from config import OSS_CONFIG, OSS_BASE_URL


def upload_to_oss(file_path: str, object_name: str = None) -> str:
    """
    将文件上传到阿里云 OSS，返回访问 URL。

    Args:
        file_path: 本地文件路径
        object_name: OSS 中的对象名称，默认使用文件名

    Returns:
        OSS 文件访问 URL
    """
    if object_name is None:
        object_name = os.path.basename(file_path)

    auth = oss2.Auth(OSS_CONFIG["access_key_id"], OSS_CONFIG["access_key_secret"])
    bucket = oss2.Bucket(auth, OSS_CONFIG["endpoint"], OSS_CONFIG["bucket_name"])

    bucket.put_object_from_file(object_name, file_path)

    # 如果配置了公共访问基址，直接拼接
    if OSS_BASE_URL:
        return f"{OSS_BASE_URL.rstrip('/')}/{object_name}"

    # 否则生成 7 天有效的临时签名 URL
    return bucket.sign_url("GET", object_name, 7 * 24 * 3600)
