# -*- coding: utf-8 -*-
from 数据库 import 执行单条查询, 执行并获取自增ID, 执行更新
from 工具 import 身份表, 哈希密码, 校验密码, 签发令牌, 生成会话令牌


def 校验注册数据(数据):
    身份 = 数据.get("身份")
    if 身份 not in ("teacher", "student"):
        return False, "身份必须为 teacher 或 student"
    编号字段 = 身份表[身份][1]
    编号 = (数据.get(编号字段) or "").strip()
    if not 编号:
        return False, f"{('工号' if 身份 == 'teacher' else '学号')}不能为空"
    密码 = 数据.get("password") or ""
    if len(密码) < 6:
        return False, "密码长度至少 6 位"
    姓名 = (数据.get("name") or "").strip()
    if not 姓名:
        return False, "姓名不能为空"
    return True, ""


def 检查重复(身份, 编号):
    """检查工号/学号是否已存在。"""
    表名, 编号字段, _ = 身份表[身份]
    sql = f"SELECT id FROM {表名} WHERE {编号字段}=%s LIMIT 1"
    return 执行单条查询(sql, (编号,)) is not None


def 注册(数据):
    通过, 消息 = 校验注册数据(数据)
    if not 通过:
        return False, 消息, None
    身份 = 数据["身份"]
    表名, 编号字段, 附加字段 = 身份表[身份]
    编号 = 数据[编号字段].strip()
    if 检查重复(身份, 编号):
        return False, "该工号/学号已注册", None
    哈希 = 哈希密码(数据["password"])
    列名 = [编号字段, "password_hash", "name"]
    占位 = ["%s"] * 3
    值 = [编号, 哈希, 数据["name"].strip()]
    附加值 = (数据.get(附加字段) or "").strip()
    if 附加值:
        列名.append(附加字段)
        占位.append("%s")
        值.append(附加值)
    phone = (数据.get("phone") or "").strip()
    if phone:
        列名.append("phone")
        占位.append("%s")
        值.append(phone)
    sql = f"INSERT INTO {表名} ({','.join(列名)}) VALUES ({','.join(占位)})"
    新ID = 执行并获取自增ID(sql, tuple(值))
    会话令牌 = 生成会话令牌()
    执行更新(f"UPDATE {表名} SET session_token=%s WHERE id=%s", (会话令牌, 新ID))
    token = 签发令牌(新ID, 身份, 编号, 数据["name"].strip(), 会话令牌)
    return True, "注册成功", token


def 登录(身份, 编号, 密码):
    if 身份 not in ("teacher", "student"):
        return False, "身份参数错误", None
    if not 编号 or not 密码:
        return False, "工号/学号与密码不能为空", None
    表名, 编号字段, _ = 身份表[身份]
    sql = f"SELECT id, {编号字段} AS 编号, password_hash, name FROM {表名} WHERE {编号字段}=%s LIMIT 1"
    用户 = 执行单条查询(sql, (编号,))
    if 用户 is None:
        return False, "账号不存在", None
    if not 校验密码(密码, 用户["password_hash"]):
        return False, "密码错误", None
    会话令牌 = 生成会话令牌()
    执行更新(f"UPDATE {表名} SET session_token=%s WHERE id=%s", (会话令牌, 用户["id"]))
    token = 签发令牌(用户["id"], 身份, 用户["编号"], 用户["name"], 会话令牌)
    return True, "登录成功", token


def 获取用户信息(用户ID, 身份):
    if 身份 not in ("teacher", "student"):
        return None
    表名, 编号字段, 附加字段 = 身份表[身份]
    sql = (
        f"SELECT id, {编号字段} AS 编号, name, phone, {附加字段} AS 附加, created_at "
        f"FROM {表名} WHERE id=%s LIMIT 1"
    )
    行 = 执行单条查询(sql, (用户ID,))
    if 行 is None:
        return None
    附加键 = "department" if 身份 == "teacher" else "class_name"
    return {
        "id": 行["id"],
        "身份": 身份,
        "编号": 行["编号"],
        "name": 行["name"],
        "phone": 行.get("phone"),
        附加键: 行.get("附加"),
        "created_at": 行["created_at"].strftime("%Y-%m-%d %H:%M:%S") if 行.get("created_at") else None,
    }
