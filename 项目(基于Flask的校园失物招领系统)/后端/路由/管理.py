# -*- coding: utf-8 -*-
"""管理模块路由：老师后台的审核、统计、用户管理、公告（flask-restx Namespace + Swagger 文档）"""
from flask import request, g
from flask_restx import Namespace, Resource, fields

from 工具 import 成功响应, 失败响应, 需要老师权限
from 业务.管理服务 import 审核物品, 批量审核, 待审核列表, 统计看板, 用户列表
from 业务.公告服务 import 公告列表, 发布公告


管理命名空间 = Namespace("admin", description="后台管理接口：仅老师可访问（统计看板 / 审核 / 用户 / 公告）")

审核请求模型 = 管理命名空间.model("审核请求", {
    "pass": fields.Boolean(required=True, description="是否通过：true=通过，false=拒绝", example=True),
    "feedback": fields.String(description="审核反馈（拒绝时填拒绝原因）", example="图片不清晰，请补充实物照片"),
})

批量审核请求模型 = 管理命名空间.model("批量审核请求", {
    "ids": fields.List(fields.Integer, required=True, description="待审核物品 ID 列表", example=[1, 2, 3]),
    "pass": fields.Boolean(required=True, description="是否通过：true=通过，false=拒绝", example=True),
    "feedback": fields.String(description="审核反馈（拒绝时填拒绝原因）"),
})

发布公告请求模型 = 管理命名空间.model("发布公告请求", {
    "title": fields.String(required=True, description="公告标题", example="失物招领平台使用须知"),
    "content": fields.String(required=True, description="公告内容", example="请如实填写物品信息，认领时需提供物品特征"),
})


@管理命名空间.route("/stats")
class 统计看板接口(Resource):
    @管理命名空间.doc(security="Bearer")
    @管理命名空间.response(200, "返回平台统计数据（用户数、物品数、待审核数等）")
    @管理命名空间.response(401, "未登录")
    @管理命名空间.response(403, "权限不足，仅老师可访问")
    @需要老师权限
    def get(self):
        """统计看板"""
        return 成功响应(统计看板())


@管理命名空间.route("/items/pending")
class 待审核列表接口(Resource):
    @管理命名空间.doc(security="Bearer", params={
        "page": "页码，默认 1",
        "size": "每页条数，默认 50",
    })
    @管理命名空间.response(200, "分页返回待审核物品列表")
    @管理命名空间.response(403, "权限不足，仅老师可访问")
    @需要老师权限
    def get(self):
        """待审核物品列表"""
        参数 = request.args
        页码 = 参数.get("page", 1, type=int)
        每页 = 参数.get("size", 50, type=int)
        return 成功响应(待审核列表(page=页码, size=每页))


@管理命名空间.route("/items/<int:id>/audit")
class 审核物品接口(Resource):
    @管理命名空间.doc(security="Bearer")
    @管理命名空间.expect(审核请求模型)
    @管理命名空间.response(200, "审核完成")
    @管理命名空间.response(400, "审核失败或已处理")
    @管理命名空间.response(403, "权限不足，仅老师可访问")
    @需要老师权限
    def post(self, id):
        """审核单个物品（通过 / 拒绝）"""
        数据 = request.get_json(silent=True) or {}
        通过 = bool(数据.get("pass"))
        反馈 = 数据.get("feedback") or ""
        ok = 审核物品(id, 通过=通过, 反馈=反馈)
        if not ok:
            return 失败响应(msg="审核失败或已处理", code=1, status=400)
        return 成功响应(None, msg=f"已{'通过' if 通过 else '拒绝'}")


@管理命名空间.route("/items/batch-audit")
class 批量审核接口(Resource):
    @管理命名空间.doc(security="Bearer")
    @管理命名空间.expect(批量审核请求模型)
    @管理命名空间.response(200, "批量审核完成")
    @管理命名空间.response(400, "未选择物品")
    @管理命名空间.response(403, "权限不足，仅老师可访问")
    @需要老师权限
    def post(self):
        """批量审核物品"""
        数据 = request.get_json(silent=True) or {}
        ids = 数据.get("ids") or []
        通过 = bool(数据.get("pass"))
        反馈 = 数据.get("feedback") or ""
        if not ids:
            return 失败响应(msg="请选择要审核的物品", code=1, status=400)
        批量审核(ids, 通过=通过, 反馈=反馈)
        return 成功响应(None, msg=f"已批量{'通过' if 通过 else '拒绝'} {len(ids)} 条")


@管理命名空间.route("/users")
class 用户列表接口(Resource):
    @管理命名空间.doc(security="Bearer")
    @管理命名空间.response(200, "返回全部学生与老师账号列表")
    @管理命名空间.response(403, "权限不足，仅老师可访问")
    @需要老师权限
    def get(self):
        """用户管理列表"""
        列表 = 用户列表()
        return 成功响应({"list": 列表, "total": len(列表)})


@管理命名空间.route("/announcements")
class 公告管理接口(Resource):
    @管理命名空间.doc(security="Bearer")
    @管理命名空间.response(200, "返回最新 20 条公告")
    @管理命名空间.response(403, "权限不足，仅老师可访问")
    @需要老师权限
    def get(self):
        """公告列表（后台管理用）"""
        return 成功响应(公告列表(limit=20))

    @管理命名空间.doc(security="Bearer")
    @管理命名空间.expect(发布公告请求模型)
    @管理命名空间.response(200, "公告已发布")
    @管理命名空间.response(400, "标题或内容不能为空")
    @管理命名空间.response(403, "权限不足，仅老师可访问")
    @需要老师权限
    def post(self):
        """发布公告"""
        用户 = g.当前用户
        数据 = request.get_json(silent=True) or {}
        标题 = 数据.get("title") or ""
        内容 = 数据.get("content") or ""
        try:
            发布公告(标题, 内容, 用户["姓名"])
        except ValueError as e:
            return 失败响应(msg=str(e), code=1, status=400)
        return 成功响应(None, msg="公告已发布")


# ---------------- 公告读取（公开接口，无需登录） ----------------

公告命名空间 = Namespace("announcements", description="公告接口：公开读取平台公告")


@公告命名空间.route("/announcements")
class 公开公告接口(Resource):
    @公告命名空间.doc(params={"limit": "返回条数，默认 6"})
    @公告命名空间.response(200, "返回最新公告列表")
    def get(self):
        """公开公告列表（大厅展示）"""
        limit = request.args.get("limit", 6, type=int)
        return 成功响应(公告列表(limit=limit))
