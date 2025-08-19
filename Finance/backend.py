from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import sqlite3

app = FastAPI(title="Portfolio Backend (SQLite3)")

user_id = 0

DATABASE = "portfolio.db"

# Ensure the table exists
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            quantity REAL NOT NULL,
            avg_cost REAL NOT NULL,
            sector TEXT,
            asset_class TEXT,
            current REAL DEFAULT 0,
            user_id INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Pydantic model for validation
class PortfolioItem(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float
    sector: str
    asset_class: str
    current: Optional[float] = 0.0
    user_id: int

# --- API Endpoints ---

@app.get("/portfolio/", response_model=List[PortfolioItem])
def get_portfolio():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, quantity, avg_cost, sector, asset_class, current, user_id FROM portfolio")
    rows = cursor.fetchall()
    conn.close()

    return [PortfolioItem(
        symbol=row[0],
        quantity=row[1],
        avg_cost=row[2],
        sector=row[3],
        asset_class=row[4],
        current=row[5],
        user_id = row[6]
    ) for row in rows]

@app.post("/portfolio/", response_model=PortfolioItem)
def add_portfolio_item(item: PortfolioItem):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO portfolio (symbol, quantity, avg_cost, sector, asset_class, current, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (item.symbol, item.quantity, item.avg_cost, item.sector, item.asset_class, item.current, item.user_id))
    user_id = item.user_id
    conn.commit()
    conn.close()

    return item

# Temporary for prototype only
@app.delete("/portfolio/")
def clear_portfolio():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM portfolio WHERE user_id = 0")  # remove all rows
    cursor.execute("DELETE FROM strategy1 WHERE user_id = 0")
    conn.commit()
    conn.close()
    return {"message": "Portfolio cleared"}

@app.get("/portfolio/summary/")
def get_portfolio_summary():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Calculate total cost per asset_class
    cursor.execute("""
        SELECT 
            asset_class, 
            SUM(quantity * avg_cost) as pre_total_sum,     
            SUM(quantity * avg_cost) * 100.0 / (SELECT SUM(quantity * avg_cost) FROM portfolio) as pre_asset_allocation,
            SUM(quantity * current) as cur_total_sum,
            SUM(quantity * current) * 100.0 / (SELECT SUM(quantity * current) FROM portfolio) as cur_asset_allocation
        FROM portfolio
        GROUP BY asset_class
    """)
    
    rows = cursor.fetchall()
    conn.close()

    # Return as a list of dicts
    return [{"asset_class": row[0], "pre_total_cost": row[1] ,"pre_asset_allocation": row[2],"cur_total_cost": row[3], "cur_asset_allocation": row[4]} for row in rows]

@app.post("/portfolio/strat1/")
def receive_changes1(changes: Dict[str, float]):
    # You now have the dict from frontend
    # Example: {"Equities": 1234.56, "Bonds": 789.01}
    # print(changes)
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM strategy1 WHERE user_id = ?", (user_id,))
    for asset_class, change in changes.items():
        cursor.execute("""SELECT symbol, quantity, avg_cost, sector, asset_class, current FROM portfolio 
                       WHERE user_id = ? 
                       AND asset_class = ?
                       ORDER BY current/avg_cost DESC""", (user_id, asset_class))
        rows = cursor.fetchall()
        if change > 0:
            cursor.execute("""
                INSERT INTO strategy1 (user_id, ticker, quantity, action, asset_class, current)
                VALUES (?, ?, ?, ?, ?, ?)
                            """, (user_id, rows[-1][0], change/rows[-1][5], 'Buy', asset_class, rows[-1][5]))
        elif change < 0:
            for row in rows:
                if change+row[1]*row[5] > 0:
                    cursor.execute("""
                        INSERT INTO strategy1 (user_id, ticker, quantity, action, asset_class, current)
                        VALUES (?, ?, ?, ?, ?, ?)
                                    """, (user_id, row[0], (-change)/row[5], 'Sell', asset_class, row[5]))
                    break
                change+=row[1]*row[5]
                cursor.execute("""
                        INSERT INTO strategy1 (user_id, ticker, quantity, action, asset_class, current)
                        VALUES (?, ?, ?, ?, ?, ?)
                                    """, (user_id, row[0], row[1], 'Sell', asset_class, row[5]))
    
    

    cursor.execute("SELECT ticker, quantity, action, asset_class, current FROM strategy1 WHERE user_id = ?", (user_id,))
    cols = [col[0] for col in cursor.description]
    strategy_rows = cursor.fetchall()
    conn.commit()
    conn.close()
    return [dict(zip(cols, row)) for row in strategy_rows]

@app.post("/portfolio/strat2/")
def receive_changes2(changes: Dict[str, float]):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM strategy2 WHERE user_id = ?", (user_id,))
    for asset_class, change in changes.items():
        if change == 0:
            continue
        cursor.execute("SELECT SUM(quantity * current) FROM portfolio WHERE user_id = ? AND asset_class = ?", (user_id, asset_class))
        total_cost = cursor.fetchone()[0]
        adjustment_percent = abs(change / total_cost)
        cursor.execute("""SELECT symbol, quantity, current FROM portfolio 
                       WHERE user_id = ? 
                       AND asset_class = ?""", (user_id, asset_class))
        rows = cursor.fetchall()
        action = "Buy" if change > 0 else "Sell"
        for row in rows:
            cursor.execute("""
                INSERT INTO strategy2 (user_id, ticker, quantity, action, asset_class, current)
                VALUES (?, ?, ?, ?, ?, ?)
                            """,(user_id, row[0], row[1] * adjustment_percent, action, asset_class, row[2]))

    cursor.execute("SELECT ticker, quantity, action, asset_class, current FROM strategy2 WHERE user_id = ?", (user_id,))
    cols = [col[0] for col in cursor.description]
    strategy_rows = cursor.fetchall()
    conn.commit()
    conn.close()
    return [dict(zip(cols, row)) for row in strategy_rows]


@app.post("/portfolio/strat3/")
def receive_changes3(changes: Dict[str, float]):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM strategy3 WHERE user_id = ?", (user_id,))
    for asset_class, change in changes.items():
        the_plan_in_strategy_3 = {}
        cursor.execute("""SELECT symbol, quantity, current FROM portfolio 
                       WHERE user_id = ? 
                       AND asset_class = ?
                       ORDER BY current/avg_cost DESC""", (user_id, asset_class))
        rows = cursor.fetchall()
        if change < 0:
            for row in rows:
                if change+row[1]*row[2]/2 > 0:
                    the_plan_in_strategy_3[row[0]] = [-change/row[2], 'Sell', row[2]]
                    change=0
                    break
                change+=row[1]*row[2]/2
                the_plan_in_strategy_3[row[0]] = [row[1]/2, 'Sell', row[2]]

        cursor.execute("SELECT SUM(quantity * current) FROM portfolio WHERE user_id = ? AND asset_class = ?", (user_id, asset_class))
        if change != 0:
            total_cost = cursor.fetchone()[0]
            adjustment_percent = abs(change / total_cost)
            print(asset_class, change, adjustment_percent)
            for row in rows:
                
                if row[0] in the_plan_in_strategy_3:
                    the_plan_in_strategy_3[row[0]][0] += (row[1]-the_plan_in_strategy_3[row[0]][0]) * adjustment_percent
                    print(row[1]-the_plan_in_strategy_3[row[0]][0], '-')
                else:
                    the_plan_in_strategy_3[row[0]] = [row[1] * adjustment_percent, "Buy" if change > 0 else "Sell", row[2]]
                    print(row[1])
        
        for key, value in the_plan_in_strategy_3.items():
            cursor.execute("""INSERT INTO strategy3 (user_id, ticker, quantity, action, asset_class, current)
                           VALUES (?, ?, ?, ?, ?, ?)
                           """, (user_id, key, value[0], value[1], asset_class, value[2]))

    cursor.execute("SELECT ticker, quantity, action, asset_class, current FROM strategy3 WHERE user_id = ?", (user_id,))
    cols = [col[0] for col in cursor.description]
    strategy_rows = cursor.fetchall()
    conn.commit()
    conn.close()
    return [dict(zip(cols, row)) for row in strategy_rows]