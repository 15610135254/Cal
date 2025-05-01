#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import os
from sqlalchemy import create_engine, text
import time

def import_csv_to_mysql():
    """将CSV数据导入到MySQL数据库"""
    print("\n=== 开始导入CSV数据到MySQL ===\n")
    
    # 检查CSV文件是否存在
    csv_file_path = 'newxinxi(1).csv'
    if not os.path.exists(csv_file_path):
        print(f"错误: CSV文件 {csv_file_path} 不存在")
        return False
    
    print(f"找到CSV文件: {csv_file_path}")
    
    try:
        # 读取CSV文件
        df = pd.read_csv(csv_file_path)
        print(f"从CSV读取了 {len(df)} 条记录")
        
        # 检查列名并规范化处理
        print(f"CSV文件列名: {df.columns.tolist()}")
        
        # 创建MySQL连接
        try:
            mysql_engine = create_engine('mysql+pymysql://root:@127.0.0.1:3306/xinxi?charset=utf8mb4')
            print("成功连接到MySQL数据库")
            
            # 在导入之前清空XinXi表
            with mysql_engine.connect() as conn:
                conn.execute(text("TRUNCATE TABLE XinXi"))
                print("已清空XinXi表")
            
            # 写入MySQL
            df.to_sql('XinXi', mysql_engine, if_exists='append', index=False)
            print(f"成功导入 {len(df)} 条记录到MySQL表 XinXi")
            
            # 验证导入
            with mysql_engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM XinXi"))
                count = result.scalar()
                print(f"导入后XinXi表中有 {count} 条记录")
            
            print("\n=== 数据导入完成 ===")
            return True
            
        except Exception as e:
            print(f"连接MySQL数据库或导入数据时出错: {e}")
            return False
            
    except Exception as e:
        print(f"读取CSV文件出错: {e}")
        return False

if __name__ == "__main__":
    success = import_csv_to_mysql()
    if success:
        print("\nCSV数据成功导入到MySQL。系统现在仅使用MySQL数据库。")
        # 可以选择删除或备份SQLite数据库文件
        try:
            sqlite_db_path = os.path.join(os.getcwd(), 'xinxi.db')
            if os.path.exists(sqlite_db_path):
                backup_path = 'xinxi.db.bak'
                # 如果备份已存在，无需再次备份
                if not os.path.exists(backup_path):
                    import shutil
                    shutil.copy2(sqlite_db_path, backup_path)
                    print(f"已将原SQLite数据库备份为: {backup_path}")
                # 删除原SQLite数据库文件
                os.remove(sqlite_db_path)
                print(f"已删除SQLite数据库文件: {sqlite_db_path}")
        except Exception as e:
            print(f"处理SQLite文件时出错: {e}")
    else:
        print("\n数据导入失败，请检查错误信息并修复问题。") 