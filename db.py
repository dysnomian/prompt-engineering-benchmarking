import os

from pymongo import MongoClient

MONGODB_URI = os.getenv("BENCHMARKS_MONGODB_URI")
MONGODB_DB_NAME = os.getenv(
    "BENCHMARKS_MONGODB_DB_NAME", "prompt-engineering-benchmarks"
)
MONGODB_PORT = int(os.getenv("BENCHMARKS_MONGODB_PORT", "27017"))

DB_CLIENT = MongoClient(MONGODB_URI, MONGODB_PORT)
DB = DB_CLIENT[MONGODB_DB_NAME]
