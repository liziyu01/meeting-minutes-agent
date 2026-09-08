"""
LangGraph 工作流模块

将会议转录文本转换为机构化纪要： 摘要 -> 待办 -> 决策 -> Markdown 格式化。
"""
import json
import logging
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate
from app.utils import get_llm, WorkflowError

# 初始化 LLM
llm = get_llm(temperature=0.2)

# 定义状态
class MeetingState(TypedDict):
    """工作流状态，在节点间传递。"""
    transcript: str
    summary: Optional[str]
    action_items: Optional[list[str]]
    decisions: Optional[list[str]]
    final_output: str

# 节点函数
def summarize_node(state: MeetingState) -> dict:
    """生成会议摘要 (150-200字)"""
    prompt = ChatPromptTemplate.from_template(
        """你是一名专业的会议记录员。根据以下会议记录生成一份会议摘要。
    
    规则：
    1. 严格控制在 150-200 字之间
    2. 必须包含：核心议题、关键结论、后续行动方向  
    3. 使用客观、正式的中文
    4. 直接输出摘要段落，不要添加标题或任何前缀
    
    会议记录：
    {transcript}
    
    摘要："""
    )

    chain = prompt | llm
    response = chain.invoke({"transcript": state["transcript"]})
    return {"summary": response.content.strip()}

logger = logging.getLogger(__name__)
def action_items_node(state: MeetingState) -> dict:
    """
    提取待办事项并格式化为 Markdown 任务列表

    解析 LLM 输出的按行分割的文本，过滤空行后返回任务列表。
    若 LLM 输出异常（如未按格式），降级为空列表。
    Args:
        state: MeetingState 对象，包含 transcript 字段。

    Returns:
        包含 action_items 键的字典，值为待办事项列表。

    Example:
    >>> state = {"transcript": "张工负责前端开发，周三完成。"}
    >>> action_items_node(state)
    {"action_items": ["- [ ] 前端开发 (@张工) 周三"]}
    """
    prompt = ChatPromptTemplate.from_template(
        """你是一个会议助手。请从以下会议记录中提取所有待办事项。
    你必须**只返回一个 JSON 数组**，格式如下：
    [
        {{
            "task": "任务描述",
            "assignee": "负责人姓名（未提及则填"未指定"）",
            "deadline": "截止日期（未提及则填"未指定"）"
        }}
    ]
    
    要求：
    - 如果没有待办事项，返回空数组 []
    - 不要加任何解释、标记、或额外文字，只输出纯 JSON
    
    会议记录：
    {transcript}"""
    )

    chain = prompt | llm
    response = chain.invoke({"transcript": state["transcript"]})
    raw_text = response.content.strip()

    # 解析 JSON，失败则降级
    try:
        items_data = json.loads(raw_text)
    except json.JSONDecoderError:
        logger.warning("待办事项 JSON 解析失败，原始输出：%s", raw_text)
        items_data = []

    # 转 Markdown 列表字符串格式
    action_items = []
    for item in items_data:
        task = item.get("task", "")
        assignee = item.get("assignee", "未指定")
        deadline = item.get("deadline", "未指定")
        action_items.append(f"- [ ] {task} (@{assignee}) {deadline}")

    return {"action_items": action_items}

def decisions_node(state: MeetingState) -> dict:
    """
    提取会议中的关键决策。

    解析 LLM 返回的按行分割的决策列表，过滤空行后返回。
    决策是明确达成一致的结论（区别于待办事项）。
    """
    prompt = ChatPromptTemplate.from_template(
        """从以下会议记录中提取所有关键决策。
    输出格式（每行一条）:
    - 决策内容
    
    要求:
    - 只提取明确做出的结论（如 「确定了」「决定了」「一致同意」「达成共识」
    - 不要包含待办事项（待办是任务，决策是结论）
    - 每条决策简洁清晰，20字以内
    - 如果没有决策，输出「（无关键决策）」
    
    会议记录:
    {transcript}
    
    关键决策:"""
    )

    chain = prompt | llm
    response = chain.invoke({"transcript": state["transcript"]})
    raw_text = response.content.strip()

    # 处理「无关键决策」的降级情况
    if raw_text == "（无关键决策）":
        items = []
    else:
        items = [
            line.strip()
            for line in raw_text.split("\n")
            if line.strip()
        ]

    return {"decisions": items}

