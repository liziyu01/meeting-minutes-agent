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

## 技术架构
```text
┌─────────────┐
│ 用户上传音频  
│ (.wav/.mp3) 
└──────┬──────┘
       ▼
┌─────────────┐
│ Streamlit   
│ 前端 :8501  
└──────┬──────┘
       │ HTTP POST
       ▼
┌─────────────┐
│ FastAPI     
│ 后端 :8000   
└──────┬──────┘
       ▼
┌─────────────┐
│ STT 模块    
│ GLM API     
└──────┬──────┘
       ▼
┌─────────────┐
│ LangGraph   
│ 工作流       
└──────┬──────┘
       ▼
┌─────────────┐
│ 摘要 → 待办  
│ 决策 → 格式化 
└──────┬──────┘
       ▼
┌─────────────┐
│ 返回前端展示  
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

### 2. 配置 API Key
```bash
# 创建 .env 文件，写入你的智谱 API Key
echo "ZHIPUAI_API_KEY=你的key" > .env
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

如果你想在本地开发而非 Docker：

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
│   ├── config.py        # 配置文件
│   └── frontend.py      # Streamlit 前端
├── tests/
│   └── test_graph.py    # 单元测试
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


## 许可
MIT License

---

## 作者
[Li Hong] - [https://github.com/liziyu01]
