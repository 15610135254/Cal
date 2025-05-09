import models
from models import app, ShuJu

with app.app_context():
    # 检查ShuJu表中的记录数
    count = ShuJu.query.count()
    print(f"ShuJu表中有 {count} 条记录")
    
    if count > 0:
        # 获取前5条记录
        records = ShuJu.query.limit(5).all()
        print("\n前5条记录:")
        for record in records:
            print(f"ID: {record.id}, 招录机关: {record.招录机关}, 职位名称: {record.职位名称}, 最低进面分: {record.最低进面分}")
