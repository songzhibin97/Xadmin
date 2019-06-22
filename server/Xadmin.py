from django.conf.urls import url  # 使用Django内置url方法
from django.shortcuts import HttpResponse, render, redirect
from django.utils.safestring import mark_safe  # Django内置不转义方法
from Xadmin.server.function import select, edit, delete, Pagination  # 引入xadmin中function文件中定义好的操作函数
from Xadmin.server.reverse_get_url import get_list_url, get_add_url, get_change_url, get_delete_url  # 引入反向解析url函数
from django.forms import ModelForm  # 引入modelform
from django.db.models.fields.related import ForeignKey, ManyToManyField, OneToOneField  # 引入外键类和多对多类
import copy
from django.urls import reverse


# modelXAdmin中list_view内容创建的类
class View_server(object):
    """
    本类服务于ModelXAdmin中的list_view 用于封装list_view中代码的冗余
    """

    def __init__(self, model_config, request, data_list):
        """
        :param model_config: model_config 为modelXAdmin 中self
        :param request: 请求信息
        :param data_list: 总数据
        :param page_html: 实例化分页obj
        :param self.data: 分页后当前页的所有数据
        :param self.actions: xadmin中action列表的内容 new_action()

        """
        self.model_config = model_config
        self.request = request
        self.data_list = data_list

        # 自定义分页
        page_num = int(self.request.GET.get('page', 1))  # 获取当前请求的页码，如果没有默认为 1
        data_quantity = self.data_list.count()  # 获取总数据量
        request_url = self.request.path  # 获取请求的url
        self.page_html = Pagination(page_num, data_quantity, request_url, self.request.GET, per_page=11, max_show=11)
        self.data = self.data_list[self.page_html.start:self.page_html.end]  # 使用分页后展示的当前页面的所有数据
        """
        Pagination参数
               :param current_page: 当前请求的页码
               :param total_count: 总数据量
               :param base_url: 请求的URL
               :param params: request.GET 获取请求携带的参数 以键值对的形式体现 #*新增
               :param per_page: 每页显示的数据量，默认值为10
               :param max_show: 页面上最多显示多少个页码，默认值为11
        """
        self.action = self.model_config.new_action()  # xadmin中action列表的内容 new_action()

    # 获取 list_filter 定制的a标签
    def get_listfilter_linktag(self):
        linktag = {}  # 定义一个空字典 存放 {'list_filter列名':[对应生成的a标签]}
        for filter in self.model_config.list_filter:  # 循环ModelXAdmin中的list_filter
            get_obj_id = self.request.GET.get(filter, 0)  # 获取get请求中循环的当前列名值 如果没有则为0 用于后面选中标签添加特殊类标记
            params = copy.deepcopy(self.request.GET)  # params 为深拷贝request.get的键值对
            field_obj = self.model_config.model._meta.get_field(filter)  # 获取字段对象
            # 如果获取到的字段是特殊字段则进行特殊处理
            if isinstance(field_obj, ForeignKey) or isinstance(field_obj, ManyToManyField) or isinstance(field_obj,
                                                                                                         OneToOneField):
                data_list = field_obj.rel.to.objects.all()  # 获取特殊字段 to 关联表的所有值
            else:  # 普通字段
                data_list = self.model_config.model.objects.all().values('pk', filter)  # 获取普通字段内容
            temp = []
            # 处理 all 标签
            if params.get(filter):  # 如果当前访问的请求中有携带本次循环列的参数 则构建一个删除除了本列参数内容 保留其他内容
                del params[filter]  # 删除当前列携带的参数
                temp.append("<a href='?{}'>all</a>".format(params.urlencode()))  # 将params rulencode()转化为url携带键值对形式
            else:
                temp.append("<a href='#' class='shine'>all</a>")
            # 处理其他数据标签
            for tag in data_list:
                # 如果获取到的字段是特殊字段则进行特殊处理
                if isinstance(field_obj, ForeignKey) or isinstance(field_obj, ManyToManyField) or isinstance(field_obj,
                                                                                                             OneToOneField):
                    # 如果是特殊字段 datalist是一个queryset对象
                    obj_pk = tag.pk  # 获取循环对象的主键值
                    obj_name = str(tag)  # 获取循环对象的__str__方法
                    params[filter] = obj_pk  # 特殊字段把request.get中增加 列名=对象的主键值作为参数放入params中
                else:
                    # 如果是普通字段 datalist是一个特殊的queryset对象 可迭代的字典序列
                    obj_pk = tag.get('pk')  # 获取queryset字典中的pk值
                    obj_name = tag.get(filter)  # 获取queryset字典中的当前列名
                    params[filter] = obj_name  # 普通字段把request.get中增加 列名=filter名
                _url = params.urlencode()  # 将params的键值对转化为url键值对形式 ?xxx=xxx&xxx=xxx
                # 如果当前循环构建标签是当前选中标签则增加 class='shine' 用于前端表示选中样式
                if str(get_obj_id) == str(obj_pk) or str(get_obj_id) == str(obj_name):
                    temp.append("<a href='?{}'class='shine'>{}</a>".format(_url, obj_name))
                else:
                    temp.append("<a href='?{}'>{}</a>".format(_url, obj_name))
                linktag[filter] = temp  # 将循环后构建好的temp 以{列名:[temp]}的形式存入linktag字典中
        return linktag  # 将字典linktag返还

    # 获取ModelAdmin类 action 列表
    def get_action_list(self):

        temp = []  # 自定义空列表
        for action in self.action:  # 循环self.action 依次添加数据 格式为{'name':action__name__,'desc':'别名 remove_name'}
            temp.append({
                'name': action.__name__,
                'desc': action.remove_name
            })
        return temp  # 返回列表

    # 处理list_view表头部分
    def get_list_view_head(self):
        # 创建head_list 用于存放表头
        head_list = []
        # 循环list_display 获取表头内容
        for head_name in self.model_config.new_list_display():
            # 判断display中循环是否为字符串 如果是函数 则调用时传入is_head = True
            if isinstance(head_name, str):
                # 如果是默认的display 遇到__str__ 自动将表头转化为表名的大写
                if head_name == "__str__":
                    head_list.append(self.model_config.model._meta.model_name.upper())
                # 如果使用修改后的display 表头为用户指定的列名
                else:
                    # 捕获model类中如果指定verbose_name的中文别名作为表头 如果没设置默认为原列名
                    row_obj = self.model_config.model._meta.get_field(head_name)
                    head_list.append(row_obj.verbose_name)
            else:
                # 判断如果是函数的话调用函数传入 is_head = True 把返回值放入head_list中
                head_list.append(head_name(self.model_config, is_head=True))
        return head_list

    # 处理list_view数据部分
    def get_list_view_body(self):
        # 创建obj_list 用于存放分段数据
        obj_list = []
        for obj in self.data:
            # 创建单表用于存放需要展示的具体内容 默认为创建model中的__str__下的内容
            sing_list = []
            for display in self.model_config.new_list_display():
                # 循环list_display内容 然后通过反射取出值加入sing_list中
                # 如果循环的display类型是str 则用反射找
                if isinstance(display, str):
                    try:  # 如果是默认 __str__ 获取field_obj会报错
                        field_obj = self.model_config.model._meta.get_field(display)
                        if isinstance(field_obj, ManyToManyField):
                            val = getattr(obj, display).all()
                            t = []
                            for v in val:
                                t.append(str(v))
                            ret = ','.join(t)
                        else:
                            ret = getattr(obj, display)
                    # 如果循环的display不是str类型则是函数调用取出
                    except Exception as e:  # 如果是 __str__ 则还是只取 getattr(obj, display)
                        ret = getattr(obj, display)
                else:
                    ret = display(self.model_config, obj)
                sing_list.append(ret)
            # 每循环一次 把构成的每一组信息表存放回obj_list中 用于传送到前段循环展出
            obj_list.append(sing_list)
        return obj_list


