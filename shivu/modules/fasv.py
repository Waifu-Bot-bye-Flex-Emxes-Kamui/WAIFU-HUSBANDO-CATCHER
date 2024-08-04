import time
import random
import re
import asyncio
from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, Application, MessageHandler, filters

from shivu import user_collection, collection, application, db  # Assuming these are correct

# ... other imports and function definitions ...

async def fav(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text('Please provide a character ID to favorite.')
        return

    character_id = context.args[0]
    user = await user_collection.find_one({'id': user_id})

    if not user:
        await update.message.reply_text('You have not interacted with any characters yet.')
        return

    character = next((c for c in user['characters'] if c['id'] == character_id), None)

    if not character:
        await update.message.reply_text('This character is not in your collection.')
        return

    keyboard = [
        [InlineKeyboardButton("Yes", callback_data=f"fav_confirm_{character_id}"),
         InlineKeyboardButton("No", callback_data="fav_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f"Are you sure you want to favorite {character['name']}?",
                                    reply_markup=reply_markup)

async def fav_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    action, character_id = query.data.split('_')[1:] 

    if action == "cancel":
        await query.answer(text="Favorite operation canceled.")
        await query.message.delete()  # Optional: Delete the confirmation message
        return

    user = await user_collection.find_one({'id': user_id})
    if not user: 
        await context.bot.send_message(chat_id=update.effective_chat.id, text="An error occurred. Please try again.")
        return

    if character_id not in user.get('favorites', []):
        user['favorites'] = user.get('favorites', []) + [character_id]
        await user_collection.update_one({'id': user_id}, {'$set': {'favorites': user['favorites']}})
        await query.answer(text="Character added to favorites!") 
    else:
        await query.answer(text="Character is already in favorites.")

    # (Optional) Edit the original message to confirm the action
    character_name = next((c['name'] for c in user['characters'] if c['id'] == character_id), "Unknown")
    await query.edit_message_text(f"{character_name} has been added to your favorites!") 

 application.add_handler(CommandHandler("fav", fav, block=False))
    application.add_handler(CallbackQueryHandler(fav_callback, pattern=r'fav_(confirm|cancel)_.+')) # Add this line

    