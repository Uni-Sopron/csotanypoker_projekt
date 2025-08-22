import sqlite3

conn = sqlite3.connect("game.db")
with open("insert_rooms_data.sql", "r") as f:
    conn.executescript(f.read())
conn.close()
