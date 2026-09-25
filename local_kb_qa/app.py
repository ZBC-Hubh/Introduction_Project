"""Gradio Web UI 入口：郑德森的数字人 Agent。

基于本地文档（个人蒸馏 skill + 简历知识库）的 RAG 数字分身：
以第一人称代表郑德森回答问题，严格依据知识库、零编造。

启动：
    python app.py
浏览器访问 http://127.0.0.1:7860
"""

import gradio as gr
from langchain_core.messages import HumanMessage, AIMessage

from qa_chain import get_answer


def _format_sources(source_docs) -> str:
    """把检索到的文档片段格式化成来源说明。"""
    if not source_docs:
        return ""
    lines = []
    for i, doc in enumerate(source_docs, 1):
        source = doc.metadata.get("source", "未知")
        snippet = doc.page_content.strip().replace("\n", " ")[:80]
        lines.append(f"{i}. [{source}] {snippet}")
    return "\n".join(lines)


def respond(message, history):
    """Gradio chatbot 回调：message 是当前问题，history 是 [(user, bot), ...] 历史对话。"""
    # 把 Gradio 的 tuple 历史转成 LangChain 的 Message 列表
    chat_history = []
    for user_msg, bot_msg in history:
        if user_msg:
            chat_history.append(HumanMessage(content=user_msg))
        if bot_msg:
            chat_history.append(AIMessage(content=bot_msg))

    try:
        answer, source_docs = get_answer(message, chat_history)
    except Exception as e:
        answer = (
            f"数字人暂时掉线：{e}\n\n请确认：\n"
            "1. Ollama 已启动（`ollama serve`）\n"
            "2. 已运行 `python ingest.py` 把个人知识库入库"
        )
        source_docs = []

    bot_reply = answer

    # tuples 模式要求输出完整的 [[user, bot], ...] 历史
    history.append([message, bot_reply])
    yield history


def clear_history():
    """清空对话按钮回调。"""
    return [], ""


def build_ui():
    with gr.Blocks(title="个人简介") as demo:
        gr.Markdown("# 自我介绍")

        chatbot = gr.Chatbot(height=520, type="tuples")
        with gr.Row():
            msg_input = gr.Textbox(
                placeholder="向郑德森提问…（回车发送）",
                scale=9,
                show_label=False,
            )
            submit_btn = gr.Button("发送", scale=1, variant="primary")

        with gr.Row():
            clear_btn = gr.Button("清空对话")
            status_box = gr.Textbox(
                value="就绪", label="状态", interactive=False, scale=2
            )

        # 提交逻辑（回车 / 按钮）
        submit_btn.click(
            respond, inputs=[msg_input, chatbot], outputs=[chatbot]
        ).then(lambda: "", outputs=[msg_input])
        msg_input.submit(
            respond, inputs=[msg_input, chatbot], outputs=[chatbot]
        ).then(lambda: "", outputs=[msg_input])
        clear_btn.click(clear_history, outputs=[chatbot, status_box])

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.queue().launch(server_name="127.0.0.1", server_port=7860)
