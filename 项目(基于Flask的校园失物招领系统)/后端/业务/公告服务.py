# -*- coding: utf-8 -*-
"""
公告业务服务
首页公告栏：老师可发布；所有人可读
"""
from 数据库 import 执行查询, 执行单条查询, 执行并获取自增ID


def 公告列表(limit=6):
    sql = "SELECT id, title, content, publisher, created_at FROM announcements ORDER BY created_at DESC LIMIT %s"
    行列表 = 执行查询(sql, (limit,))
    return [
        {
            "id": r["id"],
            "title": r["title"],
            "content": r["content"],
            "publisher": r["publisher"],
            "created_at": r["created_at"].strftime("%Y-%m-%d %H:%M:%S") if r["created_at"] else None,
        }
        for r in 行列表
    ]


def 发布公告(标题, 内容, 发布者姓名):
    if not 标题 or not 内容:
        raise ValueError("标题与内容不能为空")
    sql = "INSERT INTO announcements (title, content, publisher) VALUES (%s,%s,%s)"
    return 执行并获取自增ID(sql, (标题.strip(), 内容.strip(), 发布者姓名))


def 公告详情(id):
    return 执行单条查询(
        "SELECT id, title, content, publisher, created_at FROM announcements WHERE id=%s", (id,)
    )
