import logging
import asyncio
import io
from typing import Dict

import httpx
from gtts import gTTS
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ---------------------------------------------------------------------
# HARD-CODED CONFIG
# ---------------------------------------------------------------------
TELEGRAM_TOKEN = "8516080818:AAHZ72UcHwAg93pWKxHfJjWQYR-qkltxiXY"

# Text AI Config
GITHUB_TOKEN = "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"
GITHUB_MODELS_ENDPOINT = "https://models.github.ai/inference"
GITHUB_MODELS_MODEL = "openai/gpt-4.1"

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Language texts
# ---------------------------------------------------------------------
TEXTS: Dict[str, Dict[str, str]] = {
    "en": {
        "welcome": "👋 *AI Assistant 2025*\n\nI can Chat, Speak, Draw, and create Video Scenes!",
        "new_chat": "✨ New chat started.",
        "help": (
            "❓ **Help Menu**\n\n"
            "• **Chat**: Just text me.\n"
            "• **Image**: `/image <prompt>` (Square)\n"
            "• **Video**: `/video <prompt>` (Cinematic 16:9)\n"
            "• **Voice**: Toggle Voice ON/OFF below.\n"
        ),
        "donate": "💰 **Donation**\nSupport us via ACLEDA...",
        "support": "🛟 **Support**\nContact: @Blehhhhhhhhhhhhhhhhhhhhhhhh",
        "choose_language": "🌐 Choose your language:",
        "lang_en_label": "🇺🇸 English",
        "lang_km_label": "🇰🇭 Khmer",
        "lang_changed_en": "✅ Language: English.",
        "lang_changed_km": "✅ Language: Khmer.",
        "error_generic": "⚠️ Error. Please try again.",
        
        # Image/Video texts
        "img_instruction": "🎨 Usage: `/image description`",
        "img_generating": "🎨 Generating image...",
        "img_caption": "Here is your image!",
        
        "vid_instruction": "🎬 Usage: `/video description`",
        "vid_generating": "🎬 Generating cinematic scene...",
        "vid_caption": "Here is your cinematic concept!",
        
        # Voice texts
        "voice_on": "🔊 Voice: **ON**.",
        "voice_off": "🔇 Voice: **OFF**.",
        "voice_btn_on": "🔊 Voice: ON",
        "voice_btn_off": "🔇 Voice: OFF",

        "btn_language": "Language",
        "btn_help": "Help",
        "btn_donate": "Donate",
        "btn_support": "Support",
    },
    "km": {
        "welcome": "👋 *បូត AI ឆ្នាំ ២០២៥*\n\nខ្ញុំអាចជជែក បង្កើតរូបភាព និងបង្កើតប្លង់វីដេអូ!",
        "new_chat": "✨ ចាប់ផ្តើមជជែកថ្មី។",
        "help": (
            "❓ **ជំនួយ**\n\n"
            "• **ជជែក**: សរសេរសារ។\n"
            "• **រូបភាព**: `/image <...>` (ការ៉េ)\n"
            "• **វីដេអូ**: `/video <...>` (ប្លង់កុន 16:9)\n"
            "• **សំឡេង**: បិទ/បើក សំឡេងខាងក្រោម។\n"
        ),
        "donate": "💰 **ការរួមចំណែក**\nACLEDA: ...",
        "support": "🛟 **ការគាំទ្រ**\nទាក់ទង: @Blehhhhhhhhhhhhhhhhhhhhhhhh",
        "choose_language": "🌐 ជ្រើសរើសភាសា៖",
        "lang_en_label": "🇺🇸 អង់គ្លេស",
        "lang_km_label": "🇰🇭 ខ្មែរ",
        "lang_changed_en": "✅ បានប្ដូរទៅអង់គ្លេស។",
        "lang_changed_km": "✅ បានប្ដូរទៅខ្មែរ។",
        "error_generic": "⚠️ មានបញ្ហា។ សូមព្យាយាមម្ដងទៀត។",

        "img_instruction": "🎨 ប្រើប្រាស់: `/image ការពិពណ៌នា`",
        "img_generating": "🎨 កំពុងបង្កើតរូបភាព...",
        "img_caption": "នេះជារូបភាពរបស់អ្នក!",

        "vid_instruction": "🎬 ប្រើប្រាស់: `/video ការពិពណ៌នា`",
        "vid_generating": "🎬 កំពុងបង្កើតប្លង់វីដេអូ...",
        "vid_caption": "នេះជាប្លង់កុនរបស់អ្នក!",

        "voice_on": "🔊 មុខងារសំឡេង: **បើក**.",
        "voice_off": "🔇 មុខងារសំឡេង: **បិទ**.",
        "voice_btn_on": "🔊 សំឡេង: បើក",
        "voice_btn_off": "🔇 សំឡេង: បិទ",

        "btn_language": "ភាសា",
        "btn_help": "ជំនួយ",
        "btn_donate": "បរិច្ចាគ",
        "btn_support": "គាំទ្រ",
    },
}


