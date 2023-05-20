"""
@author: Arno
@created: 2022-11-03
@modified: 2023-05-20

Database Helper Utilities Class

"""
from abc import ABC, abstractmethod


class Db(ABC):
    """Abstract Class for database actions

    constructor:
        config(Dict): Database connection params
    """

    def __init__(self, config: dict):
        self.conn = None
        self.config = config

    def __enter__(self):
        try:
            self.open()
        except:
            self.create_db()
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        if self.conn:
            self.commit()
            self.conn.close()
            self.conn = None

    def create_db(self):
        """Function to create and open a connection to the database

        To be implemented if possible, 
        Otherwise calling this method will result in a runtime error
        """
        raise RuntimeError('Unable to create database in runtime')

    @abstractmethod
    def open(self):
        """Function to open a connection to the database
        """
        pass

    @abstractmethod
    def get_query_check_table(self) -> str:
        """Get the query for check if table exists in database
        """
        pass

    def check_table(self, table_name: str) -> bool:
        """Check if table exists in database
        """
        if self.conn is None:
            raise RuntimeError('Database not connected')

        if table_name is None:
            return False

        query_chk_table = self.get_query_check_table()
        if self.query(query_chk_table, (table_name,)):
            # table exists
            #print(f'"{table_name}" table exist')
            return True

        #print(f'"{table_name}" table not exist.')
        return False

    def check_db(self) -> bool:
        """Check wether the database exists and can be opened or created

        Database can be created in case of sqlite3
        """
        if self.conn is None:
            try:
                self.open()
            except RuntimeError as e:
                pass

        if self.conn is None:
            try:
                self.create_db()
            except Exception as e:
                print(e)
                raise  # todo

        if self.conn is not None:
            # Database exists
            return True

        return False

    @abstractmethod
    def get_execute_result(self, cursor) -> int:
        """Get result from executing a query

        return value = rowcount or total changes
        """
        pass

    def execute(self, sql: str, params=None) -> int:
        """Execute a query

        Executes a query and returns number of rows or number of changes
        For SQLite cursor.rowcount doesn't exists

        sql = query to execute,
        params = dictionary for parameters in query
        return value = rowcount or total changes
        """
        #print('Execute:', sql, params)
        cursor = self.conn.cursor()  # type: ignore
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        result = self.get_execute_result(cursor)
        cursor.close()
        return result

    def query(self, sql: str, params=None):
        """Execute a query and returns the result

        sql = query to execute,
        params = dictionary for parameters in query
        return value = fetched data from query
        """
        #print('Query:', sql, params)
        cursor = self.conn.cursor()  # type: ignore
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def commit(self):
        self.conn.commit()  # type: ignore

    def rollback(self):
        self.conn.rollback()  # type: ignore

    def has_connection(self):
        return self.conn != None

    @abstractmethod
    def get_create_primary_key_str(self) -> str:
        """Get the string to create a primary key for the specific database type

        Normally: primary_key = 'INT AUTO_INCREMENT PRIMARY KEY'
        """
        pass
