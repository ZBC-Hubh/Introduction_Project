# -*- coding: utf-8 -*-
"""上传模块路由：图片上传（flask-restx Namespace + Swagger 文档）"""
from flask import request
from flask_restx import Namespace, Resource

from 工具 import 成功响应, 失败响应, 需要登录
from 业务.上传服务 import 保存文件


上传命名空间 = Namespace("upload", description="上传接口：物品图片上传")


@上传命名空间.route("/upload")
class 图片上传接口(Resource):
    @上传命名空间.doc(
        security="Bearer",
        consumes=["multipart/form-data"],
        params={
            "file": {
                "description": "图片文件，支持 png/jpg/jpeg/gif/webp，最大 10MB",
                "in": "formData",
                "type": "file",
                "required": True,
            }
        },
    )
    @上传命名空间.response(200, "上传成功，返回图片访问地址")
    @上传命名空间.response(400, "未上传文件或文件类型不允许")
    @上传命名空间.response(401, "未登录")
    @需要登录
    def post(self):
        """上传图片文件"""
        if "file" not in request.files:
            return 失败响应(msg="未上传文件", code=1, status=400)
        f = request.files["file"]
        try:
            url = 保存文件(f)
        except ValueError as e:
            return 失败响应(msg=str(e), code=1, status=400)
        return 成功响应({"url": url}, msg="上传成功")
