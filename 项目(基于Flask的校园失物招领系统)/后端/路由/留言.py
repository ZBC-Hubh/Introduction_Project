# -*- coding: utf-8 -*-
"""留言模块路由：物品详情下的留言板（flask-restx Namespace + Swagger 文档）"""
from flask import request, g
from flask_restx import Namespace, Resource, fields

from 工具 import 成功响应, 失败响应, 需要登录
from 业务.留言服务 import 留言列表, 发布留言


留言命名空间 = Namespace("item-messages", description="留言接口：物品详情页的留言板")

发布留言请求模型 = 留言命名空间.model("发布留言请求", {
    "content": fields.String(required=True, description="留言内容", example="我在三教捡到一张类似的卡"),
})


@留言命名空间.route("/<int:item_id>/messages")
class 物品留言接口(Resource):
    @留言命名空间.response(200, "返回该物品的全部留言")
    def get(self, item_id):
        """获取物品的留言列表"""
        return 成功响应(留言列表(item_id))

    @留言命名空间.doc(security="Bearer")
    @留言命名空间.expect(发布留言请求模型)
    @留言命名空间.response(200, "留言成功")
    @留言命名空间.response(400, "留言内容不能为空")
    @留言命名空间.response(401, "未登录")
    @需要登录
    def post(self, item_id):
        """发布留言"""
        用户 = g.当前用户
        数据 = request.get_json(silent=True) or {}
        try:
            发布留言(item_id, 用户["id"], 用户["身份"], 数据.get("content") or "")
        except ValueError as e:
            return 失败响应(msg=str(e), code=1, status=400)
        return 成功响应(None, msg="留言成功")
