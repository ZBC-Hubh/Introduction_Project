# -*- coding: utf-8 -*-
"""
数据库初始化脚本
创建校园失物招领系统所需的所有表结构
"""
import pymysql
from 配置 import DB_CONFIG


def 创建数据库():
    """创建数据库（如果不存在）"""
    conn = pymysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )
    cur = conn.cursor()
    cur.execute(
        f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    conn.commit()
    conn.close()
    print(f"[OK] 数据库 {DB_CONFIG['database']} 已就绪")


def 初始化表():
    """创建所有表"""
    conn = pymysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        charset=DB_CONFIG["charset"],
    )
    cur = conn.cursor()

    # 1. 老师表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            teacher_id VARCHAR(50) NOT NULL COMMENT '工号',
            password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
            name VARCHAR(50) NOT NULL COMMENT '姓名',
            department VARCHAR(100) DEFAULT '' COMMENT '院系',
            phone VARCHAR(20) DEFAULT '' COMMENT '电话',
            session_token VARCHAR(128) NULL COMMENT '会话令牌(单点登录)',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_teacher_id (teacher_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='老师表'
    """)
    print("[OK] 表 teachers 已就绪")

    # 2. 学生表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id VARCHAR(50) NOT NULL COMMENT '学号',
            password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
            name VARCHAR(50) NOT NULL COMMENT '姓名',
            class_name VARCHAR(100) DEFAULT '' COMMENT '班级',
            phone VARCHAR(20) DEFAULT '' COMMENT '电话',
            session_token VARCHAR(128) NULL COMMENT '会话令牌(单点登录)',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_student_id (student_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生表'
    """)
    print("[OK] 表 students 已就绪")

    # 3. 物品表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL COMMENT '发布者ID',
            user_type TINYINT NOT NULL COMMENT '发布者类型 0=学生 1=老师',
            type TINYINT NOT NULL COMMENT '类型 0=丢失 1=捡到',
            category TINYINT NOT NULL COMMENT '分类 0=电子设备 1=证件卡类 2=书籍文具 3=生活用品 4=其他',
            title VARCHAR(200) NOT NULL COMMENT '标题',
            description TEXT COMMENT '描述',
            location VARCHAR(200) DEFAULT '' COMMENT '地点',
            image_url VARCHAR(500) DEFAULT '' COMMENT '图片URL',
            status TINYINT DEFAULT 0 COMMENT '状态 0=待处理 1=已找回',
            found_at DATETIME NULL COMMENT '标记找回时间',
            audit_status TINYINT DEFAULT 0 COMMENT '审核状态 0=待审核 1=已通过 2=已拒绝',
            audit_feedback VARCHAR(500) NULL COMMENT '审核反馈(拒绝原因)',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user (user_id, user_type),
            INDEX idx_type_category (type, category),
            INDEX idx_audit (audit_status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='物品表'
    """)
    print("[OK] 表 items 已就绪")

    # 4. 认领表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            id INT AUTO_INCREMENT PRIMARY KEY,
            item_id INT NOT NULL COMMENT '物品ID',
            user_id INT NOT NULL COMMENT '认领者ID',
            user_type TINYINT NOT NULL COMMENT '认领者类型 0=学生 1=老师',
            reason VARCHAR(500) DEFAULT '' COMMENT '认领理由',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_item_user (item_id, user_id, user_type),
            INDEX idx_item (item_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='认领表'
    """)
    print("[OK] 表 claims 已就绪")

    # 5. 消息表（留言+私聊）
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sender_id INT NOT NULL COMMENT '发送者ID',
            sender_type TINYINT NOT NULL COMMENT '发送者类型 0=学生 1=老师',
            receiver_id INT NULL COMMENT '接收者ID（私聊时使用）',
            receiver_type TINYINT NULL COMMENT '接收者类型（私聊时使用）',
            item_id INT NULL COMMENT '关联物品ID（留言时使用）',
            content VARCHAR(500) NOT NULL COMMENT '消息内容',
            is_read TINYINT DEFAULT 0 COMMENT '是否已读 0=未读 1=已读',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_sender (sender_id, sender_type),
            INDEX idx_receiver (receiver_id, receiver_type, is_read),
            INDEX idx_item (item_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息表（留言+私聊）'
    """)
    print("[OK] 表 messages 已就绪")

    # 6. 公告表
    cur.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(200) NOT NULL COMMENT '公告标题',
            content TEXT NOT NULL COMMENT '公告内容',
            publisher VARCHAR(50) DEFAULT '' COMMENT '发布者姓名',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='公告表'
    """)
    print("[OK] 表 announcements 已就绪")

    conn.commit()
    conn.close()
    print("\n[OK] 所有表已初始化完成！")


if __name__ == "__main__":
    创建数据库()
    初始化表()
    print("\n🎉 数据库初始化完成！")
