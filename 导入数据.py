import pandas as pd
from models import db, XinXi

# 读取newxinxi.csv文件
df = pd.read_csv('newxinxi.csv')

# 删除现有的XinXi表数据
XinXi.query.delete()

# 将数据导入到XinXi表中
for _, row in df.iterrows():
    xinxi = XinXi(
        年份=row['年份'],
        岗位代码=row['岗位代码'],
        地区=row['地区'],
        部门名称=row['部门名称'],
        职位=row['职位'],
        学历=row['学历'],
        专业=row['专业'],
        招考人数=row['招考人数'],
        报考人数=row['报考人数'],
        分数线=row['分数线'],
        最高分=row['最高分']
    )
    db.session.add(xinxi)

# 提交事务
db.session.commit()