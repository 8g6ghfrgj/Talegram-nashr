from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from menus import show_replies_menu


class ReplyHandlers:

    def __init__(self, db):
        self.db = db


    # ==================================================
    # SHOW ALL REPLIES (PRIVATE + RANDOM)
    # ==================================================

    async def show_replies(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query
        await query.answer()

        admin_id = query.from_user.id

        private_replies = self.db.get_private_replies(admin_id)
        random_replies = self.db.get_random_replies(admin_id)

        if not private_replies and not random_replies:
            await query.edit_message_text(
                "❌ لا توجد ردود مضافة",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 رجوع", callback_data="back_replies")]
                ])
            )
            return

        text = "💬 الردود:\n\n"
        keyboard = []

        # ---------- PRIVATE ----------
        if private_replies:
            text += "🔒 الردود الخاصة:\n"
            for r in private_replies:
                r_id, _, r_text, added = r
                text += f"#{r_id} — {r_text[:40]}\n"
                text += f"{added}\n\n"

                keyboard.append([
                    InlineKeyboardButton(
                        "🗑 حذف (خاص)",
                        callback_data=f"delete_private_reply_{r_id}"
                    )
                ])

        # ---------- RANDOM ----------
        if random_replies:
            text += "🎲 الردود العشوائية:\n"
            for r in random_replies:
                r_id, _, r_type, r_text, r_media, added = r

                desc = r_text[:30] if r_text else "بدون نص"
                media = "🖼️" if r_media else "—"

                text += f"#{r_id} — {r_type} | {desc} | {media}\n"
                text += f"{added}\n\n"

                keyboard.append([
                    InlineKeyboardButton(
                        "🗑 حذف (عشوائي)",
                        callback_data=f"delete_random_reply_{r_id}"
                    )
                ])

        keyboard.append(
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_replies")]
        )

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    # ==================================================
    # DELETE PRIVATE REPLY
    # ==================================================

    async def delete_private_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE, reply_id: int):

        query = update.callback_query
        await query.answer()

        admin_id = query.from_user.id
        self.db.delete_private_reply(reply_id, admin_id)

        await self.show_replies(update, context)


    # ==================================================
    # DELETE RANDOM REPLY
    # ==================================================

    async def delete_random_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE, reply_id: int):

        query = update.callback_query
        await query.answer()

        admin_id = query.from_user.id
        self.db.delete_random_reply(reply_id, admin_id)

        await self.show_replies(update, context)
