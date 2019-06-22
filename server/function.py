from django.utils.safestring import mark_safe  # Django内置不转义方法
from Xadmin.server.reverse_get_url import get_list_url, get_add_url, get_change_url, get_delete_url  # 引入反向解析url函数


# 自定义select单选框
def select(self, obj=None, is_head=False):
    # is_head = True 表示表头调用 返回表头列
    if is_head:
        return mark_safe("<input type='checkbox' id='checkbox_all'></input>")  # 在表头为全选框 id为 checkbox_all 用于绑定js事件
    return mark_safe("<input type='checkbox' name='choice' value={0} id='{0}'></input>".format(obj.pk))  # 为数据处理的复选框绑定id 与每条信息的主键值相对应


# 自定义编辑按钮
def edit(self, obj=None, is_head=False):
    # is_head = True 表示表头调用 返回表头列
    if is_head:
        return "操作"
    return mark_safe("<a href='{}'>编辑</a>".format(get_change_url(self, obj)))


# 自定义删除按钮
def delete(self, obj=None, is_head=False):
    if is_head:
        return "操作"
    return mark_safe(
        "<a url={} class='my_delete' id='delete_{}'>删除</a>".format(get_delete_url(self, obj),
                                                                   obj.pk))  # class=my_delete 用于绑定事件呼出弹出框 id=obj.pk


# 自定义分页
class Pagination(object):
    """自定义分页（Bootstrap版）"""

    def __init__(self, current_page, total_count, base_url, params, per_page=10, max_show=11):
        """
        :param current_page: 当前请求的页码
        :param total_count: 总数据量
        :param base_url: 请求的URL
        :param params: request.GET 获取请求携带的参数 以键值对的形式体现 #*新增
        :param per_page: 每页显示的数据量，默认值为10
        :param max_show: 页面上最多显示多少个页码，默认值为11
        """
        try:
            self.current_page = int(current_page)
        except Exception as e:
            # 取不到或者页码数不是数字都默认展示第1页
            self.current_page = 1
        # 定义每页显示多少条数据
        self.per_page = per_page
        # 计算出总页码数
        total_page, more = divmod(total_count, per_page)
        if more:
            total_page += 1
        self.total_page = total_page
        # 定义页面上最多显示多少页码(为了左右对称，一般设为奇数)
        self.max_show = max_show
        self.half_show = max_show // 2
        self.base_url = base_url
        # *新增
        import copy
        self.params = copy.deepcopy(params)

    @property
    def start(self):
        return (self.current_page - 1) * self.per_page

    @property
    def end(self):
        return self.current_page * self.per_page

    def page_html(self):
        # 计算一下页面显示的页码范围
        if self.total_page <= self.max_show:  # 总页码数小于最大显示页码数
            page_start = 1
            page_end = self.total_page
        elif self.current_page + self.half_show >= self.total_page:  # 右边越界
            page_end = self.total_page
            page_start = self.total_page - self.max_show
        elif self.current_page - self.half_show <= 1:  # 左边越界
            page_start = 1
            page_end = self.max_show
        else:  # 正常页码区间
            page_start = self.current_page - self.half_show
            page_end = self.current_page + self.half_show
        # 生成页面上显示的页码
        page_html_list = []
        page_html_list.append('<nav aria-label="Page navigation"><ul class="pagination">')
        # 加首页
        first_li = '<li><a href="{}?page=1">首页</a></li>'.format(self.base_url)
        page_html_list.append(first_li)
        # 加上一页
        if self.current_page == 1:
            prev_li = '<li><a href="#"><span aria-hidden="true">&laquo;</span></a></li>'
        else:
            prev_li = '<li><a href="{}?page={}"><span aria-hidden="true">&laquo;</span></a></li>'.format(
                self.base_url, self.current_page - 1)
        page_html_list.append(prev_li)

        # 新增功能 可以让生成的页码标签动态携带其他参数变量 而不是写死的url #*
        for i in range(page_start, page_end + 1):
            self.params['page'] = i  # *
            if i == self.current_page:
                li_tag = '<li class="active"><a href="{0}?page={1}">{1}</a></li>'.format(self.base_url, i)
            else:
                li_tag = '<li><a href="{0}?{1}">{2}</a></li>'.format(self.base_url, self.params.urlencode(),i)
            page_html_list.append(li_tag)
        # 加下一页
        if self.current_page == self.total_page:
            next_li = '<li><a href="#"><span aria-hidden="true">&raquo;</span></a></li>'
        else:
            next_li = '<li><a href="{}?page={}"><span aria-hidden="true">&raquo;</span></a></li>'.format(
                self.base_url, self.current_page + 1)
        page_html_list.append(next_li)
        # 加尾页
        page_end_li = '<li><a href="{}?page={}">尾页</a></li>'.format(self.base_url, self.total_page)
        page_html_list.append(page_end_li)
        page_html_list.append('</ul></nav>')
        return "".join(page_html_list)
