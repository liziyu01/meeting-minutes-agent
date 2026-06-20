"""
LLM 工具函数模块

提供统一的 LLM 实例创建接口，封装智普 API 的配置细节
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


__all__ = ["get_llm"]

load_dotenv()

ZHIPUAI_API_KEY = os.getenv("zhipuai_api_key")
if not ZHIPUAI_API_KEY:
    raise ValueError(
        "未找到 ZHIPU_API_KEY, 请检查 .env 文件"
    )

def get_llm(temperature: float = 0.2) -> ChatOpenAI:
    """
    获取 ChatOpenAI 实例（智谱 GLM-4-Flash）
    智谱 API 兼容 OpenAI 格式，故使用 ChatOpenAI 并替换 base_url。
    temperature 默认 0.2，适合结构化信息提取任务。

    Args:
        temperature: 输出随机性，0.0~1.0。默认 0.2

    Returns: Chat0penAI 实例

    """
    return ChatOpenAI(
        model="glm-4.7-flash",
        temperature=temperature,
        api_key=ZHIPUAI_API_KEY,
        base_url="https://open.bigmodel.cn/api/paas/v4"
    )

if __name__ == "__main__":
    # 测试模型参数 (temperature=0.2)
    client = get_llm()
    response = client.invoke("用一句话介绍你自己")
    print(response.content)
    print("-" * 50)

    # 测试高创造性 (temaperature=0.9)
    lient = get_llm(temperature=0.9)
    response = client.invoke("用一句话介绍你自己")
    print(response.content)
