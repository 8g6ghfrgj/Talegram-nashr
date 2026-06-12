import sqlite3
import threading
from datetime import datetime
from typing import List, Tuple, Optional, Any


DB_NAME = "bot_database.db"


class BotDatabase:
    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name
        self.lock = threading.RLock()

        self.conn = sqlite3.connect(
            self.db_name,
            check_same_thread=False,
            timeout=30,
        )
        self.conn.row_factory = sqlite3.Row

        self._setup_database()
        self._create_tables()
        self._create_indexes()

    # ==================================================
    # SETUP
    # ==================================================

    def _setup_database(self):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA synchronous = NORMAL")
            self.conn.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    # ==================================================
    # CREATE TABLES
    # ==================================================

    def _create_tables(self):
        with self.lock:
            cursor = self.conn.cursor()

            # ---------- ADMINS ----------
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY,
                username TEXT,
                role TEXT,
                active INTEGER DEFAULT 1,
                added_at TEXT
            )
            """)

            # ---------- ACCOUNTS ----------
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                session TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                added_at TEXT
            )
            """)

            # ---------- ADS ----------
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                type TEXT NOT NULL,
                text TEXT,
                media_path TEXT,
                active INTEGER DEFAULT 1,
                added_at TEXT
            )
            """)

            # ---------- GROUPS ----------
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                link TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                added_at TEXT
            )
            """)

            # ---------- PRIVATE REPLIES ----------
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS private_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                text TEXT NOT NULL,
                added_at TEXT
            )
            """)

            # ---------- RANDOM REPLIES ----------
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS random_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                type TEXT NOT NULL,
                text TEXT,
                media_path TEXT,
                added_at TEXT
            )
            """)

            self.conn.commit()

    def _create_indexes(self):
        """
        فهارس لتحسين سرعة الاستعلامات بدون تغيير شكل الجداول.
        """
        with self.lock:
            cursor = self.conn.cursor()

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_admin_id ON accounts(admin_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ads_admin_id ON ads(admin_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_groups_admin_id ON groups(admin_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_private_replies_admin_id ON private_replies(admin_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_random_replies_admin_id ON random_replies(admin_id)")

            self.conn.commit()

    # ==================================================
    # HELPERS
    # ==================================================

    def _fetchall(self, query: str, params: Tuple[Any, ...] = ()) -> List[sqlite3.Row]:
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def _fetchone(self, query: str, params: Tuple[Any, ...] = ()) -> Optional[sqlite3.Row]:
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()

    # ==================================================
    # ADMINS
    # ==================================================

    def add_admin(self, admin_id: int, username: str, role: str, active: bool = True):
        if not isinstance(admin_id, int) or admin_id <= 0:
            return False, "Invalid admin_id"

        username = username or "admin"
        role = role or "مشرف"

        try:
            with self.lock:
                cursor = self.conn.cursor()

                existing = self._fetchone(
                    "SELECT id FROM admins WHERE id=?",
                    (admin_id,),
                )

                if existing:
                    return False, "Admin already exists"

                cursor.execute("""
                INSERT INTO admins (id, username, role, active, added_at)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    admin_id,
                    username,
                    role,
                    1 if active else 0,
                    self._now(),
                ))

                self.conn.commit()
                return True, "OK"

        except Exception as e:
            self.conn.rollback()
            return False, str(e)

    def is_admin(self, admin_id: int) -> bool:
        if not isinstance(admin_id, int) or admin_id <= 0:
            return False

        row = self._fetchone(
            "SELECT id FROM admins WHERE id=? AND active=1",
            (admin_id,),
        )
        return row is not None

    def get_admins(self) -> List[sqlite3.Row]:
        return self._fetchall("SELECT * FROM admins ORDER BY added_at DESC")

    def delete_admin(self, admin_id: int):
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM admins WHERE id=?", (admin_id,))
                self.conn.commit()
                return cursor.rowcount > 0
        except Exception:
            self.conn.rollback()
            return False

    # ==================================================
    # ACCOUNTS
    # ==================================================

    def add_account(self, admin_id: int, session: str):
        if not isinstance(admin_id, int) or admin_id <= 0:
            return False, "Invalid admin_id"

        if not session or not isinstance(session, str):
            return False, "Invalid session"

        try:
            with self.lock:
                cursor = self.conn.cursor()

                cursor.execute("""
                INSERT INTO accounts (admin_id, session, active, added_at)
                VALUES (?, ?, 1, ?)
                """, (
                    admin_id,
                    session,
                    self._now(),
                ))

                self.conn.commit()
                return True, "OK"

        except Exception as e:
            self.conn.rollback()
            return False, str(e)

    def get_accounts(self, admin_id: int = None):
        if admin_id is not None:
            return self._fetchall(
                "SELECT * FROM accounts WHERE admin_id=? ORDER BY added_at DESC",
                (admin_id,),
            )

        return self._fetchall("SELECT * FROM accounts ORDER BY added_at DESC")

    def get_account(self, account_id: int):
        return self._fetchone(
            "SELECT * FROM accounts WHERE id=?",
            (account_id,),
        )

    def toggle_account_status(self, account_id: int, admin_id: int = None):
        try:
            with self.lock:
                cursor = self.conn.cursor()

                if admin_id is not None:
                    cursor.execute("""
                    UPDATE accounts
                    SET active = CASE WHEN active=1 THEN 0 ELSE 1 END
                    WHERE id=? AND admin_id=?
                    """, (account_id, admin_id))
                else:
                    cursor.execute("""
                    UPDATE accounts
                    SET active = CASE WHEN active=1 THEN 0 ELSE 1 END
                    WHERE id=?
                    """, (account_id,))

                self.conn.commit()
                return cursor.rowcount > 0

        except Exception:
            self.conn.rollback()
            return False

    def delete_account(self, account_id: int, admin_id: int = None):
        try:
            with self.lock:
                cursor = self.conn.cursor()

                if admin_id is not None:
                    cursor.execute(
                        "DELETE FROM accounts WHERE id=? AND admin_id=?",
                        (account_id, admin_id),
                    )
                else:
                    cursor.execute(
                        "DELETE FROM accounts WHERE id=?",
                        (account_id,),
                    )

                self.conn.commit()
                return cursor.rowcount > 0

        except Exception:
            self.conn.rollback()
            return False

    def update_account_session(self, account_id: int, session: str):
        if not session or not isinstance(session, str):
            return False

        try:
            with self.lock:
                cursor = self.conn.cursor()

                cursor.execute("""
                UPDATE accounts
                SET session=?
                WHERE id=?
                """, (session, account_id))

                self.conn.commit()
                return cursor.rowcount > 0

        except Exception:
            self.conn.rollback()
            return False

    # ==================================================
    # ADS
    # ==================================================

    def add_ad(self, admin_id: int, ad_type: str, text: str, media_path: str = None):
        if not isinstance(admin_id, int) or admin_id <= 0:
            return False, "Invalid admin_id"

        if ad_type not in ("text", "photo", "contact"):
            return False, "Invalid ad_type"

        text = text or ""

        try:
            with self.lock:
                cursor = self.conn.cursor()

                cursor.execute("""
                INSERT INTO ads (admin_id, type, text, media_path, active, added_at)
                VALUES (?, ?, ?, ?, 1, ?)
                """, (
                    admin_id,
                    ad_type,
                    text,
                    media_path,
                    self._now(),
                ))

                self.conn.commit()
                return True, "OK"

        except Exception as e:
            self.conn.rollback()
            return False, str(e)

    def get_ads(self, admin_id: int = None):
        if admin_id is not None:
            return self._fetchall(
                "SELECT * FROM ads WHERE admin_id=? ORDER BY added_at DESC",
                (admin_id,),
            )

        return self._fetchall("SELECT * FROM ads ORDER BY added_at DESC")

    def get_ad(self, ad_id: int):
        return self._fetchone(
            "SELECT * FROM ads WHERE id=?",
            (ad_id,),
        )

    def toggle_ad_status(self, ad_id: int, admin_id: int = None):
        try:
            with self.lock:
                cursor = self.conn.cursor()

                if admin_id is not None:
                    cursor.execute("""
                    UPDATE ads
                    SET active = CASE WHEN active=1 THEN 0 ELSE 1 END
                    WHERE id=? AND admin_id=?
                    """, (ad_id, admin_id))
                else:
                    cursor.execute("""
                    UPDATE ads
                    SET active = CASE WHEN active=1 THEN 0 ELSE 1 END
                    WHERE id=?
                    """, (ad_id,))

                self.conn.commit()
                return cursor.rowcount > 0

        except Exception:
            self.conn.rollback()
            return False

    def delete_ad(self, ad_id: int, admin_id: int = None):
        try:
            with self.lock:
                cursor = self.conn.cursor()

                if admin_id is not None:
                    cursor.execute(
                        "DELETE FROM ads WHERE id=? AND admin_id=?",
                        (ad_id, admin_id),
                    )
                else:
                    cursor.execute(
                        "DELETE FROM ads WHERE id=?",
                        (ad_id,),
                    )

                self.conn.commit()
                return cursor.rowcount > 0

        except Exception:
            self.conn.rollback()
            return False

    # ==================================================
    # GROUPS
    # ==================================================

    def add_group(self, admin_id: int, link: str):
        if not isinstance(admin_id, int) or admin_id <= 0:
            return False, "Invalid admin_id"

        if not link or not isinstance(link, str):
            return False, "Invalid link"

        try:
            with self.lock:
                cursor = self.conn.cursor()

                cursor.execute("""
                INSERT INTO groups (admin_id, link, status, added_at)
                VALUES (?, ?, 'active', ?)
                """, (
                    admin_id,
                    link,
                    self._now(),
                ))

                self.conn.commit()
                return True, "OK"

        except Exception as e:
            self.conn.rollback()
            return False, str(e)

    def get_groups(self, admin_id: int = None):
        if admin_id is not None:
            return self._fetchall(
                "SELECT * FROM groups WHERE admin_id=? ORDER BY added_at DESC",
                (admin_id,),
            )

        return self._fetchall("SELECT * FROM groups ORDER BY added_at DESC")

    def get_group(self, group_id: int):
        return self._fetchone(
            "SELECT * FROM groups WHERE id=?",
            (group_id,),
        )

    def toggle_group_status(self, group_id: int, admin_id: int = None):
        try:
            with self.lock:
                cursor = self.conn.cursor()

                if admin_id is not None:
                    cursor.execute("""
                    UPDATE groups
                    SET status = CASE WHEN status='active' THEN 'inactive' ELSE 'active' END
                    WHERE id=? AND admin_id=?
                    """, (group_id, admin_id))
                else:
                    cursor.execute("""
                    UPDATE groups
                    SET status = CASE WHEN status='active' THEN 'inactive' ELSE 'active' END
                    WHERE id=?
                    """, (group_id,))

                self.conn.commit()
                return cursor.rowcount > 0

        except Exception:
            self.conn.rollback()
            return False

    def delete_group(self, group_id: int, admin_id: int = None):
        try:
            with self.lock:
                cursor = self.conn.cursor()

                if admin_id is not None:
                    cursor.execute(
                        "DELETE FROM groups WHERE id=? AND admin_id=?",
                        (group_id, admin_id),
                    )
                else:
                    cursor.execute(
                        "DELETE FROM groups WHERE id=?",
                        (group_id,),
                    )

                self.conn.commit()
                return cursor.rowcount > 0

        except Exception:
            self.conn.rollback()
            return False

    # ==================================================
    # PRIVATE REPLIES
    # ==================================================

    def add_private_reply(self, admin_id: int, text: str):
        if not isinstance(admin_id, int) or admin_id <= 0:
            return False

        if not text or not isinstance(text, str):
            return False

        try:
            with self.lock:
                cursor = self.conn.cursor()

                cursor.execute("""
                INSERT INTO private_replies (admin_id, text, added_at)
                VALUES (?, ?, ?)
                """, (
                    admin_id,
                    text,
                    self._now(),
                ))

                self.conn.commit()
                return True

        except Exception:
            self.conn.rollback()
            return False

    def get_private_replies(self, admin_id: int = None):
        if admin_id is not None:
            return self._fetchall(
                "SELECT * FROM private_replies WHERE admin_id=? ORDER BY added_at DESC",
                (admin_id,),
            )

        return self._fetchall("SELECT * FROM private_replies ORDER BY added_at DESC")

    def delete_private_reply(self, reply_id: int, admin_id: int = None):
        try:
            with self.lock:
                cursor = self.conn.cursor()

                if admin_id is not None:
                    cursor.execute(
                        "DELETE FROM private_replies WHERE id=? AND admin_id=?",
                        (reply_id, admin_id),
                    )
                else:
                    cursor.execute(
                        "DELETE FROM private_replies WHERE id=?",
                        (reply_id,),
                    )

                self.conn.commit()
                return cursor.rowcount > 0

        except Exception:
            self.conn.rollback()
            return False

    # ==================================================
    # RANDOM REPLIES
    # ==================================================

    def add_random_reply(self, admin_id: int, r_type: str, text: str = None, media_path: str = None):
        if not isinstance(admin_id, int) or admin_id <= 0:
            return False

        if r_type not in ("text", "photo"):
            return False

        if not text and not media_path:
            return False

        try:
            with self.lock:
                cursor = self.conn.cursor()

                cursor.execute("""
                INSERT INTO random_replies (admin_id, type, text, media_path, added_at)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    admin_id,
                    r_type,
                    text,
                    media_path,
                    self._now(),
                ))

                self.conn.commit()
                return True

        except Exception:
            self.conn.rollback()
            return False

    def get_random_replies(self, admin_id: int = None):
        if admin_id is not None:
            return self._fetchall(
                "SELECT * FROM random_replies WHERE admin_id=? ORDER BY added_at DESC",
                (admin_id,),
            )

        return self._fetchall("SELECT * FROM random_replies ORDER BY added_at DESC")

    def delete_random_reply(self, reply_id: int, admin_id: int = None):
        try:
            with self.lock:
                cursor = self.conn.cursor()

                if admin_id is not None:
                    cursor.execute(
                        "DELETE FROM random_replies WHERE id=? AND admin_id=?",
                        (reply_id, admin_id),
                    )
                else:
                    cursor.execute(
                        "DELETE FROM random_replies WHERE id=?",
                        (reply_id,),
                    )

                self.conn.commit()
                return cursor.rowcount > 0

        except Exception:
            self.conn.rollback()
            return False

    # ==================================================
    # STATISTICS
    # ==================================================

    def get_statistics(self, admin_id: int) -> dict:
        """
        الحصول على إحصائيات للمدير.
        """
        accounts = self.get_accounts(admin_id)
        ads = self.get_ads(admin_id)
        groups = self.get_groups(admin_id)
        private_replies = self.get_private_replies(admin_id)
        random_replies = self.get_random_replies(admin_id)

        active_accounts = len([
            account for account in accounts
            if account["active"] == 1
        ])

        active_ads = len([
            ad for ad in ads
            if ad["active"] == 1
        ])

        active_groups = len([
            group for group in groups
            if group["status"] == "active"
        ])

        return {
            "accounts": len(accounts),
            "active_accounts": active_accounts,
            "ads": len(ads),
            "active_ads": active_ads,
            "groups": len(groups),
            "active_groups": active_groups,
            "private_replies": len(private_replies),
            "random_replies": len(random_replies),
        }

    # ==================================================
    # CLEANUP
    # ==================================================

    def close(self):
        """
        إغلاق اتصال قاعدة البيانات.
        """
        with self.lock:
            if self.conn:
                self.conn.close()
