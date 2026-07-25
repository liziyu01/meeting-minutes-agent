"""
LLM 工具函数模块

提供统一的 LLM 实例创建接口，封装智普 API 的配置细节
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from app.config import MODEL_NAME, TEMPERATURE, TIMEOUT


__all__ = ["get_llm"]

load_dotenv()

ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY")
if not ZHIPUAI_API_KEY:
    raise ValueError(
        "未找到 ZHIPUAI_API_KEY, 请检查 .env 文件"
    )

def get_llm(temperature: float = TEMPERATURE, timeout = TIMEOUT) -> ChatOpenAI:
    """
    获取 ChatOpenAI 实例（智谱 GLM-4-Flash）
    temperature 默认 0.2
    """
    return ChatOpenAI(
        model=MODEL_NAME,
        temperature=temperature,
        api_key=ZHIPUAI_API_KEY,
        base_url="https://open.bigmodel.cn/api/paas/v4",
        timeout=timeout,
    )

# 自定义异常类
class MeetingAgentError(Exception):
    """基础异常"""
    pass

class STTError(MeetingAgentError):
    """语音识别错误"""
    pass

class WorkflowError(MeetingAgentError):
    pass

class LLMError(MeetingAgentError):
    """LLM调用错误"""
    pass

if __name__ == "__main__":
    # 测试模型参数 (temperature=0.2)
    client = get_llm()
    response = client.invoke("用一句话介绍你自己")
    print(response.content)
    print("-" * 50)

    # 测试高创造性 (temaperature=0.9)
    client = get_llm(temperature=0.9)
    response = client.invoke("用一句话介绍你自己")
    print(response.content)

