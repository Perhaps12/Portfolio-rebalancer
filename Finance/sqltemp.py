import sqlite3

DATABASE = "portfolio.db"

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS portfolio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol INTEGER NOT NULL,
        quantity INT NOT NULL,
        avg_cost INT NOT NULL,
        sector TEXT NOT NULL,
        asset_class FLOAT NOT NULL,
        current TEXT NOT NULL,
        user_id TEXT NOT NULL 
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS strategy (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        strategy INT NOT NULL,
        version INT NOT NULL,
        ticker TEXT NOT NULL,
        quantity FLOAT NOT NULL,
        action TEXT NOT NULL,
        asset_class TEXT NOT NULL,
        current FLOAT NOT NULL    
    )
""")

# for i in range(128):
#     cursor.execute("""
#         INSERT INTO account (id)
#         VALUES (?)
#                 """, (i,))
conn.commit()
conn.close()