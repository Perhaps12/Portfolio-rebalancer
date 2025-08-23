**Stock portfolio rebalancer**  
Input / upload your portfolio and recieve an overview of the percentage allocation grouped by asset class (Bond, Equity, Commodity, etc.)  
Once the allocation summary is displayed, input the target allocation per asset class and recieve 3.1* suggestions on what stocks to buy/sell to achieve the target.  
*There are 3 actual strategies provided and an AI 'suggestion' however the model used (google flan t5) rarely provides satisfactory responses

**Features**  
- Data stored and retrieved via SQL database
- Ability to both manually input stocks or upload a csv file
    - csv file must contain headers of symbol (ticker symbol), quantity (# of stocks purchased), avg_cost (Price per share when it was bought), sector, asset class
- Storage over multiple sessions through the use of user ids
    - default user id 0 resets every use and is intended as a very temporary consultation
    - all other user ids store past data in the database an can be reaccessed of the user logs into the same user id
 
**How to use**  
Download all the files, run "streamlit run frontend.py" to create the frontend webpage on the local host and  
"uvicorn backend:app --reload" to start the backend server  
The existing portfolio.db file has some portfolios already stored in it for testing, simply just delete the file and run sqltemp.py in order to effectively clear the existing data  
Some sample csv files have been provided 

**Required libraries**
- fastapi + uvicorn + pydantic
- transformers + torch
- streamlit
- pandas
- matplotlib
- yfinance
