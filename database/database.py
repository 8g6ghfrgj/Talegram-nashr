import sqlite3
from datetime import datetime
from typing import List, Tuple


DB_NAME = "bot_database.db"


class BotDatabase:

    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()


    # ==================================================
    # CREATE TABLES
    # ==================================================

    def _create_tables(self):

        cursor = self.conn.cursor()

        # ---------- ADMINS ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY,
            username TEXT,
            role TEXT,
            active INTEGER,
            added_at TEXT
        )
        """)

        # ---------- ACCOUNTS ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            session TEXT,
            active INTEGER,
            added_at TEXT
        )
        """)

        # ---------- ADS ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            type TEXT,
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
            link TEXT,
            status TEXT,
            added_at TEXT
        )
        """)

        # ---------- PRIVATE REPLIES ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS private_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            text TEXT,
            added_at TEXT
        )
        """)

        # ---------- RANDOM REPLIES ----------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS random_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            type TEXT,
            text TEXT,
            media_path TEXT,
            added_at TEXT
        )
        """)

        self.conn.commit()


    # ==================================================
    # ADMINS
    # ==================================================

    def add_admin(self, admin_id: int, username: str, role: str, active: bool = True):

        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT OR IGNORE INTO admins (id, username, role, active, added_at)
        VALUES (?, ?, ?, ?, ?)
        """, (
            admin_id,
            username,
            role,
            1 if active else 0,
            datetime.now().isoformat()
        ))

        self.conn.commit()
        return True, "OK"


    def is_admin(self, admin_id: int) -> bool:

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id FROM admins WHERE id=? AND active=1",
            (admin_id,)
        )

        return cursor.fetchone() is not None


    def get_admins(self) -> List[Tuple]:

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM admins")
        return cursor.fetchall()


    def delete_admin(self, admin_id: int):

        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM admins WHERE id=?", (admin_id,))
        self.conn.commit()


    # ==================================================
    # ACCOUNTS
    # ==================================================

    def add_account(self, admin_id: int, session: str):

        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT INTO accounts (admin_id, session, active, added_at)
        VALUES (?, ?, 1, ?)
        """, (
            admin_id,
            session,
            datetime.now().isoformat()
        ))

        self.conn.commit()
        return True, "OK"


    def get_accounts(self, admin_id: int = None):

        cursor = self.conn.cursor()
        
        if admin_id:
            cursor.execute(
                "SELECT * FROM accounts WHERE admin_id=?",
                (admin_id,)
            )
        else:
            cursor.execute("SELECT * FROM accounts")
            
        return cursor.fetchall()


    def get_account(self, account_id: int):

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM accounts WHERE id=?",
            (account_id,)
        )
        return cursor.fetchone()


    def toggle_account_status(self, account_id: int, admin_id: int = None):

        cursor = self.conn.cursor()

        if admin_id:
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
        return True


    def delete_account(self, account_id: int, admin_id: int = None):

        cursor = self.conn.cursor()
        
        if admin_id:
            cursor.execute(
                "DELETE FROM accounts WHERE id=? AND admin_id=?",
                (account_id, admin_id)
            )
        else:
            cursor.execute(
                "DELETE FROM accounts WHERE id=?",
                (account_id,)
            )
            
        self.conn.commit()
        return True


    def update_account_session(self, account_id: int, session: str):

        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE accounts
            SET session=?
            WHERE id=?
        """, (session, account_id))
        self.conn.commit()
        return True


    # ==================================================
    # ADS
    # ==================================================

    def add_ad(self, admin_id: int, ad_type: str, text: str, media_path: str = None):

        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT INTO ads (admin_id, type, text, media_path, active, added_at)
        VALUES (?, ?, ?, ?, 1, ?)
        """, (
            admin_id,
            ad_type,
            text,
            media_path,
            datetime.now().isoformat()
        ))

        self.conn.commit()
        return True, "OK"


    def get_ads(self, admin_id: int = None):

        cursor = self.conn.cursor()
        
        if admin_id:
            cursor.execute(
                "SELECT * FROM ads WHERE admin_id=?",
                (admin_id,)
            )
        else:
            cursor.execute("SELECT * FROM ads")
            
        return cursor.fetchall()


    def get_ad(self, ad_id: int):

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM ads WHERE id=?",
            (ad_id,)
        )
        return cursor.fetchone()


    def toggle_ad_status(self, ad_id: int, admin_id: int = None):

        cursor = self.conn.cursor()

        if admin_id:
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
        return True


    def delete_ad(self, ad_id: int, admin_id: int = None):

        cursor = self.conn.cursor()
        
        if admin_id:
            cursor.execute(
                "DELETE FROM ads WHERE id=? AND admin_id=?",
                (ad_id, admin_id)
            )
        else:
            cursor.execute(
                "DELETE FROM ads WHERE id=?",
                (ad_id,)
            )
            
        self.conn.commit()
        return True


    # ==================================================
    # GROUPS
    # ==================================================

    def add_group(self, admin_id: int, link: str):

        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT INTO groups (admin_id, link, status, added_at)
        VALUES (?, ?, 'active', ?)
        """, (
            admin_id,
            link,
            datetime.now().isoformat()
        ))

        self.conn.commit()
        return True, "OK"


    def get_groups(self, admin_id: int = None):

        cursor = self.conn.cursor()
        
        if admin_id:
            cursor.execute(
                "SELECT * FROM groups WHERE admin_id=?",
                (admin_id,)
            )
        else:
            cursor.execute("SELECT * FROM groups")
            
        return cursor.fetchall()


    def get_group(self, group_id: int):

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM groups WHERE id=?",
            (group_id,)
        )
        return cursor.fetchone()


    def toggle_group_status(self, group_id: int, admin_id: int = None):

        cursor = self.conn.cursor()

        if admin_id:
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
        return True


    def delete_group(self, group_id: int, admin_id: int = None):

        cursor = self.conn.cursor()
        
        if admin_id:
            cursor.execute(
                "DELETE FROM groups WHERE id=? AND admin_id=?",
                (group_id, admin_id)
            )
        else:
            cursor.execute(
                "DELETE FROM groups WHERE id=?",
                (group_id,)
            )
            
        self.conn.commit()
        return True


    # ==================================================
    # PRIVATE REPLIES
    # ==================================================

    def add_private_reply(self, admin_id: int, text: str):

        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT INTO private_replies (admin_id, text, added_at)
        VALUES (?, ?, ?)
        """, (
            admin_id,
            text,
            datetime.now().isoformat()
        ))

        self.conn.commit()
        return True


    def get_private_replies(self, admin_id: int = None):

        cursor = self.conn.cursor()
        
        if admin_id:
            cursor.execute(
                "SELECT * FROM private_replies WHERE admin_id=?",
                (admin_id,)
            )
        else:
            cursor.execute("SELECT * FROM private_replies")
            
        return cursor.fetchall()


    def delete_private_reply(self, reply_id: int, admin_id: int = None):

        cursor = self.conn.cursor()
        
        if admin_id:
            cursor.execute(
                "DELETE FROM private_replies WHERE id=? AND admin_id=?",
                (reply_id, admin_id)
            )
        else:
            cursor.execute(
                "DELETE FROM private_replies WHERE id=?",
                (reply_id,)
            )
            
        self.conn.commit()
        return True


    # ==================================================
    # RANDOM REPLIES
    # ==================================================

    def add_random_reply(self, admin_id: int, r_type: str, text: str, media_path: str = None):

        cursor = self.conn.cursor()

        cursor.execute("""
        INSERT INTO random_replies (admin_id, type, text, media_path, added_at)
        VALUES (?, ?, ?, ?, ?)
        """, (
            admin_id,
            r_type,
            text,
            media_path,
            datetime.now().isoformat()
        ))

        self.conn.commit()
        return True


    def get_random_replies(self, admin_id: int = None):

        cursor = self.conn.cursor()
        
        if admin_id:
            cursor.execute(
                "SELECT * FROM random_replies WHERE admin_id=?",
                (admin_id,)
            )
        else:
            cursor.execute("SELECT * FROM random_replies")
            
        return cursor.fetchall()


    def delete_random_reply(self, reply_id: int, admin_id: int = None):

        cursor = self.conn.cursor()
        
        if admin_id:
            cursor.execute(
                "DELETE FROM random_replies WHERE id=? AND admin_id=?",
                (reply_id, admin_id)
            )
        else:
            cursor.execute(
                "DELETE FROM random_replies WHERE id=?",
                (reply_id,)
            )
            
        self.conn.commit()
        return True


    # ==================================================
    # STATISTICS
    # ==================================================

    def get_statistics(self, admin_id: int) -> dict:
        """الحصول على إحصائيات للمدير"""

        accounts = self.get_accounts(admin_id)
        active_accounts = len([a for a in accounts if a['active'] == 1])

        ads = self.get_ads(admin_id)
        active_ads = len([a for a in ads if a.get('active', 1) == 1])

        groups = self.get_groups(admin_id)
        active_groups = len([g for g in groups if g['status'] == 'active'])

        private_replies = self.get_private_replies(admin_id)
        random_replies = self.get_random_replies(admin_id)

        return {
            "accounts": len(accounts),
            "active_accounts": active_accounts,
            "ads": len(ads),
            "active_ads": active_ads,
            "groups": len(groups),
            "active_groups": active_groups,
            "private_replies": len(private_replies),
            "random_replies": len(random_replies)
        }


    # ==================================================
    # CLEANUP
    # ==================================================

    def close(self):
        """إغلاق اتصال قاعدة البيانات"""
        self.conn.close()
