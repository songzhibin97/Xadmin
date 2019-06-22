from django.apps import AppConfig
# 引用Django 内置的全局扫描方法
from django.utils.module_loading import autodiscover_modules


class XadminConfig(AppConfig):
    name = 'Xadmin'

    # ready方法在Django启动的时候(settings注册过APP的情况下)随启动而运行
    def ready(self):
        # APP启动时扫描全局 Xadmin.py 文件
        autodiscover_modules('Xadmin')
