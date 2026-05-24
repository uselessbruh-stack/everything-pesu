import os
import sqlite3
import logging
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)

# Paths and Keys
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.db")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def is_supabase_enabled() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)

def init_db():
    """Initializes the local SQLite database if Supabase is not configured."""
    if is_supabase_enabled():
        logger.info("Using Supabase as primary database.")
        return

    logger.info(f"Initializing local SQLite database at: {DB_PATH}")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rating INTEGER NOT NULL,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
        logger.info("Local SQLite database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing SQLite database: {e}")

async def get_supabase_client():
    """Returns a client session configured for Supabase REST API."""
    if not is_supabase_enabled():
        return None
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    return httpx.AsyncClient(base_url=SUPABASE_URL, headers=headers)

async def add_rating(rating: int, comment: str = None) -> dict:
    """Adds a new user rating and returns updated statistics."""
    # Validate rating
    if rating < 1 or rating > 5:
        raise ValueError("Rating must be between 1 and 5.")

    created_at = datetime.utcnow().isoformat()

    if is_supabase_enabled():
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "rating": rating,
                    "comment": comment,
                    "created_at": created_at
                }
                # POST to /rest/v1/ratings
                url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/ratings"
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                logger.info("Successfully saved rating to Supabase.")
        except Exception as e:
            logger.error(f"Supabase error adding rating: {e}. Falling back to SQLite/Memory.")
            # Fall through to SQLite if possible
            if not os.path.exists(DB_PATH):
                init_db()
            save_rating_sqlite(rating, comment)
    else:
        save_rating_sqlite(rating, comment)

    return await get_rating_stats()

def save_rating_sqlite(rating: int, comment: str):
    """Synchronously inserts a rating into local SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ratings (rating, comment) VALUES (?, ?)",
            (rating, comment)
        )
        conn.commit()
        conn.close()
        logger.info("Rating saved to SQLite successfully.")
    except Exception as e:
        logger.error(f"SQLite error saving rating: {e}")

async def get_rating_stats() -> dict:
    """Calculates and returns the average rating and count of ratings."""
    ratings_list = []

    if is_supabase_enabled():
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}"
                }
                # Query ratings list (only fetch rating field to keep payload small)
                url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/ratings?select=rating"
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                ratings_list = [r["rating"] for r in data]
                logger.info(f"Fetched {len(ratings_list)} ratings from Supabase.")
        except Exception as e:
            logger.error(f"Supabase error fetching rating stats: {e}. Trying SQLite.")
            ratings_list = get_ratings_sqlite()
    else:
        ratings_list = get_ratings_sqlite()

    total_ratings = len(ratings_list)
    if total_ratings > 0:
        average_rating = round(sum(ratings_list) / total_ratings, 1)
    else:
        average_rating = 0.0

    return {
        "average_rating": average_rating,
        "total_ratings": total_ratings
    }

def get_ratings_sqlite() -> list:
    """Fetches all rating values from the SQLite database."""
    try:
        if not os.path.exists(DB_PATH):
            return []
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT rating FROM ratings")
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"SQLite error fetching ratings: {e}")
        return []

async def save_contact_message(name: str, email: str, message: str) -> None:
    """Saves contact messages for feedback auditing."""
    created_at = datetime.utcnow().isoformat()

    if is_supabase_enabled():
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "name": name,
                    "email": email,
                    "message": message,
                    "created_at": created_at
                }
                url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/contact_messages"
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                logger.info("Saved contact message to Supabase.")
                return
        except Exception as e:
            logger.error(f"Supabase error saving contact: {e}. Trying SQLite.")

    # Fallback to SQLite
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)",
            (name, email, message)
        )
        conn.commit()
        conn.close()
        logger.info("Saved contact message to SQLite.")
    except Exception as e:
        logger.error(f"SQLite error saving contact message: {e}")
