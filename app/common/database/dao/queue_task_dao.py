# coding: utf-8
from .dao_base import DaoBase


class QueueTaskDao(DaoBase):
    """DAO for tbl_download_queue."""

    table = "tbl_download_queue"
    fields = [
        "id", "job_id", "url", "title", "host",
        "format_key", "output_dir", "cookies_file",
        "status", "create_time",
    ]

    def createTable(self) -> bool:
        return self.query.exec(f"""
            CREATE TABLE IF NOT EXISTS {self.table}(
                id          CHAR(32) PRIMARY KEY,
                job_id      TEXT,
                url         TEXT,
                title       TEXT,
                host        TEXT,
                format_key  TEXT,
                output_dir  TEXT,
                cookies_file TEXT,
                status      TEXT,
                create_time TEXT
            )
        """)

    def list_recoverable(self):
        """Return all rows with Pending or Downloading status (to restore on launch)."""
        sql = (
            f"SELECT * FROM {self.table} "
            f"WHERE status = 'Pending' OR status = 'Downloading'"
        )
        if not self.query.exec(sql):
            return []
        return self.iterRecords()
