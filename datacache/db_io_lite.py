#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@File    :   db_io_lite.py 
@Desciption    :   sqlite 操作封装
@Author    :   LensonYuan   
@Contact :   15000959076@163.com
@License :   (C)Copyright 2019-2021, HQ-33Lab

@Modify Time         @Version   
------------         --------
2019/11/8 09:58         1.0  
"""

import sqlite3
from common.utils import logger
from common.utils import project_path


class SQLITE:
    def __init__(self, db_file):
        """
        :param db: 数据库文件链接, 默认 在datacache文件夹下
        """
        self.db = project_path() + '/datacache/' + db_file

    def __GetConnect(self):
        """
        得到连接信息
        返回: conn.cursor()
        """
        if not self.db:
            logger.error("没有设置数据库信息")
            raise (NameError, "没有设置数据库信息")
        # 连接到SQLite数据库
        # 数据库文件是test.db
        # 如果文件不存在，会自动在当前目录创建:
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        if not cur:
            logger.error("连接数据库失败")
            raise (NameError, "连接数据库失败")
        else:
            return conn, cur

    def ExecQuery(self, sql):
        """
        执行查询语句
        返回的是一个包含tuple的list，list的元素是记录行，tuple的元素是每行记录的字段

        调用示例：
                ms = MSSQL(host="localhost",user="sa",pwd="123456",db="PythonWeiboStatistics")
                resList = ms.ExecQuery("SELECT id,NickName FROM WeiBoUser")
                for (id,NickName) in resList:
                    print str(id),NickName
        """

        conn, cur = self.__GetConnect()
        resList = None
        try:
            cur.execute(sql)
            resList = cur.fetchall()
        except Exception as e:
            logger.error("sql执行失败"+ repr(e) + sql)
        finally:
            # 查询完毕后必须关闭连接
            conn.close()
            return resList

    def ExecNonQuery(self, sql):
        """
        执行非查询语句

        调用示例：
            cur = self.__GetConnect()
            cur.execute(sql)
            self.conn.commit()
            self.conn.close()
        """
        conn, cur = self.__GetConnect()
        try:
            cur.execute(sql)
            conn.commit()
        except Exception as e:
            logger.error("sql执行失败" + repr(e) + sql)
        finally:
            conn.close()

    def ExecNoneQueryMulti(self, sqls=list()):
        """
        执行非查询语句，执行事务提交方式
        调用示例：
            cur = self.__GetConnect()
            cur.execute(sql)
            self.conn.commit()
            self.conn.close()

        """
        # 事务处理
        conn, cur = self.__GetConnect()
        currrent_sql = ''
        try:
            for sql in sqls:
                currrent_sql =sql
                cur.execute(sql)
            conn.commit()
            print('事务处理成功', sqls.__len__())
        except Exception as e:
            info = "sql事务执行失败：" + repr(e) + currrent_sql
            conn.rollback()
            logger.error('非预见性异常'+info)
            raise (OSError,'自定义error')
        finally:
            conn.close()





