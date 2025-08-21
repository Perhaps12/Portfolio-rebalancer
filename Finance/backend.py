from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
import sqlite3
from transformers import pipeline

app = FastAPI(title="Portfolio Backend (SQLite3)")

generator = pipeline("text2text-generation", model="google/flan-t5-base")

DATABASE = "portfolio.db"

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
    conn.commit()
    conn.close()

    return item

# Temporary for prototype only
@app.delete("/portfolio/")
def clear_portfolio(user_id: int):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM portfolio WHERE user_id = ?", (user_id,))  # remove all rows
    conn.commit()
    conn.close()
    return {"message": "Portfolio cleared"}

@app.get("/portfolio/summary/")
def get_portfolio_summary(user_id):
    # print(user_id)
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Calculate total cost per asset_class
    cursor.execute("""
        SELECT 
            asset_class, 
            SUM(quantity * avg_cost) as pre_total_sum,     
            SUM(quantity * avg_cost) * 100.0 / (SELECT SUM(quantity * avg_cost) FROM portfolio WHERE user_id = ?) as pre_asset_allocation,
            SUM(quantity * current) as cur_total_sum,
            SUM(quantity * current) * 100.0 / (SELECT SUM(quantity * current) FROM portfolio WHERE user_id = ?) as cur_asset_allocation
        FROM portfolio
        WHERE user_id = ?
        GROUP BY asset_class
    """, (user_id, user_id, user_id))
    
    rows = cursor.fetchall()
    conn.close()

    # Return as a list of dicts
    return [{"asset_class": row[0], "pre_total_cost": row[1] ,"pre_asset_allocation": row[2],"cur_total_cost": row[3], "cur_asset_allocation": row[4]} for row in rows]

