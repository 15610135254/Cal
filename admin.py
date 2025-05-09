from flask_admin import Admin,AdminIndexView
from models import app
from flask_admin.contrib.sqla import ModelView
from flask import current_app,redirect,url_for,request
from models import db,User, Role, RolesUsers,XinXi,ShuJu
from flask_security import current_user, utils as security_utils
from wtforms import PasswordField
from flask_admin.contrib.sqla.fields import QuerySelectMultipleField
from wtforms.widgets import ListWidget, CheckboxInput

# 自定义一个 QuerySelectMultipleField 来修复 iter_choices 的问题
class CustomQuerySelectMultipleField(QuerySelectMultipleField):
    widget = ListWidget(prefix_label=False) # 通常多对多关系用 checkbox
    option_widget = CheckboxInput()

    def iter_choices(self):
        for pk, obj in self._get_object_list():
            selected = False
            if self.data: # self.data 是已选中的 Role 对象列表
                selected = obj in self.data
            yield (pk, self.get_label(obj), selected, {}) # 确保返回4个值，最后一个是空的 render_kw

class MyModelView(ModelView):
    def is_accessible(self):
        if current_user.is_anonymous:
            return False
        for resu in User.query.get(current_user.get_id()).roles:
            if resu.name == 'admin':
                return True
        return False

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('index'))

# 为 User 创建特定的 Admin View
class UserAdminView(MyModelView): # 继承自 MyModelView 以保持权限控制
    form_columns = ['username', 'email', 'password', 'active', 'roles']
    form_extra_fields = {
        'password': PasswordField('Password')
    }
    # 使用 form_overrides 来指定 roles 字段使用我们自定义的字段
    form_overrides = {
        'roles': CustomQuerySelectMultipleField
    }

    # 如果需要，可以为自定义字段提供额外的参数
    form_args = {
        'roles': {
            'label': 'Roles', # 或者从 Role 模型自动获取
            'query_factory': lambda: Role.query.all(), # 提供一个查询工厂来获取所有 Role 对象
            'get_label': 'name', # 使用 Role 模型的 name 属性作为标签
             # 'allow_blank': True, # 如果允许不选择任何角色
        }
    }

    def on_model_change(self, form, model, is_created):
        if is_created:
            if not form.password.data:
                # 创建新用户时密码是必需的。
                # 理想情况下，这应该由表单验证器（如 DataRequired）处理。
                # 在此处添加检查是为了增加一层保障，防止创建没有密码的用户。
                raise ValueError("创建新用户时必须提供密码。")
            model.password = form.password.data # 直接赋值，不加密
        else: # 更新现有用户
            # 仅当表单中实际提供了新密码时才更新。
            # 如果密码字段为空，则表示管理员不想更改现有密码。
            if form.password.data:
                model.password = form.password.data # 直接赋值，不加密
        
        # 'roles' 的处理:
        # Flask-Admin 的 ModelView 会自动处理 'roles' 关系的更新，
        # 因为 'roles' 存在于 'form_columns' 中，并且是 User 模型上的一个关系属性。
        # 表单提交的角色数据 (form.roles.data) 会在会话提交前用于更新 model.roles。

# 为 Role 创建特定的 Admin View
class RoleAdminView(MyModelView): # 继承自 MyModelView 以保持权限控制
    form_columns = ['name'] # 之前测试到这里仍然报错
    form_widget_args = {
        'name': {
            'flags': {} # 显式提供一个空的 flags 字典
        }
    }

class MyItem(MyModelView):
    column_searchable_list = ['地区', '部门名称', '职位', '学历', '专业']

class MyShuJu(MyModelView):
    column_searchable_list = ['招录机关', '机构性质', '机构层级', '职位类别', '职位名称']

admin = Admin(app=app, name='后台管理系统',template_mode='bootstrap3', base_template='admin/mybase.html',index_view=AdminIndexView(
        name='导航栏',
        template='admin/welcome.html',
        url='/admin'
    ))

admin.add_view(MyItem(XinXi, db.session,name='进面数据管理'))
admin.add_view(MyShuJu(ShuJu, db.session,name='入围数据管理'))
admin.add_view(UserAdminView(User, db.session,name='用户管理'))
admin.add_view(RoleAdminView(Role, db.session,name='用户权限管理'))

if __name__ == '__main__':
    app.run(debug=True)