import asyncio
import threading
import os
import random
import logging

from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest

from config import DELAY_SETTINGS, API_ID, API_HASH

logger = logging.getLogger(__name__)


class TelegramBotManager:

    def __init__(self, db):
        self.db = db
        self.delay_settings = DELAY_SETTINGS

        self.loop = asyncio.get_event_loop()

        self.client_cache = {}

        self.tasks = {
            "publish": {},
            "private_reply": {},
            "group_reply": {},
            "random_reply": {},
            "join": {}
        }

        self.active = {
            "publish": {},
            "private_reply": {},
            "group_reply": {},
            "random_reply": {},
            "join": {}
        }

        self.lock = threading.Lock()

        self.stats = {
            "publish": 0,
            "reply": 0,
            "join": 0,
            "errors": 0
        }

        logger.info("✅ Telegram manager ready")


# ============================================================
# CLIENT MANAGEMENT
# ============================================================

    async def get_client(self, session):

        if session in self.client_cache:
            return self.client_cache[session]

        try:
            client = TelegramClient(
                StringSession(session),
                API_ID,
                API_HASH
            )

            await client.connect()

            if not await client.is_user_authorized():
                await client.disconnect()
                logger.error("❌ Unauthorized session")
                return None

            self.client_cache[session] = client
            return client

        except Exception as e:
            logger.error(f"❌ Client error: {e}")
            return None


    async def cleanup_all(self):

        for client in self.client_cache.values():
            try:
                await client.disconnect()
            except:
                pass

        self.client_cache.clear()


# ============================================================
# SAFE TASK CREATOR
# ============================================================

    def _start_task(self, name, admin_id, coro):

        if self.active[name].get(admin_id):
            return False

        self.active[name][admin_id] = True

        task = self.loop.create_task(coro)

        self.tasks[name][admin_id] = task

        return True


    def _stop_task(self, name, admin_id):

        self.active[name][admin_id] = False

        task = self.tasks[name].get(admin_id)

        if task:
            task.cancel()
            del self.tasks[name][admin_id]


# ============================================================
# PUBLISHING
# ============================================================

    async def publish_loop(self, admin_id):

        logger.info(f"🚀 Publishing started: {admin_id}")

        while self.active["publish"].get(admin_id):

            accounts = self.db.get_active_publishing_accounts(admin_id)
            ads = self.db.get_ads(admin_id)

            if not accounts or not ads:
                await asyncio.sleep(30)
                continue

            for acc in accounts:

                if not self.active["publish"].get(admin_id):
                    break

                _, session, name, _ = acc

                client = await self.get_client(session)

                if not client:
                    continue

                try:
                    dialogs = await client.get_dialogs(limit=100)

                    for dialog in dialogs:

                        if not self.active["publish"].get(admin_id):
                            break

                        if not (dialog.is_group or dialog.is_channel):
                            continue

                        for ad in ads:

                            ad_type, ad_text, media = ad[1], ad[2], ad[3]

                            try:
                                if ad_type == "text":
                                    await client.send_message(dialog.id, ad_text)

                                elif ad_type == "photo" and media and os.path.exists(media):
                                    await client.send_file(dialog.id, media, caption=ad_text)

                                self.stats["publish"] += 1

                                await asyncio.sleep(
                                    self.delay_settings["publishing"]["between_ads"]
                                )

                            except errors.FloodWaitError as e:
                                await asyncio.sleep(e.seconds + 1)

                            except Exception as e:
                                logger.error(e)
                                self.stats["errors"] += 1

                        # ⏱ delay between groups
                        await asyncio.sleep(
                            self.delay_settings["publishing"]["group_publishing_delay"]
                        )

                except Exception as e:
                    logger.error(f"❌ Publish error: {e}")

            await asyncio.sleep(
                self.delay_settings["publishing"]["between_cycles"]
            )

        logger.info(f"⏹ Publishing stopped: {admin_id}")


# ============================================================
# JOIN GROUPS
# ============================================================

    async def join_loop(self, admin_id):

        logger.info(f"👥 Join started: {admin_id}")

        while self.active["join"].get(admin_id):

            accounts = self.db.get_active_publishing_accounts(admin_id)
            groups = self.db.get_groups(admin_id, status="pending")

            if not accounts or not groups:
                await asyncio.sleep(30)
                continue

            for acc in accounts:

                _, session, name, _ = acc

                client = await self.get_client(session)

                if not client:
                    continue

                for group in groups:

                    if not self.active["join"].get(admin_id):
                        break

                    link = group[1]

                    try:
                        await self.join_single(client, link)
                        self.stats["join"] += 1

                    except Exception as e:
                        logger.error(e)

                    await asyncio.sleep(
                        self.delay_settings["join_groups"]["between_links"]
                    )

            await asyncio.sleep(
                self.delay_settings["join_groups"]["between_cycles"]
            )


    async def join_single(self, client, link):

        link = link.replace("https://", "").replace("t.me/", "")

        if link.startswith("+") or "joinchat" in link:
            invite = link.replace("+", "").split("/")[-1]
            await client(ImportChatInviteRequest(invite))
        else:
            await client(JoinChannelRequest(f"@{link}"))


# ============================================================
# PUBLIC CONTROL FUNCTIONS
# ============================================================

    def start_publishing(self, admin_id):
        return self._start_task(
            "publish",
            admin_id,
            self.publish_loop(admin_id)
        )


    def stop_publishing(self, admin_id):
        self._stop_task("publish", admin_id)


    def start_join_groups(self, admin_id):
        return self._start_task(
            "join",
            admin_id,
            self.join_loop(admin_id)
        )


    def stop_join_groups(self, admin_id):
        self._stop_task("join", admin_id)


# ============================================================
# STATS
# ============================================================

    def get_stats(self):

        return {
            "published": self.stats["publish"],
            "replies": self.stats["reply"],
            "joined": self.stats["join"],
            "errors": self.stats["errors"],
            "clients": len(self.client_cache)
        }
