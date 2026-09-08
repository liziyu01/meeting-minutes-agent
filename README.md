# 会议纪要 Agent

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.137.1-green)
![LangGraph](https://img.shields.io/badge/LangGraph-1.2.5-orange)
![Docker](https://img.shields.io/badge/Docker-ready-blue)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

> 上传会议录音，AI 自动生成结构化纪要：摘要、待办事项、关键决策，一键下载 Markdown 文件。

---

## 功能亮点

- **语音转文字**：基于智谱 GLM API，支持中文普通话，高准确率
- **智能分析**：LangGraph 编排多个 LLM 节点，并行提取摘要、待办、决策
- **结构化输出**：Markdown 格式纪要，可直接用于工作汇报
- **Web 界面**：Streamlit 构建的简洁前端，拖拉拽上传，即时预览
- **一键部署**：Docker Compose 启动，无需配置 Python 环境
- **健壮性**：JSON 结构化输出、异常处理、单元测试覆盖

---

## 飞书机器人集成

支持在飞书中通过语音消息一键生成会议纪要。

### 配置飞书应用
1. 在飞书开放平台创建企业自建应用，启用机器人能力
2. 获取 `App ID` 和 `App Secret`
3. 在权限管理中开启以下权限：
   - `im:message`
   - `im:message.p2p_msg:readonly`
   - `im:resource`
4. 在事件订阅中配置 `im.message.receive_v1` 事件

### 环境变量配置
在 `.env` 文件中添加：

```env
# 飞书应用凭证
app_id=你的AppID
app_secret=你的AppSecret
```

### 启动机器人
```bash
python feishu_bot.py
```

在飞书中给机器人发送语音消息，即可自动生成会议纪要并回复。

---

## 技术架构

```text
┌─────────────┐
│ 用户上传音频  │
│ (.wav/.mp3)  │
└──────┬──────┘
       ▼
┌─────────────┐
│ Streamlit    │
│ 前端 :8501   │
└──────┬──────┘
       │ HTTP POST
       ▼
┌─────────────┐
│ FastAPI      │
│ 后端 :8000   │
└──────┬──────┘
       ▼
┌─────────────┐
│ STT 模块     │
│ GLM API      │
└──────┬──────┘
       ▼
┌─────────────┐
│ LangGraph    │
│ 工作流        │
└──────┬──────┘
       ▼
┌─────────────┐
│ 摘要 → 待办  │
│ 决策 → 格式化 │
└──────┬──────┘
       ▼
┌─────────────┐
│ 返回前端展示  │
└─────────────┘
```

---

## 快速开始

### 前置要求
- Docker & Docker Compose
- 智谱 API Key（[注册链接](https://open.bigmodel.cn/)）

### 1. 克隆项目
```bash
git clone https://github.com/liziyu01/meeting-minutes-agent.git
cd meeting-minutes-agent
```

### 2. 配置环境变量
```bash
# 创建 .env 文件，写入所需环境变量
ZHIPUAI_API_KEY=你的智谱APIKey
app_id=你的飞书AppID
app_secret=你的飞书AppSecret
```

### 3. 启动服务
```bash
docker-compose up -d
```

### 4. 打开浏览器
- 前端界面：http://localhost:8501
- API 文档：http://localhost:8000/docs

### 5. 停止服务
```bash
docker-compose down
```

---

## 本地开发

```bash
# 1. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 .env

# 4. 启动后端
python -m app.main

# 5. 另开终端，启动前端
streamlit run app/frontend.py
```

---

## API 接口

| 方法 | 路径                   | 说明                          |
| ---- | ---------------------- | ----------------------------- |
| GET  | `/`                    | 健康检查                      |
| POST | `/upload`              | 上传音频，返回识别文字 + 纪要 |
| GET  | `/download/{filename}` | 下载生成的 `.md` 文件         |
| GET  | `/docs`                | Swagger API 文档              |

### 上传接口示例
```bash
curl -F "file=@meeting.wav" http://localhost:8000/upload
```

返回：
```json
{
  "success": true,
  "transcript": "今天讨论了...",
  "minutes": "# 📝 会议纪要\n...",
  "summary": "...",
  "action_items": ["- [ ] 任务1"],
  "decisions": ["- 决策1"],
  "download_url": "/download/xxx.md"
}
```

---

## 项目结构

```
meeting-minutes-agent/
├── app/
│   ├── main.py          # FastAPI 主程序
│   ├── stt.py           # 语音转文字模块
│   ├── graph.py         # LangGraph 工作流
│   ├── utils.py         # 工具函数 & 异常定义
│   ├── feishu_bot.py    # 飞书机器人集成
│   └── frontend.py      # Streamlit 前端
├── tests/
│   ├── test_graph.py    # 单元测试
│   ├── eval_cases.json  # 评测用例集
│   └── run_eval.py      # 评测运行脚本
├── uploads/             # 上传的音频（不提交 Git）
├── outputs/             # 生成的纪要（不提交 Git）
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 运行测试

```bash
pytest tests/
```

---

## 评测集

项目包含 11 条核心评测用例，覆盖正向、边界、压力三大类：

| 类别 | 用例数 | 说明 |
| :--- | :--- | :--- |
| 正向测试 | 3 | 验证标准会议场景正常生成纪要 |
| 边界测试 | 5 | 验证闲聊/超短文本等无效输入被正确拦截 |
| 压力测试 | 3 | 验证超长文本、特殊字符等极端场景稳定性 |

运行评测：
```bash
python tests/run_eval.py
```

引入 LLM as Judge 前置裁判后，边界防御准确率从 0% 提升至 100%。

---

## 许可

MIT License

---

## 作者

[Li Hong] - [https://github.com/liziyu01]
```

---