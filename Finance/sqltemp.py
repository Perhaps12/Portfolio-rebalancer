import sqlite3

DATABASE = "portfolio.db"

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()
cursor.execute("""
               DELETE FROM strategy
""")
cursor.execute("""
               DELETE FROM portfolio
""")

# for i in range(128):
#     cursor.execute("""
#         INSERT INTO account (id)
#         VALUES (?)
#                 """, (i,))
conn.commit()
conn.close()