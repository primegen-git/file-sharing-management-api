from logger import logger
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    load_dotenv()
except Exception as e:
    logger.error(f"Error loading .env file: {e}")
    raise

required_vars = [
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_PORT",
    "POSTGRES_DB",
    "POSTGRES_SERVICE",
]
missing_vars = [var for var in required_vars if os.getenv(var) is None]
if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    raise EnvironmentError(
        f"Missing required environment variables: {', '.join(missing_vars)}"
    )

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_SERVICE = os.getenv("POSTGRES_SERVICE")

SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVICE}:{int(POSTGRES_PORT)}/{POSTGRES_DB}"

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
except Exception as e:
    logger.error(f"Error creating database engine: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close()
