import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BotDatabase:

    def __init__(self, db_name="bot_database.db"):
        self.db_name = db_name
        self.init_database()

    def connect(self):
        return sqlite3.connect(self.db_name)

    # ==================================================
    # INIT
    # ==================================================

    def init_database(self):

        conn = self.connect()
        c = conn.cursor()

        c.execute("""CREATE TABLE IF NOT EXISTS accounts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_string TEXT UNIQUE,
            phone TEXT,
            name TEXT,
            username TEXT,
            is_active INTEGER DEFAULT 1,
            added_date TEXT DEFAULT CURRENT_TIMESTAMP,
            admin_id INTEGER DEFAULT 0,
            last_activity TEXT
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS account_publishing(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            status TEXT DEFAULT 'active',
            last_publish TEXT,
            publish_count INTEGER DEFAULT 0
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS ads(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            text TEXT,
            media_path TEXT,
            file_type TEXT,
            added_date TEXT DEFAULT CURRENT_TIMESTAMP,
            admin_id INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS groups(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link TEXT,
            status TEXT DEFAULT 'pending',
            join_date TEXT,
            added_date TEXT DEFAULT CURRENT_TIMESTAMP,
            admin_id INTEGER DEFAULT 0,
            last_checked TEXT
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS admins(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            username TEXT,
            full_name TEXT,
            added_date TEXT DEFAULT CURRENT_TIMESTAMP,
            is_super_admin INTEGER DEFAULT 0
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS private_replies(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reply_text TEXT,
            is_active INTEGER DEFAULT 1,
            added_date TEXT DEFAULT CURRENT_TIMESTAMP,
            admin_id INTEGER DEFAULT 0
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS group_text_replies(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger TEXT,
            reply_text TEXT,
            is_active INTEGER DEFAULT 1,
            added_date TEXT DEFAULT CURRENT_TIMESTAMP,
            admin_id INTEGER DEFAULT 0
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS group_photo_replies(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger TEXT,
            reply_text TEXT,
            media_path TEXT,
            is_active INTEGER DEFAULT 1,
            added_date TEXT DEFAULT CURRENT_TIMESTAMP,
            admin_id INTEGER DEFAULT 0
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS group_random_replies(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reply_text TEXT,
            media_path TEXT,
            is_active INTEGER DEFAULT 1,
            added_date TEXT DEFAULT CURRENT_TIMESTAMP,
            admin_id INTEGER DEFAULT 0,
            has_media INTEGER DEFAULT 0
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            action TEXT,
            details TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )""")

        conn.commit()
        conn.close()

    # ==================================================
    # ADMINS
    # ==================================================

    def add_admin(self, user_id, username, full_name, is_super=False):

        conn = self.connect()
        c = conn.cursor()

        try:
            c.execute(
                "INSERT INTO admins(user_id,username,full_name,is_super_admin) VALUES(?,?,?,?)",
                (user_id, username, full_name, int(is_super))
            )
            conn.commit()
            return True, "تم إضافة المشرف"

        except sqlite3.IntegrityError:
            return False, "المشرف موجود مسبقاً"

        finally:
            conn.close()

    def get_admins(self):

        conn = self.connect()
        c = conn.cursor()

        c.execute("SELECT * FROM admins ORDER BY id")
        rows = c.fetchall()

        conn.close()
        return rows

    def delete_admin(self, admin_id):

        conn = self.connect()
        c = conn.cursor()

        c.execute("DELETE FROM admins WHERE id=?", (admin_id,))
        conn.commit()

        ok = c.rowcount > 0
        conn.close()
        return ok

    def is_admin(self, user_id):

        conn = self.connect()
        c = conn.cursor()

        c.execute("SELECT id FROM admins WHERE user_id=?", (user_id,))
        r = c.fetchone()

        conn.close()
        return r is not None

    # ==================================================
    # ACCOUNTS
    # ==================================================

    def add_account(self, session, phone, name, username, admin_id):

        conn = self.connect()
        c = conn.cursor()

        try:
            c.execute("""INSERT INTO accounts
                (session_string,phone,name,username,admin_id)
                VALUES(?,?,?,?,?)""",
                (session, phone, name, username, admin_id))

            acc_id = c.lastrowid

            c.execute("INSERT INTO account_publishing(account_id) VALUES(?)", (acc_id,))
            conn.commit()

            return True, f"تم إضافة الحساب #{acc_id}"

        except sqlite3.IntegrityError:
            return False, "الحساب موجود مسبقاً"

        finally:
            conn.close()

    def get_accounts(self, admin_id):

        conn = self.connect()
        c = conn.cursor()

        c.execute("""
        SELECT a.id,a.session_string,a.phone,a.name,a.username,
               a.is_active,a.added_date,ap.status,ap.last_publish
        FROM accounts a
        LEFT JOIN account_publishing ap ON a.id=ap.account_id
        WHERE a.admin_id=? OR a.admin_id=0
        ORDER BY a.id
        """, (admin_id,))

        rows = c.fetchall()
        conn.close()
        return rows

    def delete_account(self, acc_id, admin_id):

        conn = self.connect()
        c = conn.cursor()

        c.execute("DELETE FROM accounts WHERE id=? AND (admin_id=? OR admin_id=0)",
                  (acc_id, admin_id))

        c.execute("DELETE FROM account_publishing WHERE account_id=?", (acc_id,))
        conn.commit()

        ok = c.rowcount > 0
        conn.close()
        return ok

    def toggle_account_status(self, acc_id, admin_id):

        conn = self.connect()
        c = conn.cursor()

        c.execute("SELECT is_active FROM accounts WHERE id=?",(acc_id,))
        r = c.fetchone()

        if not r:
            conn.close()
            return False

        new = 0 if r[0] else 1

        c.execute("""
        UPDATE accounts SET is_active=?
        WHERE id=? AND (admin_id=? OR admin_id=0)
        """, (new, acc_id, admin_id))

        conn.commit()
        conn.close()
        return True

    def get_active_publishing_accounts(self, admin_id):

        conn = self.connect()
        c = conn.cursor()

        c.execute("""
        SELECT a.id,a.session_string,a.name,a.username
        FROM accounts a
        JOIN account_publishing ap ON a.id=ap.account_id
        WHERE a.is_active=1 AND ap.status='active'
        AND (a.admin_id=? OR a.admin_id=0)
        """,(admin_id,))

        rows = c.fetchall()
        conn.close()
        return rows

    # ==================================================
    # ADS
    # ==================================================

    def add_ad(self, ad_type, text, media_path, file_type, admin_id):

        conn = self.connect()
        c = conn.cursor()

        c.execute("""INSERT INTO ads(type,text,media_path,file_type,admin_id)
                     VALUES(?,?,?,?,?)""",
                  (ad_type, text, media_path, file_type, admin_id))

        conn.commit()
        conn.close()
        return True, "تم إضافة الإعلان"

    def get_ads(self, admin_id=None):

        conn = self.connect()
        c = conn.cursor()

        if admin_id is not None:
            c.execute("SELECT * FROM ads WHERE admin_id=? OR admin_id=0 ORDER BY id",
                      (admin_id,))
        else:
            c.execute("SELECT * FROM ads ORDER BY id")

        rows = c.fetchall()
        conn.close()
        return rows

    def delete_ad(self, ad_id, admin_id):

        conn = self.connect()
        c = conn.cursor()

        c.execute("""DELETE FROM ads WHERE id=? AND (admin_id=? OR admin_id=0)""",
                  (ad_id, admin_id))

        conn.commit()
        ok = c.rowcount > 0
        conn.close()
        return ok

    # ==================================================
    # GROUPS
    # ==================================================

    def add_group(self, link, admin_id):

        conn = self.connect()
        c = conn.cursor()

        c.execute("INSERT INTO groups(link,admin_id) VALUES(?,?)",
                  (link, admin_id))

        conn.commit()
        conn.close()
        return True

    def get_groups(self, admin_id=None, status=None):

        conn = self.connect()
        c = conn.cursor()

        q = "SELECT * FROM groups WHERE 1=1"
        p = []

        if admin_id is not None:
            q += " AND (admin_id=? OR admin_id=0)"
            p.append(admin_id)

        if status:
            q += " AND status=?"
            p.append(status)

        q += " ORDER BY id"

        c.execute(q, p)
        rows = c.fetchall()
        conn.close()
        return rows

    def update_group_status(self, gid, status):

        conn = self.connect()
        c = conn.cursor()

        c.execute("""UPDATE groups SET status=?,join_date=CURRENT_TIMESTAMP,
                     last_checked=CURRENT_TIMESTAMP WHERE id=?""",
                  (status, gid))

        conn.commit()
        conn.close()
        return True

    # ==================================================
    # REPLIES
    # ==================================================

    def add_private_reply(self, text, admin_id):

        conn = self.connect()
        c = conn.cursor()

        c.execute("INSERT INTO private_replies(reply_text,admin_id) VALUES(?,?)",
                  (text, admin_id))

        conn.commit()
        conn.close()
        return True

    def get_private_replies(self, admin_id=None):

        conn = self.connect()
        c = conn.cursor()

        if admin_id is not None:
            c.execute("SELECT * FROM private_replies WHERE admin_id=? OR admin_id=0",
                      (admin_id,))
        else:
            c.execute("SELECT * FROM private_replies")

        rows = c.fetchall()
        conn.close()
        return rows

    def delete_private_reply(self, rid, admin_id):

        conn = self.connect()
        c = conn.cursor()

        c.execute("""DELETE FROM private_replies
                     WHERE id=? AND (admin_id=? OR admin_id=0)""",
                  (rid, admin_id))

        conn.commit()
        ok = c.rowcount > 0
        conn.close()
        return ok

    def add_group_text_reply(self, trigger, text, admin_id):

        conn = self.connect()
        c = conn.cursor()

        c.execute("""INSERT INTO group_text_replies
                     (trigger,reply_text,admin_id)
                     VALUES(?,?,?)""",
                  (trigger, text, admin_id))

        conn.commit()
        conn.close()
        return True

    def get_group_text_replies(self, admin_id=None):

        conn = self.connect()
        c = conn.cursor()

        if admin_id:
            c.execute("""SELECT * FROM group_text_replies
                         WHERE admin_id=? OR admin_id=0""",(admin_id,))
        else:
            c.execute("SELECT * FROM group_text_replies")

        rows = c.fetchall()
        conn.close()
        return rows

    def delete_group_text_reply(self, rid, admin_id):

        conn = self.connect()
        c = conn.cursor()

        c.execute("""DELETE FROM group_text_replies
                     WHERE id=? AND (admin_id=? OR admin_id=0)""",
                  (rid, admin_id))

        conn.commit()
        ok = c.rowcount > 0
        conn.close()
        return ok

    def add_group_photo_reply(self, trigger, text, media, admin_id):

        conn = self.connect()
        c = conn.cursor()

        c.execute("""INSERT INTO group_photo_replies
                     (trigger,reply_text,media_path,admin_id)
                     VALUES(?,?,?,?)""",
                  (trigger, text, media, admin_id))

        conn.commit()
        conn.close()
        return True

    def get_group_photo_replies(self, admin_id=None):

        conn = self.connect()
        c = conn.cursor()

        if admin_id:
            c.execute("""SELECT * FROM group_photo_replies
                         WHERE admin_id=? OR admin_id=0""",(admin_id,))
        else:
            c.execute("SELECT * FROM group_photo_replies")

        rows = c.fetchall()
        conn.close()
        return rows

    def delete_group_photo_reply(self, rid, admin_id):

        conn = self.connect()
        c = conn.cursor()

        c.execute("""DELETE FROM group_photo_replies
                     WHERE id=? AND (admin_id=? OR admin_id=0)""",
                  (rid, admin_id))

        conn.commit()
        ok = c.rowcount > 0
        conn.close()
        return ok

    def add_group_random_reply(self, text, media, admin_id):

        conn = self.connect()
        c = conn.cursor()

        c.execute("""INSERT INTO group_random_replies
                     (reply_text,media_path,admin_id,has_media)
                     VALUES(?,?,?,?)""",
                  (text, media, admin_id, 1 if media else 0))

        conn.commit()
        conn.close()
        return True

    def get_group_random_replies(self, admin_id=None):

        conn = self.connect()
        c = conn.cursor()

        if admin_id:
            c.execute("""SELECT * FROM group_random_replies
                         WHERE is_active=1 AND (admin_id=? OR admin_id=0)""",
                      (admin_id,))
        else:
            c.execute("SELECT * FROM group_random_replies WHERE is_active=1")

        rows = c.fetchall()
        conn.close()
        return rows

    def delete_group_random_reply(self, rid, admin_id):

        conn = self.connect()
        c = conn.cursor()

        c.execute("""DELETE FROM group_random_replies
                     WHERE id=? AND (admin_id=? OR admin_id=0)""",
                  (rid, admin_id))

        conn.commit()
        ok = c.rowcount > 0
        conn.close()
        return ok

    # ==================================================
    # LOGS + STATS
    # ==================================================

    def log_action(self, admin_id, action, details):

        conn = self.connect()
        c = conn.cursor()

        c.execute("""INSERT INTO logs(admin_id,action,details)
                     VALUES(?,?,?)""",
                  (admin_id, action, details))

        conn.commit()
        conn.close()

    def get_logs(self, limit=50):

        conn = self.connect()
        c = conn.cursor()

        c.execute("SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?",
                  (limit,))

        rows = c.fetchall()
        conn.close()
        return rows

    def get_statistics(self, admin_id=None):

        conn = self.connect()
        c = conn.cursor()

        if admin_id:
            c.execute("SELECT COUNT(*),SUM(is_active) FROM accounts WHERE admin_id=? OR admin_id=0",(admin_id,))
        else:
            c.execute("SELECT COUNT(*),SUM(is_active) FROM accounts")

        total, active = c.fetchone()

        if admin_id:
            c.execute("SELECT COUNT(*) FROM ads WHERE admin_id=? OR admin_id=0",(admin_id,))
        else:
            c.execute("SELECT COUNT(*) FROM ads")

        ads = c.fetchone()[0]

        if admin_id:
            c.execute("""SELECT COUNT(*),
                         SUM(CASE WHEN status='joined' THEN 1 ELSE 0 END)
                         FROM groups WHERE admin_id=? OR admin_id=0""",(admin_id,))
        else:
            c.execute("""SELECT COUNT(*),
                         SUM(CASE WHEN status='joined' THEN 1 ELSE 0 END)
                         FROM groups""")

        g_total, g_joined = c.fetchone()

        conn.close()

        return {
            "accounts": {"total": total or 0, "active": active or 0},
            "ads": ads or 0,
            "groups": {"total": g_total or 0, "joined": g_joined or 0}
        }
