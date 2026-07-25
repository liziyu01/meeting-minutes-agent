"""项目配置"""

from pathlib import Path

# ===== 路径计算 =====
CURRENT_DIR = Path(__file__).parent  # app/
PROJECT_ROOT = CURRENT_DIR.parent   # 项目根目录

UPLOADS_DIR = PROJECT_ROOT / "uploads"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
# 自动创建目录
UPLOADS_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

# ===== 音频配置 =====
ALLOWED_AUDIO_TYPES = {".wav", ".mp3", ".m4a"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
CHUNK_LENGTH = 28000  # 音频分段长度（毫秒）

# ===== LLM 配置 =====
MODEL_NAME = "glm-4-flash"
TEMPERATURE = 0.2
TIMEOUT = 60