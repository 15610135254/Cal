import models
from models import app
import os
import pandas
import numpy as np

pandas.set_option('display.max_columns', None)
pandas.set_option('display.width', 1000)

print("开始导入入围数据...")

# 获取数据文件列表
data_path = '2020-2022安徽省考入围分数统计/2022安徽省考入围分数各岗位报考人数统计/'
list1 = os.listdir(data_path)
print(f"找到 {len(list1)} 个文件")

# 记录成功和失败的文件
success_files = []
failed_files = []
total_records = 0

# 使用应用上下文
with app.app_context():
    # 处理每个文件
    for file_name in list1:
        if file_name.startswith('.'):  # 跳过隐藏文件
            continue

        file_path = os.path.join(data_path, file_name)
        print(f"\n处理文件: {file_path}")

        try:
            # 读取Excel文件，跳过第一行（标题行）
            df = pandas.read_excel(file_path, header=1)
            print(f"文件读取成功，包含 {len(df)} 行数据")

            # 跳过第一行，因为它通常包含列名
            df = df.iloc[1:].reset_index(drop=True)

            # 处理每一行数据
            success_count = 0
            for index, row_data in df.iterrows():
                # 将NaN值转换为None
                row_values = [None if isinstance(x, float) and np.isnan(x) else x for x in row_data.values]

                # 确保数据长度足够
                if len(row_values) < 21:
                    print(f"  警告: 第 {index+2} 行数据长度不足 ({len(row_values)}/21)，跳过")
                    continue

                # 跳过空行（主要字段为空）
                if row_values[0] is None or row_values[4] is None:  # 招录机关或职位名称为空
                    continue

                try:
                    # 创建并添加记录
                    record = models.ShuJu(
                        招录机关=row_values[0],
                        机构性质=row_values[1],
                        机构层级=row_values[2],
                        职位类别=row_values[3],
                        职位名称=row_values[4],
                        职级层次=row_values[5],
                        报考人数=str(row_values[6]) if row_values[6] is not None else None,
                        最低进面分=str(row_values[7]) if row_values[7] is not None else None,
                        最高进面分=str(row_values[8]) if row_values[8] is not None else None,
                        职位代码=str(row_values[9]) if row_values[9] is not None else None,
                        招考人数=str(row_values[10]) if row_values[10] is not None else None,
                        职位资格条件和要求=row_values[11],
                        专业=row_values[12],
                        学历=row_values[13],
                        学位=row_values[14],
                        年龄=row_values[15],
                        经历要求=row_values[16],
                        其他=row_values[17],
                        申论类别=row_values[18],
                        专业科目=row_values[19],
                        咨询电话=row_values[20],
                    )
                    models.db.session.add(record)
                    success_count += 1

                    # 每100条记录提交一次，减少数据库负担
                    if success_count % 100 == 0:
                        models.db.session.commit()
                        print(f"  已成功导入 {success_count} 条记录")

                except Exception as e:
                    print(f"  错误: 处理第 {index+2} 行时出错: {e}")
                    continue

            # 提交剩余的记录
            models.db.session.commit()
            total_records += success_count
            success_files.append(file_name)
            print(f"文件 {file_name} 处理完成，成功导入 {success_count} 条记录")

        except Exception as e:
            models.db.session.rollback()
            failed_files.append(file_name)
            print(f"错误: 处理文件 {file_name} 时出错: {e}")
            continue

# 打印导入结果摘要
print("\n=== 导入完成 ===")
print(f"总共处理了 {len(list1)} 个文件")
print(f"成功: {len(success_files)} 个文件")
print(f"失败: {len(failed_files)} 个文件")
print(f"总共导入了 {total_records} 条记录")

if failed_files:
    print("\n失败的文件:")
    for file in failed_files:
        print(f"- {file}")
