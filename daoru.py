import pandas
import models
import os

list1 = os.listdir('2020-2022安徽省考入围分数统计/2023安徽省考进面分数/')
print(list1)

for row in list1:
    df = pandas.read_excel("2020-2022安徽省考入围分数统计/2023安徽省考进面分数/{}".format(row),header=1)
    i1 = 0
    for row in df.values.tolist():
        i1 += 1
        models.db.session.add(
            models.XinXi(
                年份=row[0],
                岗位代码=row[1],
                地区=row[2],
                部门名称=row[3],
                职位=row[4],
                学历=row[5],
                专业=row[6],
                招考人数=row[7],
                报考人数=row[8],
                分数线=row[9],
                最高分=row[10],
            )
        )
        models.db.session.commit()