# -*- coding: utf-8 -*-
import datetime
import functools
import secrets

import bcrypt
import jwt
from flask import request, jsonify, g

from 配置 import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_HOURS


def 成功响应(data=None, msg="操作成功"):
    return jsonify({"code": 0, "msg": msg, "data": data})


def 失败响应(msg="操作失败", code=1, status=400):
    # 注意：必须返回 (dict, 状态码) 而非 (jsonify响应, 状态码)。
    # flask-restx 会把元组中的 Response 对象当作待序列化数据导致 TypeError，
    # 而 (dict, status) 写法在 flask-restx 与原生 Flask 中行为一致。
    return {"code": code, "msg": msg, "data": None}, status


def 哈希密码(明文):
    if isinstance(明文, str):
        明文 = 明文.encode("utf-8")
    return bcrypt.hashpw(明文, bcrypt.gensalt(rounds=10)).decode("utf-8")


def 校验密码(明文, 哈希值):
    if isinstance(明文, str):
        明文 = 明文.encode("utf-8")
    if isinstance(哈希值, str):
        哈希值 = 哈希值.encode("utf-8")
    try:
        return bcrypt.checkpw(明文, 哈希值)
    except (ValueError, TypeError):
        return False


def 生成会话令牌():
    return secrets.token_hex(32)


def 签发令牌(用户ID, 用户身份, 用户编号, 姓名, 会话令牌=None):
    payload = {
        "sub": 用户ID,
        "身份": 用户身份,
        "编号": 用户编号,
        "姓名": 姓名,
        "session": 会话令牌 or "",
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def 解析令牌(令牌):
    return jwt.decode(令牌, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def 验证会话(用户ID, 用户身份, 会话令牌):
    """单点登录：检查数据库中的 session_token 是否与 JWT 一致。"""
    if not 会话令牌:
        return False
    try:
        from 数据库 import 执行单条查询
        表名 = "teachers" if 用户身份 == "teacher" else "students"
        行 = 执行单条查询(
            f"SELECT session_token FROM {表名} WHERE id=%s LIMIT 1",
            (用户ID,)
        )
        if 行 is None:
            return False
        return 行.get("session_token") == 会话令牌
    except Exception:
        return False


def 从请求获取用户():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    令牌 = auth[7:].strip()
    try:
        payload = 解析令牌(令牌)
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    用户ID = int(payload.get("sub"))
    用户身份 = payload.get("身份")
    会话令牌 = payload.get("session", "")
    if not 验证会话(用户ID, 用户身份, 会话令牌):
        return None
    return {
        "id": 用户ID,
        "身份": 用户身份,
        "编号": payload.get("编号"),
        "姓名": payload.get("姓名"),
    }


def 需要登录(视图函数):
    @functools.wraps(视图函数)
    def 包装(*args, **kwargs):
        用户 = 从请求获取用户()
        if 用户 is None:
            return 失败响应("请先登录", code=401, status=401)
        g.当前用户 = 用户
        return 视图函数(*args, **kwargs)
    return 包装


def 需要老师权限(视图函数):
    @functools.wraps(视图函数)
    def 包装(*args, **kwargs):
        用户 = 从请求获取用户()
        if 用户 is None:
            return 失败响应("请先登录", code=401, status=401)
        if 用户.get("身份") != "teacher":
            return 失败响应("权限不足，仅老师可访问后台管理", code=403, status=403)
        g.当前用户 = 用户
        return 视图函数(*args, **kwargs)
    return 包装


# ---------------- 表名映射 ----------------

身份表 = {
    "teacher": ("teachers", "teacher_id", "department"),
    "student": ("students", "student_id", "class_name"),
}

身份中文 = {"teacher": "老师", "student": "学生"}
身份编码 = {"teacher": 1, "student": 0}
编码转身份 = {0: "student", 1: "teacher"}
