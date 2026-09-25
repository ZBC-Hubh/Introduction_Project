# -*- coding: utf-8 -*-
"""认证模块路由：注册、登录、获取当前用户（flask-restx Namespace + Swagger 文档）"""
from flask import request, g
from flask_restx import Namespace, Resource, fields

from 工具 import 成功响应, 失败响应, 需要登录
from 业务.认证服务 import 注册, 登录, 获取用户信息


认证命名空间 = Namespace("auth", description="认证接口：注册、登录、获取当前登录用户")

# ---------------- Swagger 请求模型 ----------------

注册请求模型 = 认证命名空间.model("注册请求", {
    "identity": fields.String(
        required=True, enum=["teacher", "student"],
        description="身份（兼容字段名：身份 / role）", example="student",
    ),
    "student_id": fields.String(description="学号（学生注册必填）", example="2024001"),
    "teacher_id": fields.String(description="工号（老师注册必填）", example="T1001"),
    "password": fields.String(required=True, description="密码（至少 6 位）", example="123456"),
    "name": fields.String(required=True, description="姓名", example="张三"),
    "class_name": fields.String(description="班级（学生可选）", example="软件2201班"),
    "department": fields.String(description="院系（老师可选）", example="计算机学院"),
    "phone": fields.String(description="手机号（可选）", example="13800138000"),
})

登录请求模型 = 认证命名空间.model("登录请求", {
    "identity": fields.String(
        required=True, enum=["teacher", "student"],
        description="身份（兼容字段名：身份 / role）", example="student",
    ),
    "account": fields.String(
        required=True, description="学号/工号（兼容字段名：编号 / student_id / teacher_id）",
        example="2024001",
    ),
    "password": fields.String(required=True, description="密码", example="123456"),
})

令牌数据模型 = 认证命名空间.model("令牌数据", {
    "token": fields.String(description="JWT 令牌，后续请求放入 Authorization: Bearer <token>"),
})

令牌响应模型 = 认证命名空间.model("令牌响应", {
    "code": fields.Integer(example=0, description="0=成功"),
    "msg": fields.String(example="登录成功"),
    "data": fields.Nested(令牌数据模型),
})


@认证命名空间.route("/register")
class 注册接口(Resource):
    @认证命名空间.expect(注册请求模型, validate=False)
    @认证命名空间.response(200, "注册成功，返回 JWT 令牌", 令牌响应模型)
    @认证命名空间.response(400, "参数错误或学号/工号已注册")
    def post(self):
        """新用户注册（学生 / 老师）"""
        数据 = request.get_json(silent=True) or {}
        # 兼容前端字段：role/identity/身份
        身份 = 数据.get("身份") or 数据.get("identity") or 数据.get("role")
        数据["身份"] = 身份
        成功, 消息, token = 注册(数据)
        if not 成功:
            return 失败响应(msg=消息, code=1, status=400)
        return 成功响应({"token": token}, msg=消息)


@认证命名空间.route("/login")
class 登录接口(Resource):
    @认证命名空间.expect(登录请求模型, validate=False)
    @认证命名空间.response(200, "登录成功，返回 JWT 令牌", 令牌响应模型)
    @认证命名空间.response(400, "账号或密码错误")
    def post(self):
        """用户登录（支持单点登录：新登录使旧会话失效）"""
        数据 = request.get_json(silent=True) or {}
        身份 = 数据.get("身份") or 数据.get("identity") or _兜底身份(数据)
        编号 = 数据.get("编号") or 数据.get("account") or 数据.get("teacher_id") or 数据.get("student_id")
        密码 = 数据.get("password")
        成功, 消息, token = 登录(身份, 编号, 密码)
        if not 成功:
            return 失败响应(msg=消息, code=1, status=400)
        return 成功响应({"token": token}, msg=消息)


@认证命名空间.route("/me")
class 当前用户接口(Resource):
    @认证命名空间.doc(security="Bearer")
    @需要登录
    def get(self):
        """获取当前登录用户信息"""
        用户 = g.当前用户
        信息 = 获取用户信息(用户["id"], 用户["身份"])
        if 信息 is None:
            return 失败响应(msg="用户不存在", code=404, status=404)
        信息["token_user"] = 用户
        return 成功响应(信息)


def _兜底身份(数据):
    """前端可能用 teacher/student 字段标识身份。"""
    if 数据.get("teacher_id"):
        return "teacher"
    if 数据.get("student_id"):
        return "student"
    return 数据.get("role")
