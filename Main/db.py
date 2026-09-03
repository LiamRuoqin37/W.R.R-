import psycopg2
from psycopg2.extras import RealDictCursor
import os

#Database connection and configuration. Reliant on .env file.


from dotenv import load_dotenv  #Library that read .env file and loads it into the enviornment so os.getnv can grab the values
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database" : os.getenv("DB_NAME"),
    "user":os.getenv("DB_USER"),
    "password":os.getenv("DB_PASSWORD")
}


def get_db():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn