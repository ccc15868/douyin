import re
import json
import requests


MOBILE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/16.6 Mobile/15E148 Safari/604.1"
    ),
}


def parse_douyin_link(share_url: str) -> dict:
    """
    解析抖音分享链接，提取视频信息。

    返回:
        {
            "video_id": "7638116268914068799",
            "video_url": "https://...",
            "cover_url": "https://...",
            "title": "视频标题",
        }
    """
    share_url = share_url.strip()

    # Step 1: 跟随分享链接重定向，获取页面内容
    resp = requests.get(
        share_url,
        headers=MOBILE_HEADERS,
        allow_redirects=True,
        timeout=15,
    )

    # Step 2: 从 URL 或页面中提取视频 ID
    video_id = _extract_video_id(resp)
    if not video_id:
        raise ValueError(f"无法从链接中提取视频 ID，跳转地址: {resp.url}")

    # Step 3: 从页面提取嵌入的 JSON 数据
    page_data = _extract_page_data(resp.text)
    if not page_data:
        raise ValueError("未找到视频数据，抖音页面结构可能已更新")

    # Step 4: 从 item_list 中提取视频信息
    item = _get_first_item(page_data)
    if not item:
        raise ValueError("未能从页面数据中提取视频信息")

    video = item.get("video", {})
    play_addr = video.get("play_addr", {})
    cover = video.get("cover", {})

    # 提取播放地址
    url_list = play_addr.get("url_list", [])
    if not url_list:
        raise ValueError("未能提取到视频播放地址")

    video_url = url_list[0]

    # 无水印处理
    video_url = video_url.replace("playwm", "play")

    # 提取封面
    cover_url = ""
    cover_list = cover.get("url_list", [])
    if cover_list:
        cover_url = cover_list[0]

    # 提取标题
    title = item.get("desc", f"douyin_{video_id}")

    return {
        "video_id": video_id,
        "video_url": video_url,
        "cover_url": cover_url,
        "title": title,
    }


def _extract_video_id(resp) -> str | None:
    """从响应中提取视频 ID"""
    # 优先从最终 URL 提取
    match = re.search(r"/video/(\d+)", resp.url)
    if match:
        return match.group(1)

    # 从重定向历史中提取
    for hist in resp.history:
        location = hist.headers.get("Location", "")
        match = re.search(r"/video/(\d+)", location)
        if match:
            return match.group(1)

    # 从页面内容尝试提取
    match = re.search(r'"aweme_id"\s*:\s*"(\d+)"', resp.text)
    if match:
        return match.group(1)

    return None


def _extract_page_data(html: str) -> dict | None:
    """从 HTML 页面中提取视频数据 JSON"""
    # 方式 1: window._ROUTER_DATA（当前主要方式）
    match = re.search(
        r"window\._ROUTER_DATA\s*=\s*(.*?)</script>", html, re.DOTALL
    )
    if match:
        return json.loads(match.group(1))

    # 方式 2: RENDER_DATA（旧版页面结构，保留兼容）
    match = re.search(
        r'<script id="RENDER_DATA" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    if match:
        from urllib.parse import unquote
        return json.loads(unquote(match.group(1)))

    return None


def _get_first_item(page_data: dict) -> dict | None:
    """从页面数据中提取第一个视频 item"""
    # 路径: loaderData → video_(id)/page → videoInfoRes → item_list[0]
    loader = page_data.get("loaderData", {})
    if not loader:
        # RENDER_DATA 兼容路径：递归查找 item_list
        return _find_in_data(page_data, ["item_list"])

    # 遍历 loaderData，找到包含 videoInfoRes 的条目
    for key, value in loader.items():
        if isinstance(value, dict) and "videoInfoRes" in value:
            video_info = value["videoInfoRes"]
            item_list = video_info.get("item_list", [])
            if item_list:
                return item_list[0]

    # 备选：递归查找 item_list
    return _find_in_data(page_data, ["item_list"])


def _find_in_data(data, target_keys: list, depth: int = 0):
    """递归在 JSON 数据中查找指定 key 的值（用于降级兼容）"""
    if depth > 25 or data is None:
        return None

    if isinstance(data, dict):
        for key in target_keys:
            if key in data:
                val = data[key]
                if isinstance(val, list) and val:
                    return val[0]
                if isinstance(val, dict):
                    for url_key in ["url_list", "url_list_v2", "url_list_v3"]:
                        if url_key in val and val[url_key]:
                            return val[url_key][0]
                    if "url" in val:
                        return val["url"]
                if isinstance(val, str):
                    return val
        for v in data.values():
            result = _find_in_data(v, target_keys, depth + 1)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = _find_in_data(item, target_keys, depth + 1)
            if result:
                return result

    return None


def download_video(video_url: str, save_path: str) -> str:
    """下载视频到本地，返回文件路径"""
    headers = {**MOBILE_HEADERS, "Referer": "https://www.douyin.com/"}
    resp = requests.get(video_url, headers=headers, stream=True, timeout=60)
    resp.raise_for_status()

    with open(save_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    return save_path
