import sqlite3 as lite

def create_db(river, database):
    con = lite.connect(database)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS {river}(Id INTEGER PRIMARY KEY, timestamp TIMESTAMP UNIQUE, rain FLOAT, level FLOAT, predict FLOAT, forecast FLOAT)".format(river = river))
    con.commit()
    con.close()


if __name__ == "__main__":
    create_db('dart', '../data.db')
    create_db('nevis', '../data.db')