@app.post("/portfolio/strat1/")
def receive_changes1(changes: Dict[str, float]):
    user_id = changes['user_id']
    # You now have the dict from frontend
    # Example: {"Equities": 1234.56, "Bonds": 789.01}
    # print(changes)
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    if user_id == 0:
        cursor.execute("DELETE FROM strategy WHERE user_id = 0 AND strategy = 1")
    cursor.execute("SELECT MAX(version) FROM strategy WHERE user_id = ? AND strategy = 1", (user_id,))
    version = cursor.fetchone()
    version = version[0]+1 if version and version[0] is not None else 0

    for asset_class, change in changes.items():
        if asset_class == 'user_id':
            continue
        cursor.execute("""SELECT symbol, quantity, avg_cost, sector, asset_class, current FROM portfolio 
                       WHERE user_id = ? 
                       AND asset_class = ?
                       ORDER BY current/avg_cost DESC""", (user_id, asset_class))
        rows = cursor.fetchall()
        if change > 0:
            cursor.execute("""
                INSERT INTO strategy (user_id, ticker, quantity, action, asset_class, current, strategy, version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (user_id, rows[-1][0], change/rows[-1][5], 'Buy', asset_class, rows[-1][5],1,version))
        elif change < 0:
            for row in rows:
                if change+row[1]*row[5] > 0:
                    cursor.execute("""
                        INSERT INTO strategy (user_id, ticker, quantity, action, asset_class, current, strategy, version)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (user_id, row[0], (-change)/row[5], 'Sell', asset_class, row[5],1,version))
                    break
                change+=row[1]*row[5]
                cursor.execute("""
                        INSERT INTO strategy (user_id, ticker, quantity, action, asset_class, current, strategy, version)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (user_id, row[0], row[1], 'Sell', asset_class, row[5],1,version))
    
    

    cursor.execute("SELECT ticker, quantity, action, asset_class, current FROM strategy WHERE user_id = ? AND strategy = 1 AND version = ?", (user_id,version))
    cols = [col[0] for col in cursor.description]
    strategy_rows = cursor.fetchall()
    conn.commit()
    conn.close()
    return [dict(zip(cols, row)) for row in strategy_rows]

@app.post("/portfolio/strat2/")
def receive_changes2(changes: Dict[str, float]):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    user_id = changes['user_id']
    
    if user_id == 0:
        cursor.execute("DELETE FROM strategy WHERE user_id = ? AND strategy = 2", (user_id,))
    cursor.execute("SELECT MAX(version) FROM strategy WHERE user_id = ? AND strategy = 2", (user_id,))
    version = cursor.fetchone()
    version = version[0]+1 if version and version[0] is not None else 0
    for asset_class, change in changes.items():
        if asset_class == 'user_id':
            continue
        if change == 0:
            continue
        cursor.execute("SELECT SUM(quantity * current) FROM portfolio WHERE user_id = ? AND asset_class = ?", (user_id, asset_class))
        total_cost = cursor.fetchone()[0]
        print(asset_class, total_cost)
        adjustment_percent = abs(change / total_cost)
        cursor.execute("""SELECT symbol, quantity, current FROM portfolio 
                       WHERE user_id = ? 
                       AND asset_class = ?""", (user_id, asset_class))
        rows = cursor.fetchall()
        action = "Buy" if change > 0 else "Sell"
        for row in rows:
            cursor.execute("""
                INSERT INTO strategy (user_id, ticker, quantity, action, asset_class, current, strategy, version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,(user_id, row[0], row[1] * adjustment_percent, action, asset_class, row[2], 2, version))

    cursor.execute("SELECT ticker, quantity, action, asset_class, current FROM strategy WHERE user_id = ? AND version = ? AND strategy = 2", (user_id,version))
    cols = [col[0] for col in cursor.description]
    strategy_rows = cursor.fetchall()
    conn.commit()
    conn.close()
    return [dict(zip(cols, row)) for row in strategy_rows]

@app.post("/portfolio/strat3/")
def receive_changes3(changes: Dict[str, float]):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    user_id = changes['user_id']
    
    if user_id == 0:
        cursor.execute("DELETE FROM strategy WHERE user_id = ? AND strategy = 3", (user_id,))
    cursor.execute("SELECT MAX(version) FROM strategy WHERE user_id = ? AND strategy = 3", (user_id,))
    version = cursor.fetchone()
    version = version[0]+1 if version and version[0] is not None else 0

    for asset_class, change in changes.items():
        if asset_class == 'user_id':
            continue
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
            cursor.execute("""INSERT INTO strategy (user_id, ticker, quantity, action, asset_class, current, strategy, version)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                           """, (user_id, key, value[0], value[1], asset_class, value[2], 3, version))

    cursor.execute("SELECT ticker, quantity, action, asset_class, current FROM strategy WHERE user_id = ? AND strategy = 3 AND version = ?", (user_id,version))
    cols = [col[0] for col in cursor.description]
    strategy_rows = cursor.fetchall()
    conn.commit()
    conn.close()
    return [dict(zip(cols, row)) for row in strategy_rows]

@app.get("/portfolio/extract/")
def extract_existing_data(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, quantity, avg_cost, sector, asset_class FROM portfolio WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{'symbol': row[0], 'quantity': row[1], 'avg_cost': row[2], 'sector': row[3], 'asset_class': row[4]} for row in rows]

@app.post("/portfolio/stratAI")
def what_if_we_asked_ai(changes: Dict[str, float]):
    user_id = changes['user_id']
    prompt = "Task: Suggest specific buy/sell stock actions for this user based on their portfolio.\n\nChanges:\n"
    for asset_class, change in changes.items():
        if asset_class == "user_id" or change == 0:
            continue
        prompt += f" - {asset_class}: {'+' if change>0 else '-'}${abs(change)}\n"
    conn = sqlite3.connect(DATABASE)
    prompt += "\nPortfolio:\n"
    cursor = conn.cursor()
    cursor.execute("""SELECT symbol, quantity, asset_class, current FROM portfolio WHERE user_id = ?
                    """, (user_id,))
    rows = cursor.fetchall()
    for row in rows:
        prompt += f" - {row[0]}: {row[1]} shares @ ${row[3]} ({row[2]})\n"
    prompt += (
        "\n\nInstruction: Recommend specific trades for the user. Format as action, quantity, symbol"
    )
    print(prompt)
    conn.close()
    result = generator(
        prompt,
        do_sample=True,           # add randomness
        top_k=50,                 # limit sampling pool
        top_p=0.9,                # nucleus sampling
        repetition_penalty=1.2,   # discourage repeats
        temperature=0.7           # softer randomness
    )[0]['generated_text']
    return {'response': result}