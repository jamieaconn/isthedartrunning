import sqlite3 as lite

def create_db(river, database):
    con = lite.connect(database)
    cur = con.cursor()
    cur.execute("CREATE TABLE {river}(Id INTEGER PRIMARY KEY, timestamp TIMESTAMP UNIQUE, rain FLOAT, level FLOAT, predict FLOAT)".format(river = river))
    con.commit()
    con.close()


if __name__ == "__main__":
    create_db('dart', 'data.db')