def get_lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("lang", "en")


def set_lang(context: ContextTypes.DEFAULT_TYPE, lang: str) -> None:
    context.user_data["lang"] = lang


def get_voice_mode(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return context.user_data.get("voice_mode", False)


def toggle_voice_mode(context: ContextTypes.DEFAULT_TYPE) -> bool:
    current = context.user_data.get("voice_mode", False)
    context.user_data["voice_mode"] = not current
    return context.user_data["voice_mode"]


def tr(key: str, lang: str) -> str:
    return TEXTS.get(lang, TEXTS["en"]).get(key, TEXTS["en"].get(key, key))


def build_main_menu(lang: str, voice_on: bool) -> InlineKeyboardMarkup:
    voice_label = tr("voice_btn_on", lang) if voice_on else tr("voice_btn_off", lang)
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("▶️ Start / Reset", callback_data="start")],
            [
                InlineKeyboardButton(f"🌐 {tr('btn_language', lang)}", callback_data="language"),
                InlineKeyboardButton(voice_label, callback_data="toggle_voice"),
            ],
            [
                InlineKeyboardButton(f"❓ {tr('btn_help', lang)}", callback_data="help"),
                InlineKeyboardButton(f"💰 {tr('btn_donate', lang)}", callback_data="donate"),
            ],
            [InlineKeyboardButton(f"🛟 {tr('btn_support', lang)}", callback_data="support")],
        ]
    )


def build_language_menu(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(tr("lang_en_label", lang), callback_data="set_lang_en")],
            [InlineKeyboardButton(tr("lang_km_label", lang), callback_data="set_lang_km")],
        ]
    )


# ---------------------------------------------------------------------
# API Logic
# ---------------------------------------------------------------------
async def call_github_models(message: str, lang: str) -> str:
    """Text AI"""
    token = GITHUB_TOKEN
    endpoint = GITHUB_MODELS_ENDPOINT.rstrip("/")
    if not endpoint.endswith("/chat/completions"):
        endpoint += "/chat/completions"

    system_lang = "Khmer" if lang == "km" else "English"
    payload = {
        "model": GITHUB_MODELS_MODEL,
        "messages": [
            {"role": "system", "content": f"You are a helpful assistant. Answer in {system_lang}."},
            {"role": "user", "content": message},
        ],
        "temperature": 0.7,
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=40.0) as client:
        resp = await client.post(endpoint, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


async def generate_media_bytes(prompt: str, is_wide: bool = False) -> bytes:
    """
    Generates visual content.
    - is_wide=False: Square image (1024x1024) for /image
    - is_wide=True: Wide cinematic (1280x720) for /video (scene concept)
    """
    import urllib.parse
    encoded = urllib.parse.quote(prompt)
    
    if is_wide:
        # Cinematic 16:9 aspect ratio
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&model=flux&nologo=true"
    else:
        # Square 1:1
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true"

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


async def send_voice_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, lang: str):
    """Text to Speech"""
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.RECORD_VOICE)
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_file = io.BytesIO()
        tts.write_to_fp(audio_file)
        audio_file.seek(0)
        await update.message.reply_voice(voice=audio_file)
    except Exception as e:
        logger.error(f"TTS Error: {e}")


# ---------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if "lang" not in context.user_data:
        context.user_data["lang"] = "km" if (update.effective_user.language_code or "").startswith("km") else "en"
    lang = get_lang(context)
    voice_on = get_voice_mode(context)
    await update.message.reply_text(tr("welcome", lang), reply_markup=build_main_menu(lang, voice_on))


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(context)
    voice_on = get_voice_mode(context)
    await update.message.reply_text(tr("help", lang), reply_markup=build_main_menu(lang, voice_on))


async def cmd_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(context)
    await update.message.reply_text(tr("choose_language", lang), reply_markup=build_language_menu(lang))


