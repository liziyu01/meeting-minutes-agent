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

# 创建 FastAPI 应用实例
app = FastAPI(
    title="会议纪要 Agent",
    description="上传会议录音，自动生成机构化会议纪要",
    version="1.0.0",
)

UPLOADS_DIR = Path("uploads")
OUTPUTS_DIR = Path("outputs")
UPLOADS_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

# 运行用户上传的音频格式
ALLOWER_AUDIO_TYPES = {".wav", ".mp3", ".m4a"}

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
    suffix = Path(file.filename).suffix.lower()

    if suffix not in ALLOWER_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式 '{suffix}。 请上传 {'/'.join(ALLOWER_AUDIO_TYPES)}。"
        )
    unique_name = f"{uuid4()}{suffix}"
    save_path = UPLOADS_DIR/unique_name

    try:
        content = await file.read()
        save_path.write_bytes(content)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"文件保持失败: {e}"
        )

    try:
        transcript = speech_to_text(str(save_path))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"语音识别失败: {e}",
        )

    return {
        "success": True,
        "filename": unique_name,
        "transcript": transcript,
        "text_length": len(transcript)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )