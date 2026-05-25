import os
import re
import sys
import uuid
from flask import Flask, render_template, request, jsonify, send_file
from parser import parse_douyin_link, download_video
from config import is_oss_configured
from uploader import upload_to_oss

# PyInstaller 打包后，资源文件在临时目录 _MEIPASS 中
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# downloads 目录放在 exe 同级（不是临时目录），方便用户直接找到下载的文件
EXE_DIR = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else BASE_DIR
DOWNLOAD_DIR = os.path.join(EXE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 最大 200MB


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/parse", methods=["POST"])
def api_parse():
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"success": False, "error": "请提供抖音分享链接"}), 400

    raw_text = data["url"].strip()

    # 从粘贴的分享文案中自动提取链接
    url_match = re.search(r"https?://(?:v\.douyin\.com/|www\.douyin\.com/video/|www\.iesdouyin\.com/share/video/)[^\s]+", raw_text)
    if not url_match:
        return jsonify({"success": False, "error": "未找到抖音分享链接，请重新复制抖音分享文案"}), 400

    share_url = url_match.group(0)

    if not re.search(r"v\.douyin\.com|douyin\.com/video", share_url):
        return jsonify({"success": False, "error": "链接格式不正确，请提供抖音视频分享链接"}), 400

    try:
        # Step 1: 解析链接
        video_info = parse_douyin_link(share_url)
    except Exception as e:
        return jsonify({"success": False, "error": f"解析链接失败: {str(e)}"}), 500

    # Step 2: 下载视频
    filename = f"{uuid.uuid4().hex}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    try:
        download_video(video_info["video_url"], filepath)
    except Exception as e:
        return jsonify({"success": False, "error": f"下载视频失败: {str(e)}"}), 500

    # Step 3: 上传到 OSS
    try:
        if is_oss_configured():
            oss_object = f"douyin/{video_info['video_id']}.mp4"
            oss_url = upload_to_oss(filepath, oss_object)
        else:
            oss_url = None
    except Exception as e:
        oss_url = None
        oss_error = str(e)
        return jsonify({"success": False, "error": f"上传 OSS 失败: {oss_error}"}), 500

    download_url = f"/download/{filename}"
    preview_url = oss_url if oss_url else f"/video/{filename}"

    return jsonify(
        {
            "success": True,
            "data": {
                "video_id": video_info["video_id"],
                "title": video_info.get("title", ""),
                "oss_url": oss_url,
                "cover_url": video_info.get("cover_url", ""),
                "download_url": download_url,
                "preview_url": preview_url,
            },
        }
    )


@app.route("/download/<filename>")
def download_file(filename):
    """直接下载视频文件"""
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    return send_file(
        filepath,
        mimetype="video/mp4",
        as_attachment=True,
        download_name=f"douyin_{filename}",
    )


@app.route("/video/<filename>")
def serve_video(filename):
    """在线预览视频"""
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    return send_file(filepath, mimetype="video/mp4")


if __name__ == "__main__":
    print("=" * 50)
    print(" 抖音视频 → OSS 转存工具")
    print(f" 打开浏览器访问: http://127.0.0.1:5000")
    print("=" * 50)
    # 打包后自动打开浏览器，关闭 debug 避免性能问题
    import webbrowser
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=False, host="127.0.0.1", port=5000)
