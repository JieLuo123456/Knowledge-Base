"""
app/api/feishu.py
飞书机器人 Webhook 入口（骨架，G6, FR-6.2）

TODO: 完整实现需要飞书应用凭证（FEISHU_APP_ID / FEISHU_APP_SECRET 等）。
      未配置凭证时此模块不影响主流程，可通过环境变量条件开启。

当前骨架功能：
  - URL 验证挑战（challenge）响应
  - 签名校验骨架（HMAC-SHA256）
  - 消息事件转发至 QA 逻辑
"""

import hashlib
import hmac
import time
from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException, Request

from config.settings import settings

router = APIRouter(prefix="/api/feishu", tags=["Feishu"])


def _verify_signature(
    timestamp: str,
    nonce: str,
    body: bytes,
    expected_sig: str,
) -> bool:
    """
    飞书事件签名校验（HMAC-SHA256）(FR-6.2)

    TODO: 按飞书文档完整实现校验逻辑后，移除此 TODO 注释。
    """
    if not settings.feishu_encrypt_key:
        # 未配置加密 Key，跳过校验（开发环境）
        return True

    token = settings.feishu_encrypt_key.encode("utf-8")
    content = f"{timestamp}{nonce}".encode("utf-8") + body
    digest = hmac.new(token, content, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, expected_sig)


@router.post("/webhook", summary="飞书事件 Webhook (FR-6.2, 骨架)")
async def feishu_webhook(
    request: Request,
    x_lark_signature: str = Header(default=""),
    x_lark_request_timestamp: str = Header(default=""),
    x_lark_request_nonce: str = Header(default=""),
) -> Dict[str, Any]:
    """
    接收飞书事件推送，转发给 QA 逻辑。

    TODO:
      1. 完善签名校验逻辑
      2. 解析消息内容（text_message / at_message）
      3. 调用 generate_answer 并回复用户
      4. 处理重复事件（event_id 去重）
    """
    if not settings.feishu_app_id:
        raise HTTPException(
            status_code=503,
            detail="飞书机器人未配置，请在 .env 中设置 FEISHU_APP_ID 等凭证。",
        )

    body = await request.body()

    # 签名校验（骨架）
    if not _verify_signature(
        x_lark_request_timestamp,
        x_lark_request_nonce,
        body,
        x_lark_signature,
    ):
        raise HTTPException(status_code=401, detail="飞书签名校验失败")

    payload: Dict[str, Any] = await request.json()

    # 飞书 URL 验证挑战
    if "challenge" in payload:
        return {"challenge": payload["challenge"]}

    # TODO: 解析事件类型，提取用户消息，调用 QA 并回复
    # event = payload.get("event", {})
    # question = event.get("message", {}).get("content", "")
    # answer = generate_answer(question)
    # ... 调用飞书发送消息 API ...

    return {"status": "received"}
