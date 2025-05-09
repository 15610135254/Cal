import models
from models import app, User, Role, db
from flask_security import SQLAlchemySessionUserDatastore

def fix_users_roles():
    """修复没有角色的用户，为其分配默认的 'User' 角色"""
    with app.app_context():
        # 设置用户数据存储
        user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
        
        # 查找所有用户
        users = User.query.all()
        print(f"找到 {len(users)} 个用户")
        
        # 查找或创建 'User' 角色
        normal_role = user_datastore.find_or_create_role(name='User', description='普通用户')
        
        # 遍历所有用户，检查是否有角色
        for user in users:
            if not user.roles:
                print(f"用户 '{user.username}' 没有角色，添加 'User' 角色")
                user_datastore.add_role_to_user(user, normal_role)
        
        # 提交更改到数据库
        db.session.commit()
        print("用户角色修复完成")
        
        # 验证修复结果
        for user in User.query.all():
            roles = [role.name for role in user.roles]
            print(f"用户 '{user.username}' 的角色: {roles}")

if __name__ == "__main__":
    fix_users_roles()
