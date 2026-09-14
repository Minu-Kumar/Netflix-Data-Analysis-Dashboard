import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# Read CSV
df = pd.read_csv("data/netflix_titles.csv", encoding="latin1")


print(df.head())

# MySQL Connection
connection_url = URL.create(
    drivername="mysql+pymysql",
    username="root",
    password="Minu@87894",
    host="localhost",
    port=3306,
    database="netflix"
)

engine = create_engine(connection_url)

# Upload to MySQL
df.to_sql(
    "netflix_titles",
    con=engine,
    if_exists="replace",
    index=False
)

print("✅ Netflix data uploaded successfully!")