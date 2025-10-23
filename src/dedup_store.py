import aiosqlite
import asyncio
import logging
from pathlib import Path
from typing import Optional, Set, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class DedupStore:
    
    def __init__(self, db_path: str = "data/dedup.db"):
        self.db_path = db_path
        self._ensure_data_dir()
        self._lock = asyncio.Lock()
        logger.info(f"DedupStore initialized with database: {db_path}")
    
    def _ensure_data_dir(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS processed_events (
                    topic TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    source TEXT NOT NULL,
                    processed_at TEXT NOT NULL,
                    PRIMARY KEY (topic, event_id)
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_topic 
                ON processed_events(topic)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_at 
                ON processed_events(processed_at)
            """)
            
            await db.commit()
        
        logger.info("DedupStore database initialized")
    
    async def is_duplicate(self, topic: str, event_id: str) -> bool:
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT 1 FROM processed_events WHERE topic = ? AND event_id = ? LIMIT 1",
                    (topic, event_id)
                )
                result = await cursor.fetchone()
                return result is not None
    
    async def mark_processed(
        self, 
        topic: str, 
        event_id: str, 
        timestamp: str, 
        source: str
    ) -> bool:
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                try:
                    processed_at = datetime.utcnow().isoformat()
                    await db.execute(
                        """
                        INSERT INTO processed_events 
                        (topic, event_id, timestamp, source, processed_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (topic, event_id, timestamp, source, processed_at)
                    )
                    await db.commit()
                    return True
                except aiosqlite.IntegrityError:
                    return False
    
    async def get_processed_count(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM processed_events")
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def get_topics(self) -> List[str]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT DISTINCT topic FROM processed_events ORDER BY topic"
            )
            results = await cursor.fetchall()
            return [row[0] for row in results]
    
    async def get_events_by_topic(
        self, 
        topic: str, 
        limit: Optional[int] = None
    ) -> List[Tuple[str, str, str, str]]:
        query = """
            SELECT event_id, timestamp, source, processed_at 
            FROM processed_events 
            WHERE topic = ? 
            ORDER BY processed_at DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, (topic,))
            return await cursor.fetchall()
    
    async def get_count_by_topic(self, topic: str) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM processed_events WHERE topic = ?",
                (topic,)
            )
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def cleanup_old_events(self, days: int = 30):
        cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_iso = cutoff.isoformat()
        
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "DELETE FROM processed_events WHERE processed_at < ?",
                    (cutoff_iso,)
                )
                deleted = cursor.rowcount
                await db.commit()
                
                if deleted > 0:
                    logger.info(f"Cleaned up {deleted} old events (older than {days} days)")
