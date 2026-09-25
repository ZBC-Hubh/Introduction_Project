# -*- coding: utf-8 -*-
from 数据库 import 执行查询, 执行单条查询, 执行并获取自增ID, 执行更新
from 工具 import 身份表, 身份中文, 编码转身份


分类映射 = {0: "电子设备", 1: "证件卡类", 2: "书籍文具", 3: "生活用品", 4: "其他"}
类型映射 = {0: "丢失", 1: "捡到"}
审核状态 = {0: "待审核", 1: "已通过", 2: "已拒绝"}
物品状态 = {0: "待处理", 1: "已找回"}


def _查询发布者(用户类型, 用户ID):
    """根据 user_type + user_id 回查老师/学生基本信息。"""
    if 用户类型 not in (0, 1):
        return None
    身份 = 编码转身份[用户类型]
    表名, 编号字段, 附加 = 身份表[身份]
    sql = f"SELECT id, {编号字段} AS code, name, {附加} AS extra FROM {表名} WHERE id=%s LIMIT 1"
    行 = 执行单条查询(sql, (用户ID,))
    if 行 is None:
        return None
    return {
        "id": 行["id"],
        "type": "teacher" if 用户类型 == 1 else "student",
        "code": 行["code"],
        "name": 行["name"],
        "extra": 行.get("extra"),
        "label": ("老师" if 用户类型 == 1 else "学生"),
    }


def _格式化物品(行, 带发布者=True):
    if 行 is None:
        return None
    # 兼容旧表结构：audit_feedback 列可能不存在
    反馈 = 行.get("audit_feedback", "") if isinstance(行, dict) and "audit_feedback" in 行 else ""
    d = {
        "id": 行["id"],
        "type": 行["type"],
        "type_label": 类型映射.get(行["type"], "未知"),
        "category": 行["category"],
        "category_label": 分类映射.get(行["category"], "其他"),
        "title": 行["title"],
        "description": 行["description"],
        "location": 行["location"],
        "image_url": 行["image_url"],
        "status": 行["status"],
        "status_label": 物品状态.get(行["status"], ""),
        "found_at": 行.get("found_at").strftime("%Y-%m-%d %H:%M:%S") if 行.get("found_at") else None,
        "audit_status": 行["audit_status"],
        "audit_status_label": 审核状态.get(行["audit_status"], ""),
        "audit_feedback": 反馈,
        "user_id": 行["user_id"],
        "user_type": 行["user_type"],
        "user_label": 身份中文.get(编码转身份.get(行["user_type"], ""), ""),
        "created_at": 行["created_at"].strftime("%Y-%m-%d %H:%M:%S") if 行["created_at"] else None,
    }
    if 带发布者:
        d["publisher"] = _查询发布者(行["user_type"], 行["user_id"])
    return d


def 发布物品(用户ID, 用户身份, 数据):
    """发布物品，返回自增 ID。"""
    类型 = int(数据.get("type", 0))
    分类 = int(数据.get("category", 4))
    标题 = (数据.get("title") or "").strip()
    描述 = (数据.get("description") or "").strip()
    地点 = (数据.get("location") or "").strip()
    图片 = (数据.get("image_url") or "").strip()

    if not 标题:
        raise ValueError("标题不能为空")
    if 类型 not in (0, 1):
        raise ValueError("类型必须为 0 丢失或 1 捡到")
    if 分类 not in 分类映射:
        raise ValueError("分类无效")

    编码类型 = 0 if 用户身份 == "student" else 1
    sql = """
        INSERT INTO items (user_id, user_type, type, category, title, description, location, image_url)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """
    return 执行并获取自增ID(sql, (用户ID, 编码类型, 类型, 分类, 标题, 描述, 地点, 图片))


