from flask import current_app, redirect, url_for, request
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_security import current_user
from wtforms import PasswordField

from models import app, db, User, Role, XinXi, ShuJu

def get_roles():
    return Role.query.filter(Role.name.in_(['User', 'admin'])).all()

def format_role_name(view, context, model, name):
    return model.role.name if model.role else ''

# 自定义查询选择字段，用于角色选择
class CustomQuerySelectField(QuerySelectField):
    def __init__(self, *args, **kwargs):
        super(CustomQuerySelectField, self).__init__(*args, **kwargs)

    def iter_choices(self):
        for pk, obj in self._get_object_list():
            selected = self.data == obj
            yield (pk, self.get_label(obj), selected, {})

    def process_formdata(self, valuelist):
        if valuelist:
            pk = valuelist[0]
            for val, obj in self._get_object_list():
                if str(val) == str(pk):
                    self.data = obj
                    break
            else:
                self.data = None
        else:
            self.data = None

# 基础管理视图，实现权限控制
class MyModelView(ModelView):
    def is_accessible(self):
        if current_user.is_anonymous:
            return False
        user = User.query.get(current_user.get_id())
        if user and user.role and user.role.name == 'admin':
            return True
        return False

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('index'))

# 用户管理视图
class UserAdminView(MyModelView):
    form_columns = ['username', 'email', 'password', 'active', 'role']
    form_extra_fields = {
        'password': PasswordField('密码')
    }
    form_overrides = {
        'role': CustomQuerySelectField
    }

    form_args = {
        'role': {
            'label': '角色',
            'query_factory': get_roles,
            'get_label': 'name',
            'allow_blank': False,
        }
    }
    
    column_labels = {
        'username': '用户名',
        'email': '邮箱',
        'active': '激活状态',
        'role': '角色'
    }

    def on_model_change(self, form, model, is_created):
        if is_created:
            if not form.password.data:
                raise ValueError("创建新用户时必须提供密码。")
            model.password = form.password.data
        else:
            if form.password.data:
                model.password = form.password.data

        try:
            if hasattr(form, 'role') and form.role.data:
                model.role = form.role.data
        except Exception as e:
            print(f"处理角色时出错: {e}")

# 用户角色管理视图
class UserRoleAdminView(MyModelView):
    column_list = ['username', 'email', 'role']
    form_columns = ['role']

    form_overrides = {
        'role': CustomQuerySelectField
    }

    form_args = {
        'role': {
            'label': '角色',
            'query_factory': get_roles,
            'get_label': 'name',
            'allow_blank': False,
        }
    }

    can_create = False
    can_delete = False

    column_labels = {
        'username': '用户名',
        'email': '邮箱',
        'role': '角色'
    }
    
    column_formatters = {
        'role': format_role_name
    }

    def on_model_change(self, form, model, is_created):
        try:
            if hasattr(form, 'role') and form.role.data:
                model.role = form.role.data
        except Exception as e:
            print(f"处理角色时出错: {e}")

# 进面数据管理视图
class MyItem(MyModelView):
    column_searchable_list = ['地区', '部门名称', '职位', '学历', '专业']

# 入围数据管理视图
class MyShuJu(MyModelView):
    column_searchable_list = ['招录机关', '机构性质', '机构层级', '职位类别', '职位名称']

# 初始化后台管理系统
admin = Admin(
    app=app,
    name='后台管理系统',
    template_mode='bootstrap3',
    base_template='admin/mybase.html',
    index_view=AdminIndexView(
        name='导航栏',
        template='admin/welcome.html',
        url='/admin'
    )
)

admin.add_view(MyItem(XinXi, db.session, name='进面数据管理'))
admin.add_view(MyShuJu(ShuJu, db.session, name='入围数据管理'))
admin.add_view(UserAdminView(User, db.session, name='用户管理'))
admin.add_view(UserRoleAdminView(User, db.session, name='用户权限管理', endpoint='userrole'))

if __name__ == '__main__':
    app.run(debug=True)