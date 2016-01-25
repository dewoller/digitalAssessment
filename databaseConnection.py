

import sqlite3
import os
sqlite_file = '/tmp/digitalMarking.db'    # name of the sqlite database file

class databaseConnection:

    def __init__(self):
        self.conn=None

    def connect(self):
        if not os.path.isfile( sqlite_file ):
            self.createDB()

        self.conn = sqlite3.connect(sqlite_file)
        return self.conn.cursor()


    def disconnect(self):
        # Committing changes and closing the connection to the database file
        self.conn.commit()
        self.conn.close()
        return

    def setPersistant( self, row ):
        c=self.connect()
        c.execute("""
        INSERT OR IGNORE 
        INTO persistant 
        (key, id) 
        VALUES (1, :id)
        """, {"id": row} )
        self.disconnect()
        return


    def getPersistant(self ):
        c=self.connect()
        c.execute("""
        SELECT id
        from persistant 
        where key=1
        """)
        all_rows = c.fetchall()
        self.disconnect()
        return all_rows


    def createDB(self):
        self.conn = sqlite3.connect(sqlite_file)
        c = self.conn.cursor()
        c.execute(
            """
            CREATE TABLE persistant (
            key integer primary key,
            sfile text, 
            afile text,
            id text
            )
        """ )
        c.execute(
            """
            insert into persistant (key) values (1)
            )
            """
        )
        self.conn.commit()
        self.conn.close()

