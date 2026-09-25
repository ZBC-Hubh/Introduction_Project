# -*- coding: utf-8 -*-
"""消息模块路由：用户间私聊（flask-restx Namespace + Swagger 文档）"""
from flask import request, g
from flask_restx import Namespace, Resource, fields

from 工具 import 成功响应, 失败响应, 需要登录
from 业务.消息服务 import (
    发送消息, 获取会话, 获取会话列表, 标记已读, 获取未读数
)


消息命名空间 = Namespace("messages", description="消息接口：学生/老师之间的站内私聊")

发送消息请求模型 = 消息命名空间.model("发送消息请求", {
    "receiver_id": fields.Integer(required=True, description="接收者用户 ID", example=2),
    "receiver_type": fields.String(
        required=True, enum=["teacher", "student"], description="接收者身份", example="teacher",
    ),
    "content": fields.String(required=True, description="消息内容（最长 500 字）", example="同学你好，我看到你丢的校园卡了"),
    "item_id": fields.Integer(description="关联物品 ID（可选）", example=1),
})


@消息命名空间.route("/send")
class 发送消息接口(Resource):
    @消息命名空间.doc(security="Bearer")
    @消息命名空间.expect(发送消息请求模型)
    @消息命名空间.response(200, "消息已发送，返回消息 id")
    @消息命名空间.response(400, "接收者信息不完整 / 身份无效 / 不能给自己发消息")
    @消息命名空间.response(401, "未登录")
    @需要登录
    def post(self):
        """发送私聊消息"""
        当前用户 = g.当前用户
        数据 = request.get_json(silent=True) or {}
        接收者ID = 数据.get("receiver_id")
        接收者身份 = 数据.get("receiver_type")
        内容 = 数据.get("content", "")
        物品ID = 数据.get("item_id")

        if not 接收者ID or not 接收者身份:
            return 失败响应(msg="接收者信息不完整", code=1, status=400)
        if 接收者身份 not in ("teacher", "student"):
            return 失败响应(msg="接收者身份无效", code=1, status=400)
        if int(接收者ID) == 当前用户["id"] and 接收者身份 == 当前用户["身份"]:
            return 失败响应(msg="不能给自己发消息", code=1, status=400)

        try:
            id = 发送消息(
                当前用户["id"], 当前用户["身份"],
                int(接收者ID), 接收者身份,
                内容, 物品ID
            )
        except ValueError as e:
            return 失败响应(msg=str(e), code=1, status=400)
        return 成功响应({"id": id}, msg="消息已发送")


@消息命名空间.route("/conversation")
class 会话详情接口(Resource):
    @消息命名空间.doc(security="Bearer", params={
        "other_id": "对方用户 ID（必填）",
        "other_type": "对方身份：teacher / student（必填）",
        "limit": "返回条数上限，默认 50",
    })
    @消息命名空间.response(200, "返回与对方的聊天记录（自动把对方发来的消息标记为已读）")
    @消息命名空间.response(400, "对方信息不完整或身份无效")
    @消息命名空间.response(401, "未登录")
    @需要登录
    def get(self):
        """获取与某人的会话记录（进入会话即已读）"""
        当前用户 = g.当前用户
        对方ID = request.args.get("other_id", type=int)
        对方身份 = request.args.get("other_type")
        limit = request.args.get("limit", 50, type=int)

        if not 对方ID or not 对方身份:
            return 失败响应(msg="对方信息不完整", code=1, status=400)
        if 对方身份 not in ("teacher", "student"):
            return 失败响应(msg="对方身份无效", code=1, status=400)

        # 标记已读
        标记已读(当前用户["id"], 当前用户["身份"], 对方ID, 对方身份)

        消息列表 = 获取会话(当前用户["id"], 当前用户["身份"], 对方ID, 对方身份, limit)
        return 成功响应({"messages": 消息列表})


@消息命名空间.route("/conversations")
class 会话列表接口(Resource):
    @消息命名空间.doc(security="Bearer")
    @消息命名空间.response(200, "返回当前用户的会话列表（每个联系人一条，含未读数）")
    @消息命名空间.response(401, "未登录")
    @需要登录
    def get(self):
        """获取会话列表"""
        当前用户 = g.当前用户
        列表 = 获取会话列表(当前用户["id"], 当前用户["身份"])
        return 成功响应({"list": 列表, "total": len(列表)})


@消息命名空间.route("/unread")
class 未读数接口(Resource):
    @消息命名空间.doc(security="Bearer")
    @消息命名空间.response(200, "返回当前用户未读消息总数")
    @消息命名空间.response(401, "未登录")
    @需要登录
    def get(self):
        """获取未读消息总数（前端轮询小红点）"""
        当前用户 = g.当前用户
        未读数 = 获取未读数(当前用户["id"], 当前用户["身份"])
        return 成功响应({"count": 未读数})