# 默认样式类
class ModelXAdmin(object):
    """
    list_display 自定义样式类接口放入需要展示的字段以字符串形式放入 也可以放入规定格式的函数名
    规定函数名规范 def 函数名(self, obj=None, is_head=False):如果是表头部分则不要传obj obj使用默认参数none 需要传入 is_head=true来确定表头
    而如果是处理数据则需要传入obj 需要获取obj.pk来获取该对象的主键值确定访问的页码等信息 is_head不需要传值 使用默认值
    list_display 对外注册有一个使列名自定义的接口 verbose_name 如果在model 定义函数的属性中加入则使用该列名捕获verbose_name为表头名
    list_display_link 用户可以定制使那一列变为可点击编辑的a便签 使用需要用户先配置list_display list_display_link中列需要在list_display基础上
    search_fields 用户可以定制模糊查找列行 如果用户为定制则不会渲染查询框
    action 列表提供批量操作功能 可定制函数后放入action中进行批量操作
    list_filter 列表提供用户定制指定字段进行快速检索条件跳转

    """

    def __init__(self, model, site):  # model 为models中的类变量 site 为 单例对象
        self.model = model
        self.site = site

    # 默认样式类 list_display
    list_display = ['__str__']  # 默认是复选框以及obj对象的__str__方法
    list_display_link = []  # 默认是空 如果用户指定编辑列表名则在此添加列名
    search_fields = []  # 如果用户指定在search_fields中添加列名则使用此列表中列名进行模糊查找
    action = []  # 指定action批量操作函数名 可定制
    list_filter = []  # 用户定制指定字段进行侧边栏展示进行快速检索

    # 自定义批量操作函数
    def action_delete(self, data):  # 批量删除 data传入为pk列表
        self.model.objects.filter(pk__in=data).delete()

    # 自定义批量处理函数重命名
    action_delete.remove_name = '批量删除'

    # 定义获取list_display 如果用户定制则使用用户定制后再放入默认
    def new_list_display(self):
        temp = []  # 定义一个空列表
        temp.append(select)  # 加入select操作函数
        temp.extend(self.list_display)  # 加入list_display中配置的内容
        if self.list_display_link:  # 如果list_display_link配置 pass
            pass
        else:
            temp.append(edit)  # 如果list_display_link未配置 则加入编辑函数
        temp.append(delete)  # 加入删除操作函数
        return temp  # 返回新的list_display

    # 定义获取新action列表 增加默认值
    def new_action(self):
        temp = []  # 定义一个列表
        temp.append(self.action_delete)  # 将默认项删除函数加入
        temp.extend(self.action)  # 如果用户定制将用户定制内容也加入
        return temp  # 返回列表

    # 获取modelform class
    def get_modelform_class(self):
        class modelform_class(ModelForm):  # 继承modelform
            class Meta:
                model = self.model  # 动态获取表名
                fields = '__all__'  # 默认转换所有字段

        return modelform_class

    # 获取search搜索条件
    def get_search_condition(self, request):
        from django.db.models import Q
        submit_search = request.GET.get("search", "")  # 获取提交上来的搜索条件 如果没提取到内容默认为空
        self.submit_search = submit_search  # 将搜索出来的search绑定到self.submit_search中 用于前端搜索后input框中的value
        search_Q_obj = Q()  # 实例化Q对象
        if submit_search:  # 如果有搜索值
            search_Q_obj.connector = 'or'  # Q查询或关系
            for fields in self.search_fields:  # 循环search_fields中把需要查找的列拿出
                search_Q_obj.children.append((fields + "__contains", submit_search))  # 列名 + 模糊查询 查找值
        return search_Q_obj  # 返回添加好的Q条件 search_Q_obj

    # 获取list_filter搜索条件
    def get_list_filter_condition(self, request):
        from django.db.models import Q
        list_filter_condition = Q()
        for filter, val in request.GET.items():  # 循环拿到的get请求携带的键值对
            if filter in self.list_filter:  # 判断 如果循环的字段存在 list_filter 才把条件值存入Q条件中 避免与page Q条件重复
                list_filter_condition.children.append((filter, val))  # q查询条件存入列名 查找值
        return list_filter_condition  # 返回q条件

    # 处理查看函数
    def list_view(self, request):
        if request.method == 'POST':  # 如果是post请求 action提交数据
            func = request.POST.get('func')  # 获取请求post值 func func为执行函数
            choice = request.POST.getlist('choice')  # 获取请求choice值 choice为选择需要执行的数据pk值
            ret = hasattr(self, func)  # 判断是否能通过反射找到
            if ret:  # 能通过反射找到 则传入参数执行该函数
                getattr(self, func)(choice)

        # 获取表名
        obj_name = self.model._meta.model_name
        # 获取search 的 Q 条件
        q_obj = self.get_search_condition(request)
        # 获取 list_filter 的 Q 条件
        filter_q_obj = self.get_list_filter_condition(request)
        # 获取self.model数据 如果有search将Q条件也传入 如果有list_filter将Q条件也传入 Q条件关系and
        data_list = self.model.objects.all().filter(q_obj).filter(filter_q_obj)
        # 实例化view_server对象
        # view_server中两个方法 view_obj.get_list_view_head()获取head_list以及view_obj.get_list_view_body()获取obj_list
        view_obj = View_server(self, request, data_list)
        add_url = get_add_url(self)  # 获取添加反向解析的url传入前端作为添加按钮跳转接口
        return render(request, 'list_view.html',
                      {'view_obj': view_obj, "obj_name": obj_name, 'add_url': add_url})

    # 处理添加函数
    def add_view(self, request):
        from django.forms.models import ModelChoiceField
        modelform_class = self.get_modelform_class()  # 实例化modelform 将实例化对象传到模板中构建input框
        # 获取表名
        obj_name = self.model._meta.model_name
        if request.method == 'POST':
            form_obj = modelform_class(request.POST)  # 将前端传回的值进行form校验
            if form_obj.is_valid():  # 通过校验
                new_obj = form_obj.save()  # 校验成功后保存数据
                if request.GET.get('relevance_pop'):  # 拿到post请求的get值 判断是否有 relevance_pop 如果有证明是通过window窗口访问
                    field_name = request.GET.get('relevance_pop')
                    obj_pk = new_obj.pk
                    obj_name = str(new_obj)
                    return render(request, 'pop.html', {'field_name': field_name, 'obj_pk': obj_pk,
                                                        'obj_name': obj_name})  # 返回指定的pop页面执行script内容
                else:
                    _url = get_list_url(self)  # 反向解析拿到查看url
                    return redirect(_url)
            else:  # 重新返回添加页面 并把error值返回展现 返还的是经过校验的modelform_class 为 form_obj
                return render(request, 'add_list.html', {'modelform_class': form_obj, 'obj_name': obj_name})
        else:
            form_obj = modelform_class()
            for bfield in form_obj:  # 循环modelform对象
                if isinstance(bfield.field, ModelChoiceField):  # 如果是ChoiceField类对象则为多对多关系或外键关系则
                    try:
                        bfield.is_pop = True  # 如果满足条件设置标志位 用于add页面渲染 pop功能
                        relevance_model_name = bfield.field.queryset.model._meta.model_name  # 获取关联表对应的字段名
                        relevance_app_name = bfield.field.queryset.model._meta.app_label  # 获取关联表对应的app名
                        _url = reverse('{}_{}_add'.format(relevance_app_name, relevance_model_name))  # 反向解析 找到关联表的add页面
                        bfield.url = _url + '?relevance_pop={}'.format(bfield.name)  # 设置标记位 用于传入前端调用事件函数参数
                    except Exception as e:  # 如果抛错 则是 AbstractUser 对象
                        pass
            return render(request, 'add_list.html', {'modelform_class': form_obj, 'obj_name': obj_name})

    # 处理修改函数
    def change_view(self, request, page):
        obj = self.model.objects.filter(pk=page).first()  # 通过page找到相应的对象 queryset对象
        modelform_class = self.get_modelform_class()  # 实例化modelform 将实例化对象传到模板中构建input框
        _url = get_list_url(self)  # 查看url
        # 获取表名
        obj_name = self.model._meta.model_name
        if not obj:  # 如果对象不存在返回查看
            return redirect(_url)
        if request.method == 'POST':  # 如果为提交请求
            form_obj = modelform_class(request.POST, instance=obj)  # 将找到的对象传入modelform_class中进行校验
            if form_obj.is_valid():  # 校验成功
                form_obj.save()  # 将数据进行保存
                return redirect(_url)  # 返回查看页面
            else:
                return render(request, 'change_list.html',
                              {'modelform_class': form_obj, 'obj_name': obj_name})  # 将错误信息返回到前端进行重新渲染
        else:
            form_obj = modelform_class(instance=obj)
            return render(request, 'change_list.html', {"modelform_class": form_obj, "obj_name": obj_name})

    # 处理删除函数
    def delete_view(self, request, page):
        try:
            obj = self.model.objects.filter(pk=page).delete()
            return redirect(get_list_url(self))
        except Exception as e:
            return redirect(get_list_url(self))

    # 创建获取url2的方法
    def get_url2(self):
        temp = []
        model_name = self.model._meta.model_name
        app_name = self.model._meta.app_label
        temp.append(
            url(r"^$", self.list_view, name='{}_{}'.format(app_name, model_name)))  # url2分发到查视图,name app名_访问表名 用于反向解析
        temp.append(url(r"^add/$", self.add_view,
                        name='{}_{}_add'.format(app_name, model_name)))  # url2分发到增视图,name app名_访问表名_add 用于反向解析
        temp.append(url(r"^(\d+)/change/$", self.change_view,
                        name='{}_{}_change'.format(app_name, model_name)))  # url2分发到改视图,name app名_访问表名_change 用于反向解析
        temp.append(url(r"^(\d+)/delete/$", self.delete_view,
                        name='{}_{}_delete'.format(app_name, model_name)))  # url2分发到删视图,name app名_访问表名_delete 用于反向解析
        return temp

    # 创建urls方法实现二级路由分发
    @property  # 伪装为类的静态方法可直接调用不用加括号调用
    def urls2(self):
        return self.get_url2(), None, None  # 返回三个值 分别为列表(列表中存放url路径),None,None


