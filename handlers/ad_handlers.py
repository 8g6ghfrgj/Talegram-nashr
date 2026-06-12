from telegram.ext import CallbackQueryHandler
from handlers.ads_handlers import AdHandlers


ad_handlers = AdHandlers(db)


application.add_handler(
    CallbackQueryHandler(
        ad_handlers.show_ads,
        pattern="^show_ads$"
    )
)

application.add_handler(
    CallbackQueryHandler(
        ad_handlers.ad_stats,
        pattern="^ads_stats$"
    )
)


async def delete_ad_callback(update, context):
    query = update.callback_query
    ad_id = int(query.data.replace("delete_ad_", ""))
    await ad_handlers.delete_ad(update, context, ad_id)


application.add_handler(
    CallbackQueryHandler(
        delete_ad_callback,
        pattern="^delete_ad_\\d+$"
    )
)
