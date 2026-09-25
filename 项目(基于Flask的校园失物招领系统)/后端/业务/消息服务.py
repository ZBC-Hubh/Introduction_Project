# -*- coding: utf-8 -*-
from 数据库 import 执行查询, 执行单条查询, 执行并获取自增ID, 执行更新
from 工具 import 身份表


def 发送消息(发送者ID, 发送者身份, 接收者ID, 接收者身份, 内容, 物品ID=None):
    if not 内容 or not 内容.strip():
        raise ValueError("消息内容不能为空")
    内容 = 内容.strip()
    if len(内容) > 500:
        raise ValueError("消息内容过长")

    发送者编码 = 1 if 发送者身份 == "teacher" else 0
    接收者编码 = 1 if 接收者身份 == "teacher" else 0

    sql = """INSERT INTO messages 
        (sender_id, sender_type, receiver_id, receiver_type, content, item_id)
        VALUES (%s, %s, %s, %s, %s, %s)"""
    return 执行并获取自增ID(sql, (
        发送者ID, 发送者编码, 接收者ID, 接收者编码, 内容, 物品ID
    ))


def 获取会话(用户ID, 用户身份, 对方ID, 对方身份, limit=50):
    """获取与某个用户的会话记录。"""
    用户编码 = 1 if 用户身份 == "teacher" else 0
    对方编码 = 1 if 对方身份 == "teacher" else 0

    sql = """SELECT * FROM messages 
        WHERE (sender_id=%s AND sender_type=%s AND receiver_id=%s AND receiver_type=%s)
           OR (sender_id=%s AND sender_type=%s AND receiver_id=%s AND receiver_type=%s)
        ORDER BY created_at DESC LIMIT %s"""
    行列表 = 执行查询(sql, (
        用户ID, 用户编码, 对方ID, 对方编码,
        对方ID, 对方编码, 用户ID, 用户编码,
        limit
    ))
    # 按时间正序排列
    行列表.reverse()

    结果 = []
    for 行 in 行列表:
        结果.append({
            "id": 行["id"],
            "content": 行["content"],
            "sender_id": 行["sender_id"],
            "sender_type": "teacher" if 行["sender_type"] == 1 else "student",
            "receiver_id": 行["receiver_id"],
            "receiver_type": "teacher" if 行["receiver_type"] == 1 else "student",
            "item_id": 行.get("item_id"),
            "created_at": 行["created_at"].strftime("%Y-%m-%d %H:%M:%S") if 行["created_at"] else None,
            "is_self": 行["sender_id"] == 用户ID and 行["sender_type"] == 用户编码,
        })
    return 结果


def 获取会话列表(用户ID, 用户身份):
    """获取当前用户的所有会话列表。"""
    用户编码 = 1 if 用户身份 == "teacher" else 0

    # 找出所有与当前用户有过消息往来的对方
    sql = """
        SELECT 
            CASE 
                WHEN sender_id=%s AND sender_type=%s THEN receiver_id
                ELSE sender_id
            END AS other_id,
            CASE 
                WHEN sender_id=%s AND sender_type=%s THEN receiver_type
                ELSE sender_type
            END AS other_type,
            MAX(created_at) AS last_time,
            (SELECT COUNT(*) FROM messages m2 
                WHERE (m2.sender_id=%s AND m2.receiver_id=CASE 
                    WHEN m1.sender_id=%s THEN m1.receiver_id ELSE m1.sender_id END)
                   OR (m2.receiver_id=%s AND m2.sender_id=CASE 
                    WHEN m1.sender_id=%s THEN m1.receiver_id ELSE m1.sender_id END)
            ) AS unread_count
        FROM messages m1
        WHERE (sender_id=%s AND sender_type=%s)
           OR (receiver_id=%s AND receiver_type=%s)
        GROUP BY other_id, other_type
        ORDER BY last_time DESC
    """
    行列表 = 执行查询(sql, (
        用户ID, 用户编码,
        用户ID, 用户编码,
        用户ID, 用户ID,
        用户ID,
        用户ID, 用户编码,
        用户ID, 用户编码
    ))

    # 补充对方用户信息
    结果 = []
    for 行 in 行列表:
        对方编码 = 行["other_type"]
        对方ID = 行["other_id"]
        对方身份 = "teacher" if 对方编码 == 1 else "student"

        # 查对方名字
        表名, 编号字段, _ = 身份表[对方身份]
        用户行 = 执行单条查询(
            f"SELECT id, {编号字段} AS code, name FROM {表名} WHERE id=%s LIMIT 1",
            (对方ID,)
        )
        对方名称 = 用户行["name"] if 用户行 else "未知用户"
        对方编号 = 用户行["code"] if 用户行 else ""

        # 计算未读数
        未读 = 执行单条查询(
            "SELECT COUNT(*) AS c FROM messages WHERE receiver_id=%s AND receiver_type=%s AND sender_id=%s AND sender_type=%s AND is_read=0",
            (用户ID, 用户编码, 对方ID, 对方编码)
        )
        未读数 = 未读["c"] if 未读 else 0

        结果.append({
            "other_id": 对方ID,
            "other_type": 对方身份,
            "other_name": 对方名称,
            "other_code": 对方编号,
            "last_time": 行["last_time"].strftime("%Y-%m-%d %H:%M:%S") if 行["last_time"] else None,
            "unread_count": 未读数,
        })
    return 结果


def 标记已读(用户ID, 用户身份, 对方ID, 对方身份):
    """将与某用户的消息标记为已读。"""
    用户编码 = 1 if 用户身份 == "teacher" else 0
    对方编码 = 1 if 对方身份 == "teacher" else 0
    sql = """UPDATE messages SET is_read=1 
        WHERE sender_id=%s AND sender_type=%s AND receiver_id=%s AND receiver_type=%s AND is_read=0"""
    return 执行更新(sql, (对方ID, 对方编码, 用户ID, 用户编码))


def 获取未读数(用户ID, 用户身份):
    """获取当前用户的未读消息总数。"""
    用户编码 = 1 if 用户身份 == "teacher" else 0
    行 = 执行单条查询(
        "SELECT COUNT(*) AS c FROM messages WHERE receiver_id=%s AND receiver_type=%s AND is_read=0",
        (用户ID, 用户编码)
    )
    return 行["c"] if 行 else 0