# 创建单例对象
class Xadminsite(object):
    """
    用于XAdmin实现单例 初始化self._registry为{}
    register用于实现调用实例化对象后实现注册功能 将 model类：adminclass(model) 存储的self._registry 以便于后面的使用
    get_url 实现获取一级分发返回的url列表
    urls 实现一级路由分发

    """

    def __init__(self):
        # 注册后的对象以及配置类存放的字典
        self._registry = {}

    # 创建获取url的方法
    def get_url(self):
        temp = []  # 创建一个列表，用于返回url
        for model, admin_class_obj in self._registry.items():  # model为注册的类名(拆分为str) admin_class_obj为对应的样式类名(拆分为str)
            app_name = model._meta.app_label  # 获取app变量名
            model_name = model._meta.model_name  # 获取model中对应模型的类变量
            temp.append(url(r'^{}/{}/'.format(app_name, model_name), admin_class_obj.urls2))  # 将url添加到temp列表中返回
        return temp

    # 创建urls方法实现一级路由分发
    @property  # 伪装为类的静态方法可直接调用不用加括号调用
    def urls(self):
        return self.get_url(), None, None  # 返回三个值 分别为列表(列表中存放url路径),None,None

        # 创建register方法 如果APP注册时传样式类会用用户自定义样式类，如果不传默认赋值为默认的样式类

    def register(self, model, admin_class=None, **kwargs):
        if not admin_class:
            # 如果用户未传样式类则使用默认类
            admin_class = ModelXAdmin
        self._registry[model] = admin_class(model, self)


site = Xadminsite()  # 调用Xadminsite 通过模块的方法引入 实现单例 site为单例对象
