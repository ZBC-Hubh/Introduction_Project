# -*- coding: utf-8 -*-
"""
上传文件业务服务
- 检查扩展名/大小
- 生成不冲突文件名
- 保存到配置.UPLOAD_DIR，返回可访问 URL
"""
import os
import time
import uuid

from werkzeug.utils import secure_filename

from 配置 import ALLOWED_EXTENSIONS, UPLOAD_DIR, ensure_dirs


ensure_dirs()


def 允许扩展名(文件名):
    return "." in 文件名 and 文件名.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def 保存文件(file_storage):
    """
    保存上传的图片文件。
    :param file_storage: werkzeug.FileStorage（request.files[name]）
    :return: 访问 URL 字符串，如 /上传文件/xxxx.jpg
    """
    if not file_storage or not file_storage.filename:
        raise ValueError("未选择文件")
    if not 允许扩展名(file_storage.filename):
        raise ValueError("只允许 png/jpg/jpeg/gif/webp 图片")

    安全名 = secure_filename(file_storage.filename)
    if not 安全名:
        安全名 = "img"
    ext = 安全名.rsplit(".", 1)[1].lower() if "." in 安全名 else "jpg"
    新名 = f"{int(time.time())}_{uuid.uuid4().hex[:8]}.{ext}"
    完整路径 = os.path.join(UPLOAD_DIR, 新名)
    file_storage.save(完整路径)
    return f"/上传文件/{新名}"
