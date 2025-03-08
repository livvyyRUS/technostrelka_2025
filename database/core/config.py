import os
import dotenv

dotenv.load_dotenv("config.env")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite://tmdb_database.db")
