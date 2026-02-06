import asyncio
import logging
import random

from config import DELAY_SETTINGS

logger = logging.getLogger(__name__)


class TelegramBotManager:

    def __init__(self, db):
        self.db = db

        # مهام التشغيل لكل مشرف
        self.publishing_tasks = {}
        self.join_tasks = {}

        self.private_reply_tasks = {}
        self.random_reply_tasks = {}


    # ==================================================
    # PUBLISH ADS (SIMULATION)
    # ==================================================

    def start_publishing(self, admin_id):

        if admin_id in self.publishing_tasks:
            return False

        task = asyncio.create_task(
            self._publishing_loop(admin_id)
        )

        self.publishing_tasks[admin_id] = task
        return True


    def stop_publishing(self, admin_id):

        task = self.publishing_tasks.pop(admin_id, None)

        if task:
            task.cancel()
            return True

        return False


    async def _publishing_loop(self, admin_id):

        logger.info(f"[PUBLISH] Started for admin {admin_id}")

        while True:
            try:
                accounts = self.db.get_accounts(admin_id)
                ads = self.db.get_ads(admin_id)
                groups = self.db.get_groups(admin_id)

                active_accounts = [a for a in accounts if a[3] == 1]
                joined_groups = [g for g in groups if g[3] == "joined"]

                if not active_accounts or not ads or not joined_groups:
                    await asyncio.sleep(10)
                    continue

                random.shuffle(active_accounts)
                random.shuffle(ads)
                random.shuffle(joined_groups)

                for acc in active_accounts:

                    for ad in ads:

                        for group in joined_groups:

                            # 🔧 هنا مستقبلاً ترسل الإعلان الحقيقي
                            logger.info(
                                f"[SEND] acc:{acc[0]} -> group:{group[0]} -> ad:{ad[0]}"
                            )

                            await asyncio.sleep(
                                DELAY_SETTINGS["publishing"]["between_groups"]
                            )

                        await asyncio.sleep(
                            DELAY_SETTINGS["publishing"]["between_ads"]
                        )

                await asyncio.sleep(
                    DELAY_SETTINGS["publishing"]["between_cycles"]
                )

            except asyncio.CancelledError:
                logger.info(f"[PUBLISH] Stopped for admin {admin_id}")
                break

            except Exception as e:
                logger.exception(e)
                await asyncio.sleep(5)


    # ==================================================
    # JOIN GROUPS (SIMULATION)
    # ==================================================

    def start_join_groups(self, admin_id):

        if admin_id in self.join_tasks:
            return False

        task = asyncio.create_task(
            self._join_groups_loop(admin_id)
        )

        self.join_tasks[admin_id] = task
        return True


    def stop_join_groups(self, admin_id):

        task = self.join_tasks.pop(admin_id, None)

        if task:
            task.cancel()
            return True

        return False


    async def _join_groups_loop(self, admin_id):

        logger.info(f"[JOIN] Started for admin {admin_id}")

        while True:
            try:
                accounts = self.db.get_accounts(admin_id)
                groups = self.db.get_groups(admin_id)

                active_accounts = [a for a in accounts if a[3] == 1]
                pending_groups = [g for g in groups if g[3] == "pending"]

                if not active_accounts or not pending_groups:
                    await asyncio.sleep(10)
                    continue

                for group in pending_groups:

                    for acc in active_accounts:

                        # 🔧 هنا مستقبلاً تنفيذ الانضمام الحقيقي
                        logger.info(
                            f"[JOIN] acc:{acc[0]} -> group:{group[0]}"
                        )

                        # تحديث الحالة كمحاكاة
                        # (يمكن لاحقاً جعلها joined أو failed حسب النتيجة)

                        await asyncio.sleep(
                            DELAY_SETTINGS["join_groups"]["between_links"]
                        )

                await asyncio.sleep(
                    DELAY_SETTINGS["join_groups"]["between_cycles"]
                )

            except asyncio.CancelledError:
                logger.info(f"[JOIN] Stopped for admin {admin_id}")
                break

            except Exception as e:
                logger.exception(e)
                await asyncio.sleep(5)


    # ==================================================
    # PRIVATE REPLIES LOOP (OPTIONAL)
    # ==================================================

    def start_private_replies(self, admin_id):

        if admin_id in self.private_reply_tasks:
            return False

        task = asyncio.create_task(
            self._private_reply_loop(admin_id)
        )

        self.private_reply_tasks[admin_id] = task
        return True


    def stop_private_replies(self, admin_id):

        task = self.private_reply_tasks.pop(admin_id, None)

        if task:
            task.cancel()
            return True

        return False


    async def _private_reply_loop(self, admin_id):

        logger.info(f"[PRIVATE REPLY] Started for admin {admin_id}")

        while True:
            try:
                replies = self.db.get_private_replies(admin_id)

                if not replies:
                    await asyncio.sleep(5)
                    continue

                for r in replies:
                    logger.info(f"[PRIVATE REPLY] {r[0]}")
                    await asyncio.sleep(
                        DELAY_SETTINGS["private_reply"]["between_replies"]
                    )

                await asyncio.sleep(
                    DELAY_SETTINGS["private_reply"]["between_cycles"]
                )

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.exception(e)
                await asyncio.sleep(5)


    # ==================================================
    # RANDOM REPLIES LOOP (OPTIONAL)
    # ==================================================

    def start_random_replies(self, admin_id):

        if admin_id in self.random_reply_tasks:
            return False

        task = asyncio.create_task(
            self._random_reply_loop(admin_id)
        )

        self.random_reply_tasks[admin_id] = task
        return True


    def stop_random_replies(self, admin_id):

        task = self.random_reply_tasks.pop(admin_id, None)

        if task:
            task.cancel()
            return True

        return False


    async def _random_reply_loop(self, admin_id):

        logger.info(f"[RANDOM REPLY] Started for admin {admin_id}")

        while True:
            try:
                replies = self.db.get_random_replies(admin_id)

                if not replies:
                    await asyncio.sleep(5)
                    continue

                reply = random.choice(replies)

                logger.info(f"[RANDOM REPLY] {reply[0]}")

                await asyncio.sleep(
                    DELAY_SETTINGS["random_reply"]["between_replies"]
                )

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.exception(e)
                await asyncio.sleep(5)
