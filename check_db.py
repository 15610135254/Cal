import models
from models import app, ShuJu

with app.app_context():
    count = ShuJu.query.count()
    print(f"ShuJu表中有 {count} 条记录")
    
    if count > 0:
        # 获取前5条记录
        records = ShuJu.query.limit(5).all()
        print("\n前5条记录:")
        for record in records:
            print(f"ID: {record.id}, 招录机关: {record.招录机关}, 职位名称: {record.职位名称}")
    else:
        print("ShuJu表中没有记录")
        
    # 检查数据目录是否存在
    import os
    data_path = '2020-2022安徽省考入围分数统计/2022安徽省考入围分数各岗位报考人数统计/'
    if os.path.exists(data_path):
        files = os.listdir(data_path)
        print(f"\n数据目录存在，包含 {len(files)} 个文件")
        if files:
            print(f"前几个文件: {files[:5]}")
    else:
        print(f"\n数据目录不存在: {data_path}")
