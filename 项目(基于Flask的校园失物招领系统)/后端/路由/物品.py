# -*- coding: utf-8 -*-
"""物品模块路由：失物/招领物品的发布、查询、修改、认领、标记找回（flask-restx + Swagger 文档）"""
from flask import request, g
from flask_restx import Namespace, Resource, fields

from 工具 import 成功响应, 失败响应, 需要登录
from 业务.物品服务 import (
    发布物品, 列表查询, 获取详情, 更新物品, 删除物品,
    标记找回, 我的发布, 申请认领
)


物品命名空间 = Namespace("items", description="物品接口：失物/招领的发布、大厅查询、详情、编辑、认领与找回")

# ---------------- Swagger 请求模型 ----------------

发布物品请求模型 = 物品命名空间.model("发布物品请求", {
    "type": fields.Integer(required=True, enum=[0, 1], description="类型：0=丢失，1=捡到", example=0),
    "category": fields.Integer(
        enum=[0, 1, 2, 3, 4],
        description="分类：0=电子设备，1=证件卡类，2=书籍文具，3=生活用品，4=其他", example=0,
    ),
    "title": fields.String(required=True, description="标题", example="黑色校园卡"),
    "description": fields.String(description="详细描述", example="在二食堂丢失，卡面有姓名"),
    "location": fields.String(description="丢失/拾获地点", example="二食堂一楼"),
    "image_url": fields.String(description="图片地址（先调用 /api/upload 获取）", example="/上传文件/xxx.jpg"),
})

更新物品请求模型 = 物品命名空间.model("更新物品请求", {
    "type": fields.Integer(enum=[0, 1], description="类型：0=丢失，1=捡到"),
    "category": fields.Integer(description="分类 0-4"),
    "title": fields.String(description="标题"),
    "description": fields.String(description="详细描述"),
    "location": fields.String(description="地点"),
    "image_url": fields.String(description="图片地址"),
})

认领请求模型 = 物品命名空间.model("认领请求", {
    "reason": fields.String(description="认领理由（描述物品特征以证明身份）", example="卡面有我的姓名和照片"),
})


@物品命名空间.route("")
class 物品列表接口(Resource):
    @物品命名空间.doc(params={
        "type": "类型筛选：0=丢失，1=捡到（可选）",
        "category": "分类筛选 0-4（可选）",
        "keyword": "关键词，匹配标题/描述（可选）",
        "page": "页码，默认 1",
        "size": "每页条数，默认 12",
    })
    @物品命名空间.response(200, "分页返回大厅物品列表")
    def get(self):
        """物品大厅列表（仅展示审核通过的物品）"""
        参数 = request.args
        try:
            类型 = 参数.get("type", type=int)
            分类 = 参数.get("category", type=int)
            关键词 = 参数.get("keyword") or None
            页码 = 参数.get("page", 1, type=int)
            每页 = 参数.get("size", 12, type=int)
        except (TypeError, ValueError):
            return 失败响应(msg="参数格式错误", code=1, status=400)
        数据 = 列表查询(type=类型, category=分类, keyword=关键词, page=页码, size=每页)
        return 成功响应(数据)

    @物品命名空间.doc(security="Bearer")
    @物品命名空间.expect(发布物品请求模型)
    @物品命名空间.response(200, "发布成功，返回新物品 id，等待老师审核")
    @物品命名空间.response(400, "参数校验失败")
    @物品命名空间.response(401, "未登录")
    @需要登录
    def post(self):
        """发布失物/招领信息"""
        用户 = g.当前用户
        数据 = request.get_json(silent=True) or {}
        try:
            id = 发布物品(用户["id"], 用户["身份"], 数据)
        except ValueError as e:
            return 失败响应(msg=str(e), code=1, status=400)
        return 成功响应({"id": id}, msg="发布成功，等待审核")


@物品命名空间.route("/hot")
class 热门物品接口(Resource):
    @物品命名空间.response(200, "返回最新的 6 条审核通过物品")
    def get(self):
        """首页热门物品（最新 6 条审核通过）"""
        数据 = 列表查询(audit_status=1, page=1, size=6, 仅审核通过=True)
        return 成功响应(数据)


@物品命名空间.route("/mine")
class 我的发布接口(Resource):
    @物品命名空间.doc(security="Bearer")
    @物品命名空间.response(200, "返回当前用户发布的全部物品")
    @物品命名空间.response(401, "未登录")
    @需要登录
    def get(self):
        """我的发布列表（含待审核/已拒绝）"""
        用户 = g.当前用户
        return 成功响应(我的发布(用户["id"], 用户["身份"]))


@物品命名空间.route("/<int:id>")
class 物品详情接口(Resource):
    @物品命名空间.response(200, "返回物品详情")
    @物品命名空间.response(404, "物品不存在")
    def get(self, id):
        """物品详情"""
        数据 = 获取详情(id)
        if 数据 is None:
            return 失败响应(msg="物品不存在", code=404, status=404)
        return 成功响应(数据)

    @物品命名空间.doc(security="Bearer")
    @物品命名空间.expect(更新物品请求模型)
    @物品命名空间.response(200, "更新成功")
    @物品命名空间.response(401, "未登录")
    @物品命名空间.response(403, "非发布者本人或老师，无权限")
    @需要登录
    def put(self, id):
        """更新物品信息（仅发布者本人）"""
        用户 = g.当前用户
        数据 = request.get_json(silent=True) or {}
        ok = 更新物品(id, 用户["id"], 用户["身份"], 数据)
        if not ok:
            return 失败响应(msg="更新失败或无权限", code=1, status=403)
        return 成功响应(None, msg="更新成功")

    @物品命名空间.doc(security="Bearer")
    @物品命名空间.response(200, "删除成功")
    @物品命名空间.response(401, "未登录")
    @物品命名空间.response(403, "非发布者本人或老师，无权限")
    @需要登录
    def delete(self, id):
        """删除物品（发布者本人或老师）"""
        用户 = g.当前用户
        ok = 删除物品(id, 用户["id"], 用户["身份"], 允许老师=True)
        if not ok:
            return 失败响应(msg="删除失败或无权限", code=1, status=403)
        return 成功响应(None, msg="删除成功")


@物品命名空间.route("/<int:id>/claim")
class 物品认领接口(Resource):
    @物品命名空间.doc(security="Bearer")
    @物品命名空间.expect(认领请求模型)
    @物品命名空间.response(200, "认领申请已提交")
    @物品命名空间.response(400, "物品不可认领")
    @物品命名空间.response(401, "未登录")
    @需要登录
    def post(self, id):
        """申请认领物品"""
        用户 = g.当前用户
        数据 = request.get_json(silent=True) or {}
        try:
            申请认领(id, 用户["id"], 用户["身份"], 数据.get("reason") or "")
        except ValueError as e:
            return 失败响应(msg=str(e), code=1, status=400)
        return 成功响应(None, msg="认领申请已提交")


@物品命名空间.route("/<int:id>/complete")
class 物品找回接口(Resource):
    @物品命名空间.doc(security="Bearer")
    @物品命名空间.response(200, "已标记为已找回（3 天后自动从大厅隐藏）")
    @物品命名空间.response(401, "未登录")
    @物品命名空间.response(403, "非发布者本人或老师，无权限")
    @需要登录
    def post(self, id):
        """标记物品为已找回"""
        用户 = g.当前用户
        ok = 标记找回(id, 用户["id"], 用户["身份"], 允许老师=True)
        if not ok:
            return 失败响应(msg="操作失败或无权限", code=1, status=403)
        return 成功响应(None, msg="已标记为已找回")
