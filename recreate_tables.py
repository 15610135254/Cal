import models
from models import app

# 使用应用上下文
with app.app_context():
    # 删除所有表
    print("正在删除所有表...")
    models.db.drop_all()
    
    # 重新创建所有表
    print("正在重新创建所有表...")
    models.db.create_all()
    
    print("数据库表已重新创建")
    
    # 检查ShuJu表是否存在
    from sqlalchemy import inspect
    inspector = inspect(models.db.engine)
    tables = inspector.get_table_names()
    print(f"数据库中的表: {tables}")
    
    if 'ShuJu' in tables:
        # 获取ShuJu表的列信息
        columns = inspector.get_columns('ShuJu')
        print("\nShuJu表的列信息:")
        for column in columns:
            print(f"  {column['name']}: {column['type']}")
