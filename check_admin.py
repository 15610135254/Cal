import models
from models import app, User, Role

with app.app_context():
    # 检查用户表中的记录
    users = User.query.all()
    print(f"用户表中有 {len(users)} 条记录")
    
    if users:
        print("\n现有用户:")
        for user in users:
            roles = [role.name for role in user.roles]
            print(f"ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}, 角色: {roles}")
    else:
        print("用户表中没有记录")
        
    # 检查角色表
    roles = Role.query.all()
    print(f"\n角色表中有 {len(roles)} 条记录")
    
    if roles:
        print("\n现有角色:")
        for role in roles:
            print(f"ID: {role.id}, 角色名: {role.name}, 描述: {role.description}")
    else:
        print("角色表中没有记录")
