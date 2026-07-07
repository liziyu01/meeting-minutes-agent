"""
语音转文字模块 (STT)

功能：
    将音频文件（支持 mp3/m4a/wav 等格式）转换为中文文字。

特点：
    - 自动转换为单声道（满足 API 声道要求）
    - 按静音自动分段，支持长音频
    - 识别完成后自动清理临时文件
"""

import os
from pydub import AudioSegment
from pydub.silence import split_on_silence
from zhipuai import ZhipuAI
from dotenv import load_dotenv
from app.utils import STTError

load_dotenv()

ZHIPUAI_API_KEY = os.getenv("zhipuai_api_key")

if not ZHIPUAI_API_KEY:
    raise ValueError(
        "未找到 ZHIPUAI_API_KEY! \n"
        "请检查项目根目录里的 .env 文件是否正确配置。 \n"
        "格式：ZHIPUAI_API_KEY=your key"
    )

client = ZhipuAI(api_key=ZHIPUAI_API_KEY)

# ===== 对外暴露的接口 =====
__all__ = ["speech_to_text"]


def speech_to_text(audio_path: str, max_chunk_len: int = 28000) -> str:
    """
    将音频文件转换为中文数字

    Args:
        audio_path: 音频文件路径（支持 wav/mp3/m4a 等）
        max_chunk_len: 每段音频的最大长度（单位: 毫秒）,默认 28 秒

    Returns:
        识别出的文字内容（字符串）
    """

    audio = AudioSegment.from_file(audio_path).set_channels(1)
    print(f"音频已转换为单音道，总时长: {len(audio) / 1000:.1f}s")

    # 按静音分段
    chunks = split_on_silence(
        audio,
        min_silence_len=500,
        silence_thresh=-40,
        keep_silence=300
    )

    # 二次切分
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > max_chunk_len:
            for i in range(0, len(chunk), max_chunk_len):
                final_chunks.append(chunk[i:i + max_chunk_len])
        else:
            final_chunks.append(chunk)

    print(f"共切分了 {len(final_chunks)} 段")

    full_text = []
    for i, chunk in enumerate(final_chunks):
        temp_wav = f"temp_chunk_{i}.wav"    # 临时文件名
        chunk.export(temp_wav, format=("wav"))

        with open(temp_wav, "rb") as audio_file:
            try:
                response = client.audio.transcriptions.create(
                    model="glm-asr-2512",
                    file=audio_file
                )

                text = response.text if hasattr(response, 'text') else str(response)
                full_text.append(text)
            except Exception as e:
                if os.path.exists(temp_wav):
                    os.remove(temp_wav)
                raise STTError(f"语音识别失败（第 {i+1} 段： {e}") from e

        print(f" 第 {i+1}/{len(final_chunks)} 段识别完成")
        os.remove(temp_wav)

    return "".join(full_text)


if __name__ == "__main__":
    import pathlib
    project_roof = pathlib.Path(__file__).parent.parent

    test_file = project_roof/"test.wav"    # 用 ffmpeg 转换为单声道

    try:
        print("开始识别...")
        result = speech_to_text(str(test_file))
        print("识别成功")
        print("-" * 50)
        print(result)
        print("-" * 50)
        print(f"共识别 {len(result)} 个字符")

    except FileNotFoundError:
        print(f"请先准备测试文件：放入根目录下的 {test_file}")

    except ValueError as e:
        print(f"识别失败: {e}")