def 列表查询(type=None, category=None, keyword=None, audit_status=1, page=1, size=12, 仅审核通过=True):
    """物品列表查询（失物大厅/首页）。audit_status 为 None 时不过滤（后台待审用）。
    已找回的物品在 found_at 3天后自动从大厅消失。"""
    where, args = [], []
    if type is not None:
        where.append("type=%s"); args.append(int(type))
    if category is not None:
        where.append("category=%s"); args.append(int(category))
    if keyword:
        where.append("(title LIKE %s OR description LIKE %s OR location LIKE %s)")
        kw = f"%{keyword}%"
        args.extend([kw, kw, kw])
    # 当 audit_status 不为 None 时始终添加过滤条件
    if audit_status is not None:
        where.append("audit_status=%s"); args.append(int(audit_status))
    # 已找回的物品在 found_at 3天后自动从大厅消失
    where.append("(status=0 OR (status=1 AND found_at >= NOW() - INTERVAL 3 DAY))")

    sql_count = "SELECT COUNT(*) AS c FROM items"
    sql = "SELECT * FROM items"
    if where:
        sql_count += " WHERE " + " AND ".join(where)
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    page = max(1, int(page)); size = max(1, int(size))
    args_q = list(args) + [size, (page - 1) * size]

    总行 = 执行单条查询(sql_count, tuple(args))
    总数 = 0 if 总行 is None else int(list(总行.values())[0])
    行列表 = 执行查询(sql, tuple(args_q))
    列表 = [_格式化物品(r, 带发布者=False) for r in 行列表]
    return {"total": 总数, "page": page, "size": size, "list": 列表,
            "categories": 分类映射, "types": 类型映射}


def 获取详情(id):
    r = 执行单条查询("SELECT * FROM items WHERE id=%s", (id,))
    return _格式化物品(r, 带发布者=True)


def 更新物品(id, 用户ID, 用户身份, 数据):
    编码类型 = 0 if 用户身份 == "student" else 1
    where = "id=%s AND user_id=%s AND user_type=%s"
    args = [id, 用户ID, 编码类型]
    fields, vals = [], []
    for k in ("title", "description", "location", "image_url"):
        if k in 数据:
            fields.append(f"{k}=%s")
            vals.append(数据[k])
    for k in ("type", "category"):
        if k in 数据 and 数据[k] is not None:
            fields.append(f"{k}=%s")
            vals.append(int(数据[k]))
    if not fields:
        return False
    sql = f"UPDATE items SET {','.join(fields)} WHERE {where}"
    return 执行更新(sql, tuple(vals + args)) > 0


def 标记找回(id, 用户ID, 用户身份, 允许老师=False):
    编码类型 = 0 if 用户身份 == "student" else 1
    if 允许老师 and 用户身份 == "teacher":
        # 老师可直接标记任意物品
        sql = "UPDATE items SET status=1, found_at=NOW() WHERE id=%s"
        return 执行更新(sql, (id,)) > 0
    sql = "UPDATE items SET status=1, found_at=NOW() WHERE id=%s AND user_id=%s AND user_type=%s"
    return 执行更新(sql, (id, 用户ID, 编码类型)) > 0


def 删除物品(id, 用户ID, 用户身份, 允许老师=False):
    编码类型 = 0 if 用户身份 == "student" else 1
    if 允许老师 and 用户身份 == "teacher":
        sql = "DELETE FROM items WHERE id=%s"
        return 执行更新(sql, (id,)) > 0
    sql = "DELETE FROM items WHERE id=%s AND user_id=%s AND user_type=%s"
    return 执行更新(sql, (id, 用户ID, 编码类型)) > 0


def 我的发布(用户ID, 用户身份):
    编码类型 = 0 if 用户身份 == "student" else 1
    sql = "SELECT * FROM items WHERE user_id=%s AND user_type=%s ORDER BY created_at DESC"
    rows = 执行查询(sql, (用户ID, 编码类型))
    return [_格式化物品(r, 带发布者=False) for r in rows]


def 申请认领(id, 用户ID, 用户身份, 原因=""):
    编码类型 = 0 if 用户身份 == "student" else 1
    # 同一用户不重复申请同一物品
    exist = 执行单条查询(
        "SELECT id FROM claims WHERE item_id=%s AND user_id=%s AND user_type=%s LIMIT 1",
        (id, 用户ID, 编码类型)
    )
    if exist is not None:
        raise ValueError("您已经提交过认领申请")
    sql = "INSERT INTO claims (item_id, user_id, user_type, reason) VALUES (%s,%s,%s,%s)"
    return 执行并获取自增ID(sql, (id, 用户ID, 编码类型, 原因))