async def cmd_donate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(context)
    voice_on = get_voice_mode(context)
    await update.message.reply_text(tr("donate", lang), reply_markup=build_main_menu(lang, voice_on))


async def cmd_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = get_lang(context)
    voice_on = get_voice_mode(context)
    await update.message.reply_text(tr("support", lang), reply_markup=build_main_menu(lang, voice_on))


async def cmd_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Standard Image Generation"""
    lang = get_lang(context)
    voice_on = get_voice_mode(context)
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text(tr("img_instruction", lang))
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
    status_msg = await update.message.reply_text(tr("img_generating", lang))
    
    try:
        # False = Square Image
        media_bytes = await generate_media_bytes(prompt, is_wide=False)
        await update.message.reply_photo(
            photo=media_bytes,
            caption=f"{tr('img_caption', lang)}\n🎨: *{prompt}*",
            parse_mode="Markdown",
            reply_markup=build_main_menu(lang, voice_on)
        )
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
    except Exception as e:
        await status_msg.edit_text(tr("error_generic", lang))


async def cmd_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Video Generation (Cinematic Scene)"""
    lang = get_lang(context)
    voice_on = get_voice_mode(context)
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text(tr("vid_instruction", lang))
        return

    # Note: Since we don't have a paid API key for real .mp4 generation,
    # we generate a High-Quality Wide-Screen Cinematic Concept.
    # If you get a paid API key later, replace generate_media_bytes with a call to that API
    # and use await update.message.reply_video(video=url)
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
    status_msg = await update.message.reply_text(tr("vid_generating", lang))
    
    try:
        # True = Wide Cinematic (16:9)
        media_bytes = await generate_media_bytes(prompt, is_wide=True)
        
        await update.message.reply_photo(
            photo=media_bytes,
            caption=f"{tr('vid_caption', lang)}\n🎬: *{prompt}*",
            parse_mode="Markdown",
            reply_markup=build_main_menu(lang, voice_on)
        )
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
    except Exception as e:
        await status_msg.edit_text(tr("error_generic", lang))


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    lang = get_lang(context)
    
    if data == "toggle_voice":
        new_state = toggle_voice_mode(context)
        msg = tr("voice_on", lang) if new_state else tr("voice_off", lang)
        await query.edit_message_text(text=msg, reply_markup=build_main_menu(lang, new_state))
        return

    voice_on = get_voice_mode(context)

    if data == "start":
        await query.message.reply_text(tr("new_chat", lang), reply_markup=build_main_menu(lang, voice_on))
    elif data == "language":
        await query.message.reply_text(tr("choose_language", lang), reply_markup=build_language_menu(lang))
    elif data == "help":
        await query.message.reply_text(tr("help", lang), reply_markup=build_main_menu(lang, voice_on))
    elif data == "donate":
        await query.message.reply_text(tr("donate", lang), reply_markup=build_main_menu(lang, voice_on))
    elif data == "support":
        await query.message.reply_text(tr("support", lang), reply_markup=build_main_menu(lang, voice_on))
    elif data == "set_lang_en":
        set_lang(context, "en")
        await query.message.reply_text(tr("lang_changed_en", "en"), reply_markup=build_main_menu("en", voice_on))
    elif data == "set_lang_km":
        set_lang(context, "km")
        await query.message.reply_text(tr("lang_changed_km", "km"), reply_markup=build_main_menu("km", voice_on))


async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    lang = get_lang(context)
    voice_on = get_voice_mode(context)
    user_text = update.message.text.strip()

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    try:
        ai_reply = await call_github_models(user_text, lang)
    except Exception as e:
        logger.exception("AI Error: %s", e)
        ai_reply = tr("error_generic", lang)

    await update.message.reply_text(ai_reply, reply_markup=build_main_menu(lang, voice_on))

    if voice_on and ai_reply:
        await send_voice_reply(update, context, ai_reply, lang)


# ---------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------
def main() -> None:
    if not TELEGRAM_TOKEN:
        raise RuntimeError("Please set TELEGRAM_TOKEN.")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("language", cmd_language))
    app.add_handler(CommandHandler("donate", cmd_donate))
    app.add_handler(CommandHandler("support", cmd_support))
    
    # Media Commands
    app.add_handler(CommandHandler("image", cmd_image))
    app.add_handler(CommandHandler("video", cmd_video))

    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_message))

    logger.info("Bot is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()