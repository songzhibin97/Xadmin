from django.urls import reverse


# 反向解析获取查看列表的url
def get_list_url(self):
    try:
        app_name = self.model._meta.app_label
        model_name = self.model._meta.model_name
    except Exception as e:
        app_name = self.model_config.model._meta.app_label
        model_name = self.model_config.model._meta.model_name
    _url = reverse('{}_{}'.format(app_name, model_name))
    return _url


# 反向解析获取增加列表的url
def get_add_url(self):
    try:
        app_name = self.model._meta.app_label
        model_name = self.model._meta.model_name
    except Exception as e:
        app_name = self.model_config.model._meta.app_label
        model_name = self.model_config.model._meta.model_name
    _url = reverse('{}_{}_add'.format(app_name, model_name))
    return _url


# 反向解析获取修改列表的url 需要传入obj.pk对象的主键值作为参数 来确定修改列表内容
def get_change_url(self, obj):
    try:
        app_name = self.model._meta.app_label
        model_name = self.model._meta.model_name
    except Exception as e:
        app_name = self.model_config.model._meta.app_label
        model_name = self.model_config.model._meta.model_name
    _url = reverse('{}_{}_change'.format(app_name, model_name), args=(obj.pk,))
    return _url


# 反向解析获取删除列表的url 需要传入obj.pk对象的主键值作为参数 来确定修改列表内容
def get_delete_url(self, obj):
    try:
        app_name = self.model._meta.app_label
        model_name = self.model._meta.model_name
    except Exception as e:
        app_name = self.model_config.model._meta.app_label
        model_name = self.model_config.model._meta.model_name
    _url = reverse('{}_{}_delete'.format(app_name, model_name), args=(obj.pk,))
    return _url
