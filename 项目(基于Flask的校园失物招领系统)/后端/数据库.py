# -*- coding: utf-8 -*-
"""
数据库连接模块
基于 PyMySQL + DBUtils 提供连接池与上下文管理，
业务代码使用 with 获取游标即可，自动提交/回滚与归还连接。
"""
import pymysql
from pymysql.cursors import DictCursor
from dbutils.pooled_db import PooledDB

from 配置 import DB_CONFIG


# 创建连接池：maxshared 控制最大共享连接数，便于并发请求
_pool = PooledDB(
    creator=pymysql,
    maxconnections=10,
    mincached=2,
    maxcached=5,
    maxshared=3,
    blocking=True,
    maxusage=None,
    setsession=[],
    ping=1,  # 连接空闲时自动 ping 检查
    **{
        "host": DB_CONFIG["host"],
        "port": DB_CONFIG["port"],
        "user": DB_CONFIG["user"],
        "password": DB_CONFIG["password"],
        "database": DB_CONFIG["database"],
        "charset": DB_CONFIG["charset"],
        "cursorclass": DictCursor,
    }
)


class 数据库连接:
    """上下文管理器：获取游标并自动提交或回滚。"""

    def __init__(self, autocommit=True):
        self._conn = _pool.connection()
        self._cur = None
        self._autocommit = autocommit

    def __enter__(self):
        self._cur = self._conn.cursor()
        return self._cur

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                self._conn.rollback()
            elif self._autocommit:
                self._conn.commit()
        finally:
            if self._cur is not None:
                self._cur.close()
            self._conn.close()
        return False  # 不吞掉异常


def 执行查询(sql, args=None):
    """执行查询并返回所有行（字典列表）。"""
    with 数据库连接() as cur:
        cur.execute(sql, args)
        return cur.fetchall()


def 执行单条查询(sql, args=None):
    """执行查询并返回单行（字典）。"""
    with 数据库连接() as cur:
        cur.execute(sql, args)
        return cur.fetchone()


def 执行更新(sql, args=None):
    """执行 INSERT/UPDATE/DELETE，返回受影响行数。"""
    with 数据库连接() as cur:
        rows = cur.execute(sql, args)
        return rows


def 执行并获取自增ID(sql, args=None):
    """执行 INSERT 并返回自增主键 ID。"""
    with 数据库连接() as cur:
        cur.execute(sql, args)
        return cur.lastrowid


def 测试连接():
    """连接测试，返回服务器版本字符串。"""
    try:
        row = 执行单条查询("SELECT VERSION() AS v")
        return row.get("v") if row else None
    except Exception as e:
        return f"连接失败: {e}"
