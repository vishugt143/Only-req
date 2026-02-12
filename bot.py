# Don't Remove Credit @teacher_slex
# Modified Clean Version

from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import filters, Client, errors
from pyrogram.errors.exceptions.flood_420 import FloodWait
from database import add_user, add_group, all_users, all_groups, users
from configs import cfg
import asyncio
import re

app = Client(
    "approver",
    api_id=cfg.API_ID,
    api_hash=cfg.API_HASH,
    bot_token=cfg.BOT_TOKEN
)

#━━━━━━━━━━━━━━━━━━━━ JOIN REQUEST (10 SEC DELAY) ━━━━━━━━━━━━━━━━━━━━
@app.on_chat_join_request(filters.group | filters.channel)
async def approve(_, m):
    chat = m.chat
    user = m.from_user

    try:
        add_group(chat.id)
        add_user(user.id)

        # ⏳ 10 SECOND DELAY
        await asyncio.sleep(10)

        # ✅ APPROVE REQUEST
        await app.approve_chat_join_request(chat.id, user.id)

        # ✅ WELCOME MESSAGE
        await app.send_message(
            user.id,
            f"👋 Hello {user.first_name}!\n\n"
            "✅ Aapka join request approve ho gaya hai.\n"
            "🎉 Welcome to the group!"
        )

    except FloodWait as e:
        await asyncio.sleep(e.value)
    except errors.PeerIdInvalid:
        pass
    except:
        pass
#━━━━━━━━━━━━━━━━━━━━ ILLEGAL WORD DELETE (NO BAN) ━━━━━━━━━━━━━━━━━━━━
@app.on_message(filters.group & filters.text)
async def illegal_filter(_, m: Message):

    if not m.from_user:
        return

    # 🔹 SUDO exempt
    if m.from_user.id in cfg.SUDO:
        return

    text = m.text.lower()

    for word in cfg.ILLEGAL_WORDS:
        pattern = r"\b" + re.escape(word.lower()) + r"\b"
        if re.search(pattern, text):
            try:
                await m.delete()

                await m.chat.send_message(
                    f"⚠️ {m.from_user.mention}, illegal words allowed nahi hain."
                )
            except:
                pass
            break


#━━━━━━━━━━━━━━━━━━━━ START COMMAND ━━━━━━━━━━━━━━━━━━━━
@app.on_message(filters.private & filters.command("start"))
async def start(_, m: Message):
    add_user(m.from_user.id)

    await m.reply_text(
        "🤖 Hello!\n\n"
        "Main auto approve bot hoon."
    )


#━━━━━━━━━━━━━━━━━━━━ USERS COUNT ━━━━━━━━━━━━━━━━━━━━
@app.on_message(filters.command("users") & filters.user(cfg.SUDO))
async def users_count(_, m: Message):
    u = all_users()
    g = all_groups()
    await m.reply_text(f"🙋 Users : `{u}`\n👥 Groups : `{g}`\n📊 Total : `{u+g}`")


#━━━━━━━━━━━━━━━━━━━━ BROADCAST ━━━━━━━━━━━━━━━━━━━━
@app.on_message(filters.command("bcast") & filters.user(cfg.SUDO))
async def bcast(_, m: Message):

    if not m.reply_to_message:
        return await m.reply("Reply to a message to broadcast.")

    status = await m.reply("⚡ Broadcasting...")
    ok = fail = 0

    for u in users.find():
        try:
            await m.reply_to_message.copy(u["user_id"])
            ok += 1
        except:
            fail += 1

    await status.edit(f"✅ {ok} | ❌ {fail}")


print("🤖 Bot is Alive!")
app.run()
