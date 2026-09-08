import os
import json
import asyncio
import threading
from pathlib import Path
import httpx

import lark_oapi as lark
from lark_oapi.api.im.v1 import *
from app.stt import speech_to_text
from app.graph import run_workflow
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("app_id")
APP_SECRET = os.getenv("app_secret")


async def get_tenant_access_token() -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": APP_ID, "app_secret": APP_SECRET}
        )
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"获取token失败:{data}")
        return data["tenant_access_token"]


api_client = lark.Client.builder()\
    .app_id(APP_ID)\
    .app_secret(APP_SECRET)\
    .build()


def handle_message_event(event: P2ImMessageReceiveV1) -> None:
    msg = event.event.message
    sender = event.event.sender
    open_id = sender.sender_id.open_id
    message_id = msg.message_id

    if msg.message_type != "audio":
        return

    try:
        content = json.loads(msg.content)
    except json.JSONDecodeError:
        return

    file_key = content.get("file_key")
    if not file_key:
        return

    asyncio.create_task(process_audio_task(file_key, message_id, open_id))


async def process_audio_task(file_key: str, message_id: str, open_id: str):
    temp_path = Path(f"temp_{file_key}.ogg")
    try:
        token = await get_tenant_access_token()
        url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/resources/{file_key}"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"type": "file"}

        async with httpx.AsyncClient() as client:
            download_resp = await client.get(url, headers=headers, params=params)
            if download_resp.status_code != 200:
                print(f"[下载语音HTTP失败] status={download_resp.status_code}, resp={download_resp.text}")
                return
            temp_path.write_bytes(download_resp.content)


        transcript = speech_to_text(str(temp_path))
        result = run_workflow(transcript)
        summary = result["final_output"]

        reply_content = json.dumps({"text": summary})
        msg_req = CreateMessageRequest.builder()\
            .receive_id_type("open_id")\
            .request_body(CreateMessageRequestBody.builder()
                          .receive_id(open_id)
                          .msg_type("text")
                          .content(reply_content)
                          .build())\
            .build()


        resp = api_client.im.v1.message.create(msg_req)
        if resp.code != 0:
            print(f"发送消息失败 code={resp.code},msg={resp.msg}")

    except Exception as e:
        print(f"[处理语音异常] {e}")
    finally:
        if temp_path.exists():
            os.remove(temp_path)


def run_ws_client():
    event_handler = lark.EventDispatcherHandler.builder("", "")\
        .register_p2_im_message_receive_v1(handle_message_event)\
        .build()

    ws_cli = lark.ws.Client(
        APP_ID,
        APP_SECRET,
        event_handler=event_handler,
        log_level=lark.LogLevel.INFO
    )
    print("🤖飞书机器人WebSocket已启动，等待消息...")
    ws_cli.start()


async def main():
    ws_thread = threading.Thread(target=run_ws_client, daemon=True)
    ws_thread.start()

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
