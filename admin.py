from flask_admin import Admin,AdminIndexView
from main import app
from flask_admin.contrib.sqla import ModelView
from flask import current_app,redirect,url_for,request
from models import db,User, Role, RolesUsers,XinXi,ShuJu
from flask_security import current_user

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

class MyUser(MyModelView):
    column_labels = dict(
        username='账号',
        email='邮箱',
        password='密码'
    )
    column_searchable_list = ['username']

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
admin.add_view(MyUser(User, db.session,name='用户管理'))
admin.add_view(MyModelView(Role, db.session,name='用户权限管理'))

if __name__ == '__main__':
    app.run(debug=True)