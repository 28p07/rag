import sqlite3
from datetime import datetime,timedelta
utc_now = datetime.utcnow()

# Convert UTC to IST (IST is UTC+5:30)
ist_offset = timedelta(hours=5, minutes=30)
ist_now = utc_now + ist_offset

class DocumentDB:
    def __init__(self):
        self.conn = sqlite3.connect("documents.db", check_same_thread=False)
        self._create_table()
    
    def _create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            page_count INTEGER NOT NULL,
            chunk_count INTEGER NOT NULL,
            upload_time TEXT NOT NULL
        )
        """)
        self.conn.commit()
    
    def add_document(self, metadata: dict):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO documents (filename, page_count, chunk_count, upload_time)
        VALUES (?, ?, ?, ?)
        """, (
            metadata["filename"],
            metadata["page_count"],
            metadata["chunk_count"],
            ist_now.isoformat()
        ))
        self.conn.commit()
    
    def get_document_count(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        return cursor.fetchone()[0]
    
    def get_all_documents(self) -> list:
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT filename, page_count, upload_time 
        FROM documents 
        ORDER BY upload_time DESC
        """)
        return [
            {
                "filename": row[0],
                "page_count": row[1],
                "upload_time": row[2]
            } 
            for row in cursor.fetchall()
        ]
    
    def close(self):
        self.conn.close()

# Singleton instance
db_instance = DocumentDB()

def get_db():
    return db_instance