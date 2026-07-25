"""
Streamlit 前端界面
提供文件上传、纪要预览、下载功能
"""
import os
import streamlit as st
import requests
import json

# ===== 页面配置 =====
st.set_page_config(
    page_title="会议纪要 Agent",
    page_icon="📝",
    layout="wide",
)

# ===== 标题区 =====
st.title("📝 会议纪要 Agent")
st.markdown("上传会议录音，AI 自动生成结构化纪要。支持摘要、待办事项、关键决策提取。")

# ===== 侧边栏：配置 =====
with st.sidebar:
    st.header("⚙️ 设置")
    default_api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    api_base = st.text_input(
        "后端 API 地址",
        value=default_api_url,  # ✅ 从环境变量读取
        help="FastAPI 服务地址，默认本机 8000 端口"
    )
    st.divider()
    st.markdown("### 关于")
    st.markdown("技术栈：FastAPI + LangGraph + Streamlit")

# ===== 主区域：文件上传 =====
st.header("🎙️ 上传会议录音")
uploaded_file = st.file_uploader(
    "选择音频文件",
    type=["wav", "mp3", "m4a"],
    help="支持手机录音、会议软件导出的音频文件"
)

if uploaded_file is not None:
    # 显示文件信息
    col1, col2 = st.columns(2)
    with col1:
        st.audio(uploaded_file, format=f"audio/{uploaded_file.type.split('/')[-1]}")
    with col2:
        st.info(f"文件名: {uploaded_file.name}\n大小: {uploaded_file.size / 1024:.1f} KB")

    # 上传按钮
    if st.button("🚀 生成纪要", type="primary", use_container_width=True):
        with st.spinner("正在处理中... 这可能需要几秒到一分钟"):
            # 构造文件上传请求
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}

            try:
                # 调用后端 /upload 接口
                response = requests.post(
                    f"{api_base}/upload",
                    files=files,
                    timeout=120  # 长音频可能需要更久
                )
                response.raise_for_status()
                result = response.json()

                if result.get("success"):
                    st.success("✅ 纪要生成成功！")

                    # === 显示转录文本 ===
                    with st.expander("📄 查看完整转录文本"):
                        st.text_area("识别文字", result["transcript"], height=200)

                    # === 显示结构化纪要 ===
                    st.header("📋 会议纪要")

                    # 分栏显示摘要
                    if result.get("summary"):
                        st.subheader("📝 摘要")
                        st.info(result["summary"])

                    # 待办事项
                    if result.get("action_items"):
                        st.subheader("✅ 待办事项")
                        for item in result["action_items"]:
                            st.markdown(item)

                    # 关键决策
                    if result.get("decisions"):
                        st.subheader("🎯 关键决策")
                        for d in result["decisions"]:
                            st.markdown(d)

                    # === 完整 Markdown 预览 ===
                    with st.expander("📝 查看完整 Markdown"):
                        st.markdown(result.get("minutes", ""))

                    # === 下载按钮 ===
                    if result.get("download_url"):
                        download_url = f"{api_base}{result['download_url']}"
                        st.download_button(
                            label="📥 下载纪要 (.md)",
                            data=result["minutes"],
                            file_name=f"会议纪要.md",
                            mime="text/markdown"
                        )
                else:
                    st.error(f"❌ 处理失败: {result.get('error', '未知错误')}")

            except requests.exceptions.ConnectionError:
                st.error(f"❌ 无法连接到后端服务 ({api_base})。请确保 FastAPI 服务已启动。")
            except requests.exceptions.Timeout:
                st.error("❌ 请求超时。可能是音频太长或网络问题，请重试。")
            except Exception as e:
                st.error(f"❌ 发生错误: {str(e)}")
