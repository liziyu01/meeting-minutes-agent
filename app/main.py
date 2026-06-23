"""
FastAPI 主程序 - 会议纪要 Agent

项目 web 入口：
1. 接收用户上传的音频文件
2. 调用 stt.py 进行语音识别
3. 返回识别结果
"""

from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, UploadFile, File, HTTPException
from app.stt import speech_to_text
from fastapi.responses import FileResponse
from app.graph import run_workflow

# 创建 FastAPI 应用实例
app = FastAPI(
    title="会议纪要 Agent",
    description="上传会议录音，自动生成结构化会议纪要",
    version="1.0.0",
)

UPLOADS_DIR = Path("uploads")
OUTPUTS_DIR = Path("outputs")
UPLOADS_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

# 运行用户上传的音频格式
ALLOWED_AUDIO_TYPES = {".wav", ".mp3", ".m4a"}

# 定义路由
@app.get("/")
async def home():
    return {
        "service": "会议纪要 Agent",
        "status": "running...",
        "endpoints": {
            "上传音频": "POST /upload",
            "API 文档": "GET /docs",
        }
    }

# 上传音频并识别
@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    """
    上传音频文件，自动生成会议纪要。

    流程：验证格式 -> 保存音频 -> 语音转文字 -> LangGraph 工作流 -> 保存文件 -> 返回结果。
    """
    # 验证文件格式
    suffix = Path(file.filename).suffix.lower()

    if suffix not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式 '{suffix}。 请上传 {'/'.join(ALLOWER_AUDIO_TYPES)}。"
        )

    # 保存音频文件
    unique_id = str(uuid4())
    audio_filename = f"{unique_id}{suffix}"
    audio_path = UPLOADS_DIR/audio_filename

    try:
        content = await file.read()

        if len(content) > 25 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="文件大小不能超过 25MB"
            )
        audio_path.write_bytes(content)
        # 临时调试
        print(f"文件已保存到: {audio_path.resolve()}")  # 加这行，看路径对不对
        print(f"文件是否存在: {audio_path.exists()}")  # 加这行，看文件是否真的存在

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"文件保持失败: {e}"
        )

    # 语音转文字（STT）
    try:
        transcript = speech_to_text(str(audio_path))
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail=f"音频文件保存后无法找到。"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"语音识别失败: {e}",
        )

    # 调用 LangGraph 工作流
    try:
        result = run_workflow(transcript)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"会议纪要生成失败：{e}"
        )

    # 保存会议纪要 .md 文件
    md_filename = f"{unique_id}.md"
    md_path = OUTPUTS_DIR / md_filename
    try:
        md_path.write_text(result["final_output"], encoding="utf-8")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"会议纪要保存失败：{e}"
        )

    # 完整结果
    return {
        "success": True,
        "filename": audio_filename,
        "transcript": transcript,
        "minutes": result["final_output"],
        "summary": result.get("summary"),
        "action_items": result.get("action_items"),
        "decisions": result.get("decisions"),
        "download_url": f"/download/{md_filename}"
    }

# 下载接口
@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    下载指定文件。

    文件路径安全校验，防止路径遍历攻击
    """
    file_path = OUTPUTS_DIR / filename

    # 安全防护
    resolved_path = file_path.resolve()
    if not str(resolved_path).startswith(str(OUTPUTS_DIR.resolve())):
        raise HTTPException(
            status_code=403,
            detail="禁止访问"
        )

    if not resolved_path.exists():
        raise HTTPException(
            status_code=404,
            detail="文件不存在"
        )

    return FileResponse(
        path=str(resolved_path),
        media_type="text/markdown; charset=utf-8",
        filename=filename
    )

from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """统一捕获未处理的异常，返回标准的 JSON 错误"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "type": type(exc).__name__
        }
    )

from fastapi.responses import HTMLResponse
@app.get("/test", response_class=HTMLResponse)
async def test_page():
    return """
    <html>
        <body>
            <h2>上传会议录音</h2>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <input type="file" name="file">
                <button type="submit">上传</button>
            </form>
        </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )