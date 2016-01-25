
import sqlite3
sqlite_file = 'digitalMarking.db'    # name of the sqlite database file
table_name1 = 'persistant'  # name of the table to be created
table_name2 = 'errors'  # name of the table to be created

conn=None

def connect():
  conn = sqlite3.connect(sqlite_file)
  return conn.cursor()


def disconnect():
# Committing changes and closing the connection to the database file
  conn.commit()
  conn.close()
  return

def setPersistant( row ):
  c=connect()
  c.execute("""
  INSERT OR IGNORE 
  INTO persistant 
  (key, afile, sfile, id) 
  VALUES (1, {key}, {afile}, {sfile})
  """.format(afile = row['afile'], sfile=row['sfile'], id=row['id'])  )
  disconnect()
  return


def getPersistant( ):
  c=connect()
  c.execute("""
  SELECT key, afile, sfile
  from persistant 
  where key=1
  """)
  all_rows = c.fetchall()
  disconnect()
  return all_rows


def createDB():
  c=connect()
  # Creating a new SQLite table with 1 column
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

  disconnect()
