import pandas as pd
import os

data_path = '2020-2022安徽省考入围分数统计/2022安徽省考入围分数各岗位报考人数统计/'
files = os.listdir(data_path)

if files:
    # 检查第一个文件
    first_file = files[0]
    file_path = os.path.join(data_path, first_file)
    print(f"检查文件: {file_path}")
    
    try:
        # 尝试读取Excel文件
        df = pd.read_excel(file_path, header=1)
        print(f"文件成功读取，包含 {len(df)} 行数据")
        
        # 显示列名
        print("\n列名:")
        print(df.columns.tolist())
        
        # 显示前几行数据
        print("\n前3行数据:")
        print(df.head(3))
        
        # 检查数据类型
        print("\n数据类型:")
        print(df.dtypes)
        
        # 检查是否有空值
        print("\n空值统计:")
        print(df.isnull().sum())
        
        # 检查行数据的长度
        if len(df) > 0:
            first_row = df.values.tolist()[0]
            print(f"\n第一行数据长度: {len(first_row)}")
            print(f"第一行数据: {first_row}")
    except Exception as e:
        print(f"读取文件时出错: {e}")
else:
    print("目录中没有文件")
