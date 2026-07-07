"""
测试 LangGraph 工作流中的各个节点
"""
import pytest
from unittest.mock import MagicMock, patch
from app.graph import summarize_node, action_items_node,decisions_node,format_node

# 模拟会议状态
mock_state = {
    "transcript": "今天会议决定于下周三发布新产品，张三负责测试，李四负责宣发。",
    "summary": None,
    "action_items": None,
    "decisions": None,
    "final_output": ""
}

def test_format_node():
    """
    测试格式化输出节点：期望输出为包含 摘要、待办、决策 的 Markdown
    """
    state = {
        "transcript": "",
        "summary": "这是一个摘要",
        "action_items": ["- [ ] 任务1 （@王五） 周五"],
        "decisions": ["- 决策A"],
        "final_output": ""
    }
    result = format_node(state)
    assert "## 一、会议摘要" in result["final_output"]
    assert "这是一个摘要" in result["final_output"]
    assert "## 二、待办事项" in result["final_output"]
    assert "- [ ] 任务1" in result["final_output"]
    assert "## 三、关键决策" in result["final_output"]
    assert "- 决策A" in result["final_output"]

@pytest.mark.integration
def test_full_workflow_integration():
    """短文本测试工作流，验证端到端输出结构"""
    from app.graph import run_workflow
    transcript = "今天讨论项目进度，会议觉得下周五上线，由张三负责部署和运营"
    result = run_workflow(transcript)

    assert "final_output" in result
    assert "summary" in result
    assert isinstance(result["action_items"], list)
    assert isinstance(result["decisions"], list)
