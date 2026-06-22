"""
测试 LangGraph 工作流

用模拟会议文本验证每个节点是否正常工作
"""
from app.graph import run_workflow

mock_transcript =  """
今天会议主要讨论了三件事。
第一，产品发布计划，大家一致同意把发布时间定在下周五。
第二，关于新功能的技术方案，李工建议用微服务架构，王经理表示同意，
让李工负责出详细方案，下周三之前完成。
第三，预算问题，财务部反馈预算超支，决定暂时冻结非紧急采购。
张经理提醒大家周五前提交周报。
"""

if __name__ == "__main__":
    print("开始运行工作流...\n")

    result = run_workflow(mock_transcript)

    print("=" * 50)
    print(result["final_output"])
    print("=" * 50)

    print("\n统计信息")
    print(f"- 摘要字数：{len(result.get('summary', ''))}")
    print(f"- 待办事项数：{len(result.get('action_items', []))}")
    print(f"- 决策数：{len(result.get('decisions', []))}")

