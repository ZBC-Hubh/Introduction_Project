# -*- coding: utf-8 -*-
from 数据库 import 执行查询, 执行单条查询, 执行更新
from 业务.物品服务 import 列表查询


def 审核物品(id, 通过=True, 反馈=""):
    if 通过:
        sql = "UPDATE items SET audit_status=1 WHERE id=%s AND audit_status=0"
        return 执行更新(sql, (id,)) > 0
    else:
        # 拒绝：直接删除该物品
        sql = "DELETE FROM items WHERE id=%s AND audit_status=0"
        return 执行更新(sql, (id,)) > 0


def 批量审核(ids, 通过=True, 反馈=""):
    """批量通过/拒绝审核。拒绝时直接删除物品。"""
    if not ids:
        return False
    id列表 = [int(i) for i in ids]
    # pymysql 对 IN 子句列表参数使用 IN %s（不加括号），自动展开
    if 通过:
        sql = "UPDATE items SET audit_status=1 WHERE id IN %s AND audit_status=0"
        执行更新(sql, (id列表,))
    else:
        # 拒绝：直接删除这些物品
        sql = "DELETE FROM items WHERE id IN %s AND audit_status=0"
        执行更新(sql, (id列表,))
    return True


def 待审核列表(page=1, size=20):
    return 列表查询(audit_status=0, page=page, size=size, 仅审核通过=False)


def 统计看板():
    # 总物品、丢失数、捡到数、找回数
    总数 = 执行单条查询("SELECT COUNT(*) AS c FROM items")["c"]
    丢失 = 执行单条查询("SELECT COUNT(*) AS c FROM items WHERE type=0")["c"]
    捡到 = 执行单条查询("SELECT COUNT(*) AS c FROM items WHERE type=1")["c"]
    找回 = 执行单条查询("SELECT COUNT(*) AS c FROM items WHERE status=1")["c"]
    待审 = 执行单条查询("SELECT COUNT(*) AS c FROM items WHERE audit_status=0")["c"]
    找回率 = round(找回 * 100.0 / 总数, 2) if 总数 else 0.0

    # 分类分布
    分类行 = 执行查询("SELECT category, COUNT(*) AS c FROM items GROUP BY category ORDER BY c DESC")
    分类映射 = {0: "电子设备", 1: "证件卡类", 2: "书籍文具", 3: "生活用品", 4: "其他"}
    分类分布 = {int(r["category"]): r["c"] for r in 分类行}

    # 用户数
    学生数 = 执行单条查询("SELECT COUNT(*) AS c FROM students")["c"]
    老师数 = 执行单条查询("SELECT COUNT(*) AS c FROM teachers")["c"]

    return {
        "total_items": 总数,
        "total_lost": 丢失,
        "total_found": 捡到,
        "total_recovered": 找回,
        "pending_audit": 待审,
        "recovery_rate": 找回率,
        "students": 学生数,
        "teachers": 老师数,
        "category_distribution": 分类分布,
    }


def 用户列表():
    学生 = 执行查询("SELECT id, student_id AS code, name, class_name AS extra, phone, created_at FROM students ORDER BY created_at DESC")
    老师 = 执行查询("SELECT id, teacher_id AS code, name, department AS extra, phone, created_at FROM teachers ORDER BY created_at DESC")

    def fmt(rows, 角色):
        结果 = []
        for r in rows:
            # 统计该用户发布的物品数量
            编码类型 = 1 if 角色 == "teacher" else 0
            cnt = 执行单条查询(
                "SELECT COUNT(*) AS c FROM items WHERE user_id=%s AND user_type=%s",
                (r["id"], 编码类型)
            )["c"]
            结果.append({
                "id": r["id"],
                "role": 角色,
                "code": r["code"],
                "name": r["name"],
                "phone": r.get("phone") or "",
                "items": cnt,
                "created_at": r["created_at"].strftime("%Y-%m-%d %H:%M:%S") if r["created_at"] else None,
            })
        return 结果

    return fmt(学生, "student") + fmt(老师, "teacher")
