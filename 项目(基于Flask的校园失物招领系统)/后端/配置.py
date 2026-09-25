# -*- coding: utf-8 -*-
"""
配置模块
集中管理数据库连接、JWT 密钥、文件上传路径等配置项。
"""
import os

# 项目根目录（后端目录的上一级，便于定位前端静态资源）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 后端目录
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
# 前端静态资源目录
FRONTEND_DIR = os.path.join(BASE_DIR, "前端")
# 上传文件存储目录
UPLOAD_DIR = os.path.join(BACKEND_DIR, "上传文件")


# MySQL 数据库连接配置
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "bishe",
    "charset": "utf8mb4",
    "cursorclass": None,  # 在数据库.py 中动态指定 DictCursor
}

# JWT 配置
JWT_SECRET = "campus-lost-found-2024-secure-key-change-me"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

# 上传文件配置
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB

# 应用运行配置
HOST = "0.0.0.0"
PORT = 5000
DEBUG = True


def ensure_dirs():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


# 启动时确保上传目录存在
ensure_dirs()
