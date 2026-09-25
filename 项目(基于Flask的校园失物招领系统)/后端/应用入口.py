# -*- coding: utf-8 -*-
import os
import sys

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_restx import Api

from 配置 import FRONTEND_DIR, UPLOAD_DIR, HOST, PORT, DEBUG, MAX_CONTENT_LENGTH


def _自动迁移数据库():
    """启动时检查并添加缺失的数据库列。"""
    try:
        from 数据库 import 执行更新, 执行单条查询
        # 检查 items 表是否有 audit_feedback 列
        行 = 执行单条查询(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'items' AND COLUMN_NAME = 'audit_feedback'"
        )
        if not 行:
            执行更新(
                "ALTER TABLE items ADD COLUMN audit_feedback VARCHAR(500) NULL "
                "COMMENT '审核反馈(拒绝原因)' AFTER audit_status"
            )
            print("🔧 自动迁移：已添加 audit_feedback 列到 items 表")

        # 检查 teachers 表是否有 session_token 列（单点登录）
        行 = 执行单条查询(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'teachers' AND COLUMN_NAME = 'session_token'"
        )
        if not 行:
            执行更新(
                "ALTER TABLE teachers ADD COLUMN session_token VARCHAR(128) NULL "
                "COMMENT '会话令牌(单点登录)' AFTER password_hash"
            )
            print("🔧 自动迁移：已添加 session_token 列到 teachers 表")

        # 检查 students 表是否有 session_token 列
        行 = 执行单条查询(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'students' AND COLUMN_NAME = 'session_token'"
        )
        if not 行:
            执行更新(
                "ALTER TABLE students ADD COLUMN session_token VARCHAR(128) NULL "
                "COMMENT '会话令牌(单点登录)' AFTER password_hash"
            )
            print("🔧 自动迁移：已添加 session_token 列到 students 表")

        # 创建 messages 表（私聊消息）
        行 = 执行单条查询(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'messages'"
        )
        if not 行:
            执行更新("""
                CREATE TABLE messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    sender_id INT NOT NULL COMMENT '发送者ID',
                    sender_type TINYINT NOT NULL COMMENT '发送者类型 0=学生 1=老师',
                    receiver_id INT NOT NULL COMMENT '接收者ID',
                    receiver_type TINYINT NOT NULL COMMENT '接收者类型 0=学生 1=老师',
                    content VARCHAR(500) NOT NULL COMMENT '消息内容',
                    item_id INT NULL COMMENT '关联物品ID',
                    is_read TINYINT DEFAULT 0 COMMENT '是否已读 0=未读 1=已读',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_sender (sender_id, sender_type),
                    INDEX idx_receiver (receiver_id, receiver_type, is_read)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8
            """)
            print("🔧 自动迁移：已创建 messages 表")

        # 检查 items 表是否有 found_at 列（标记找回时间）
        行 = 执行单条查询(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'items' AND COLUMN_NAME = 'found_at'"
        )
        if not 行:
            执行更新(
                "ALTER TABLE items ADD COLUMN found_at DATETIME NULL "
                "COMMENT '标记找回时间' AFTER status"
            )
            print("[OK] 自动迁移：已添加 found_at 列到 items 表")
    except Exception as e:
        print(f"[WARN] 自动迁移数据库失败（可忽略）：{e}")


def 创建应用():
    # 启动时自动迁移数据库（添加缺失的列等）
    _自动迁移数据库()

    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
    # 关闭 Swagger 中的 X-Fields 调试参数
    app.config["RESTX_MASK_SWAGGER"] = False
    CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

    # ---------------- 静态资源路由 ----------------
    # 注意：必须先于 flask-restx 的 Api 创建之前注册。
    # flask-restx 会自动在 "/" 注册一个永远返回 404 的元数据端点（render_root），
    # werkzeug 对完全相同的路由规则按注册顺序匹配，先注册者生效，
    # 因此首页路由需先注册，否则 "/" 会被 flask-restx 抢占导致打不开失物大厅。
    @app.route("/")
    def 首页():
        return send_from_directory(FRONTEND_DIR, "失物大厅.html")

    # 通用 HTML 页面路由：/失物大厅.html 等直接读文件返回
    @app.route("/<path:page_file>")
    def 静态页面(page_file):
        if not page_file.endswith(".html"):
            return ("Not Found", 404)
        文件路径 = os.path.join(FRONTEND_DIR, page_file)
        if not os.path.exists(文件路径):
            return ("Not Found", 404)
        return send_from_directory(FRONTEND_DIR, page_file)

    # 静态子目录：样式、脚本、资源
    @app.route("/样式/<path:asset_file>")
    def 样式文件(asset_file):
        return send_from_directory(os.path.join(FRONTEND_DIR, "样式"), asset_file)

    @app.route("/脚本/<path:asset_file>")
    def 脚本文件(asset_file):
        return send_from_directory(os.path.join(FRONTEND_DIR, "脚本"), asset_file)

    @app.route("/资源/<path:asset_file>")
    def 资源文件(asset_file):
        return send_from_directory(os.path.join(FRONTEND_DIR, "资源"), asset_file)

    # 上传文件访问
    @app.route("/上传文件/<path:asset_file>")
    def 上传文件访问(asset_file):
        return send_from_directory(UPLOAD_DIR, asset_file)

    # 健康检查
    @app.get("/api/health")
    def 健康检查():
        from 数据库 import 测试连接
        return {"code": 0, "msg": "ok", "db": 测试连接()}

    # ---------------- Swagger 接口文档 ----------------
    # JWT Bearer 认证方案：点击右上角 Authorize，输入 "Bearer <token>" 即可调试需登录接口
    授权方案 = {
        "Bearer": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": 'JWT 令牌，格式："Bearer eyJhbGciOi..."（登录接口返回的 token）',
        }
    }
    接口文档 = Api(
        app,
        version="1.0",
        title="校园失物招领系统 API",
        description="基于 Flask + flask-restx 的校园失物招领系统接口文档。"
        "统一响应格式：{code, msg, data}，code=0 表示成功。",
        doc="/docs",
        authorizations=授权方案,
    )

    # 注册命名空间（每个模块一个 Namespace，路径与原蓝图保持一致）
    from 路由.认证 import 认证命名空间
    from 路由.物品 import 物品命名空间
    from 路由.留言 import 留言命名空间
    from 路由.上传 import 上传命名空间
    from 路由.管理 import 管理命名空间, 公告命名空间
    from 路由.消息 import 消息命名空间
    接口文档.add_namespace(认证命名空间, path="/api/auth")
    接口文档.add_namespace(物品命名空间, path="/api/items")
    接口文档.add_namespace(留言命名空间, path="/api/items")
    接口文档.add_namespace(上传命名空间, path="/api")
    接口文档.add_namespace(管理命名空间, path="/api/admin")
    接口文档.add_namespace(公告命名空间, path="/api")
    接口文档.add_namespace(消息命名空间, path="/api/messages")

    return app


应用 = 创建应用()


if __name__ == "__main__":
    # 确保从 后端 目录运行时仍能导入本目录模块
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    应用.run(host=HOST, port=PORT, debug=DEBUG)
