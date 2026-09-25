# -*- coding: utf-8 -*-
"""
留言业务服务
"""
from 数据库 import 执行查询, 执行并获取自增ID
from 工具 import 身份表


def 留言列表(物品ID):
    sql = "SELECT * FROM messages WHERE item_id=%s ORDER BY created_at ASC"
    rows = 执行查询(sql, (物品ID,))
    结果 = []
    for r in rows:
        身份 = "teacher" if r["user_type"] == 1 else "student"
        表名, 编号字段, _ = 身份表[身份]
        user = _查询用户(表名, 编号字段, r["user_id"])
        结果.append({
            "id": r["id"],
            "item_id": r["item_id"],
            "user_type": r["user_type"],
            "user_id": r["user_id"],
            "name": user["name"] if user else f"{身份}",
            "code": user["code"] if user else "-",
            "content": r["content"],
            "created_at": r["created_at"].strftime("%Y-%m-%d %H:%M:%S") if r["created_at"] else None,
        })
    return 结果


def _查询用户(表名, 编号字段, id):
    from 数据库 import 执行单条查询
    return 执行单条查询(f"SELECT id, {编号字段} AS code, name FROM {表名} WHERE id=%s LIMIT 1", (id,))


def 发布留言(物品ID, 用户ID, 用户身份, 内容):
    if not 内容 or not 内容.strip():
        raise ValueError("留言内容不能为空")
    编码类型 = 0 if 用户身份 == "student" else 1
    sql = "INSERT INTO messages (item_id, user_id, user_type, content) VALUES (%s,%s,%s,%s)"
    return 执行并获取自增ID(sql, (物品ID, 用户ID, 编码类型, 内容.strip()))
