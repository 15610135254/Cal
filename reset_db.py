#!/usr/bin/env python
# -*- coding: utf-8 -*-

from models import db, app

def reset_database():
    with app.app_context():
        print("删除所有表...")
        db.drop_all()
        print("创建新表...")
        db.create_all()
        print("数据库重置完成！")

if __name__ == "__main__":
    reset_database() 