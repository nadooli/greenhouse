
import sqlite3
import logging

logger = logging.getLogger("db")


class Database:
    
    def __init__(self, connection_string="./db/greenhouse.db"):
        self._conn=sqlite3.connect(connection_string)
        self._cursor=self._conn.cursor()
    
    def __enter__(self):        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    
    @property
    def connection(self):
        return self._conn
    
    @property
    def cursor(self):
        return self._cursor
    
    def commit(self):
        self.connection.commit()
        
    def close(self, commit=True):
        if commit:
            self.commit()
        self.connection.close()
        
    def execute(self, sql, params=None):
        self.cursor.execute(sql, params or ())
        
    def fetchall(self):
        return self.cursor.fetchall()
    
    def fetchone(self):
        return self.cursor.fetchone()
    
    def query(self, sql, params=None):
        self.cursor.execute(sql, params or ())
        return self.fetchall()
    
    def query_one(self, sql, params=None):
        self.cursor.execute(sql, params or ())
        return self.fetchone()
    

