import json
from pathlib import Path
from app.graph import run_workflow


def run_evaluation():
    eval_file = Path(__file__).parent / "eval_cases.json"
    with open(eval_file, "r", encoding="utf-8") as f:
        suite = json.load(f)

    results = []
    for case in suite["cases"]:
        print(f"🔄 正在测试: {case['id']} - {case['name']}")
        try:
            result = run_workflow(case["input"])
            summary = result.get("summary", "")[:100]
            status = "✅ PASS" if "⚠️" not in summary else "⚠️ 边界触发"
        except Exception as e:
            summary = f"❌ ERROR: {str(e)}"
            status = "❌ FAIL"

        results.append({
            "id": case["id"],
            "name": case["name"],
            "expected": case["expect"],
            "actual": summary,
            "status": status
        })

    # 打印报告
    print("\n" + "=" * 60)
    print("📊 评测报告")
    print("=" * 60)
    for r in results:
        print(f"{r['status']}  {r['id']}: {r['name']}")
        print(f"  预期: {r['expected']}")
        print(f"  实际: {r['actual'][:80]}...")
        print("-" * 40)


if __name__ == "__main__":
    run_evaluation()