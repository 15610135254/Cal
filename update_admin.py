import models
from models import app, User, Role, db
from flask_security import SQLAlchemySessionUserDatastore

with app.app_context():
    # 设置用户数据存储
    user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
    
    # 查找admin用户
    admin_user = User.query.filter_by(username='admin').first()
    
    if admin_user:
        print(f"找到用户: {admin_user.username}")
        
        # 更新密码
        admin_user.password = 'admin123'
        print("已更新密码为: admin123")
        
        # 查找admin角色
        admin_role = Role.query.filter_by(name='admin').first()
        
        if admin_role:
            # 检查用户是否已有admin角色
            has_admin_role = False
            for role in admin_user.roles:
                if role.name == 'admin':
                    has_admin_role = True
                    break
            
            if not has_admin_role:
                # 添加admin角色
                user_datastore.add_role_to_user(admin_user, admin_role)
                print(f"已为用户 {admin_user.username} 添加 admin 角色")
            else:
                print(f"用户 {admin_user.username} 已有 admin 角色")
        else:
            print("错误: 未找到admin角色")
        
        # 提交更改
        db.session.commit()
        print("更改已保存到数据库")
    else:
        print("未找到用户名为admin的用户，将创建新用户")
        
        # 创建新的admin用户
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = user_datastore.create_role(name='admin', description='管理员')
            print("已创建admin角色")
        
        admin_user = user_datastore.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            active=True
        )
        print("已创建admin用户")
        
        # 添加admin角色
        user_datastore.add_role_to_user(admin_user, admin_role)
        print("已为新用户添加admin角色")
        
        # 提交更改
        db.session.commit()
        print("新用户已保存到数据库")
