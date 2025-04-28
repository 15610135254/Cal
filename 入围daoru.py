import models
import datetime
import os
import pandas

list1 = os.listdir('2020-2022安徽省考入围分数统计/2022安徽省考入围分数各岗位报考人数统计/')
# print(list1)

for row in list1[1:]:
    df = pandas.read_excel("2020-2022安徽省考入围分数统计/2022安徽省考入围分数各岗位报考人数统计/{}".format(row), header=1)
    i1 = 0
    try:
        for row in df.values.tolist():
            print(row)
            models.db.session.add(
                models.ShuJu(
                    招录机关=row[0],
                    机构性质=row[1],
                    机构层级=row[2],
                    职位类别=row[3],
                    职位名称=row[4],
                    职级层次=row[5],
                    报考人数=row[6],
                    最低进面分=row[7],
                    最高进面分=row[8],
                    职位代码=row[9],
                    招考人数=row[10],
                    职位资格条件和要求=row[11],
                    专业=row[12],
                    学历=row[13],
                    学位=row[14],
                    年龄=row[15],
                    经历要求=row[16],
                    其他=row[17],
                    申论类别=row[18],
                    专业科目=row[19],
                    咨询电话=row[20],
                )
            )
            models.db.session.commit()
    except:
        models.db.session.rollback()
        continue