def format_node(state: MeetingState) -> dict:
    """
    将摘要、待办、决策拼接位 Markdown 格式的会议纪要。

    纯字符串操作，不调用 LLM
    """
    summary = state.get("summary") or "（未生成摘要）"
    action_items = state.get("action_items") or []
    decisions = state.get("decisions") or []

    md = f"""# 会议纪要
## 一、会议摘要
{summary}

## 二、待办事项
"""
    if action_items:
        for item in action_items:
            md += f"{item}\n"

    else:
        md += "（未提取到待办事项）"

    md += "\n## 三、关键决策\n"

    if decisions:
        for d in decisions:
                md += f"{d}\n"
    else:
        md += "（未提取到关键决策）\n"

    md += "\n---\n*本纪要由 AI 自动生成*\n"

    return {"final_output": md}

def build_workflow():
    """
    构建并编译 LangGraph 工作流。

    节点执行顺序：摘要 -> 待办 -> 决策 -> 格式化。
    """
    workflow = StateGraph(MeetingState)

    workflow.add_node("summarize", summarize_node)
    workflow.add_node("action_items", action_items_node)
    workflow.add_node("decisions", decisions_node)
    workflow.add_node("format", format_node)

    workflow.add_edge(START, "summarize")
    workflow.add_edge("summarize", "action_items")
    workflow.add_edge("action_items", "decisions")
    workflow.add_edge("decisions", "format")
    workflow.add_edge("format", END)

    return workflow.compile()

# llm as judge
def is_valid_meeting_content(text: str) -> tuple[bool, str]:
    """
    使用 LLM 判断输入是否为有效的会议记录内容。

    Returns:
        (is_valid: bool, reason: str)
    """
    judge_llm = get_llm(temperature=0.1)  # 低温度，确保判断稳定

    judge_prompt = ChatPromptTemplate.from_template(
        """你是一个专业的会议记录内容审核员。请判断以下文本是否属于有效的会议记录或会议讨论内容。

有效的会议记录应包含以下特征之一：
- 提到会议、讨论、决定、决议等明确的会议场景词汇
- 涉及项目进度、任务分配、方案评审、问题解决等工作内容
- 包含多人讨论的对话形式，或明确的决策和待办事项

无效的会议记录特征：
- 单纯的日常问候、闲聊（如"你好"、"今天天气真好"）
- 一句话的简单陈述，没有实质内容
- 不涉及任何工作或会议相关话题

请只输出 JSON 格式，不要输出任何其他内容：
{{
    "is_valid": true/false,
    "reason": "判断理由（一句话）"
}}

待判断的文本：
{text}"""
    )

    chain = judge_prompt | judge_llm
    response = chain.invoke({"text": text})

    try:
        result = json.loads(response.content.strip())
        return result.get("is_valid", False), result.get("reason", "")
    except json.JSONDecodeError:
        # 如果 LLM 返回的 JSON 解析失败，默认按有效处理（避免误伤）
        return True, "无法解析判断结果，默认放行"


def run_workflow(transcript: str) -> MeetingState:
    """
    执行完整工作流，返回包含 final_output 的完整状态。
    前置：使用 LLM as Judge 判断输入是否为有效会议内容。
    """
    transcript = transcript.strip()

    # ===== 前置裁判：LLM as Judge =====
    is_valid, reason = is_valid_meeting_content(transcript)

    if not is_valid:
        friendly_message = f"⚠️ 检测到非会议内容，已跳过生成。\n\n💡 建议：请提供包含会议讨论、决策或待办事项的录音或文本。\n\n📌 判断依据：{reason}"
        return {
            "transcript": transcript,
            "summary": friendly_message,
            "action_items": [],
            "decisions": [],
            "final_output": friendly_message
        }

    # ===== 通过验证，执行正常工作流 =====
    app = build_workflow()
    return app.invoke({"transcript": transcript})