from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Get MySQL connection details from environment variables
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

# Debug print
print("Database connection details:")
print(f"Host: {MYSQL_HOST}")
print(f"Database: {MYSQL_DATABASE}")
print(f"User: {MYSQL_USER}")
print(f"Password: {'*' * len(MYSQL_PASSWORD) if MYSQL_PASSWORD else 'Not set'}")

# Validate required environment variables
required_vars = ["MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_HOST", "MYSQL_DATABASE"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}"

print(f"Connection URL: mysql+mysqlconnector://{MYSQL_USER}:****@{MYSQL_HOST}/{MYSQL_DATABASE}")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Enable automatic reconnection
    pool_recycle=3600,  # Recycle connections after 1 hour
    connect_args={
        "connect_timeout": 30  # 30 second timeout
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 