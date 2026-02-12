# Don't Remove Credit @teacher_slex
# Subscribe YouTube ƈɦǟռռɛʟ For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

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

#━━━━━━━━━━━━━━━━━━━━ HELPER ━━━━━━━━━━━━━━━━━━━━
def parse_post_link(link: str):
    parts = link.split("/")
    chat = parts[-2]
    msg_id = int(parts[-1])
    return chat, msg_id

#━━━━━━━━━━━━━━━━━━━━ JOIN REQUEST (10 SEC DELAY APPROVE + WELCOME) ━━━━━━━━━━━━━━━━━━━━
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

        # ✅ ONLY WELCOME MESSAGE (NO PROMO)
        try:
            await app.send_message(
                user.id,
                f"👋 Hello {user.first_name}!\n\n"
                "✅ Aapka join request approve ho gaya hai.\n"
                "🎉 Welcome to the group!"
            )
        except:
            # user might have privacy settings; ignore
            pass

    except FloodWait as e:
        await asyncio.sleep(e.value)
    except errors.PeerIdInvalid:
        pass
    except:
        pass

#━━━━━━━━━━━━━━━━━━━━ ILLEGAL WORD DELETE IN GROUP (NO BAN) ━━━━━━━━━━━━━━━━━━━━
@app.on_message(filters.group & filters.text)
async def illegal_filter(_, m: Message):

    if not m.from_user:
        return

    # 🔹 SUDO exempt
    if m.from_user.id in cfg.SUDO:
        return

    text = (m.text or "").lower()

    for word in cfg.ILLEGAL_WORDS:
        pattern = r"\b" + re.escape(word.lower()) + r"\b"
        if re.search(pattern, text):
            try:
                # delete offending message
                await m.delete()

                # warn in group (best-effort)
                try:
                    await m.chat.send_message(
                        f"⚠️ {m.from_user.mention}, aise shabd allowed nahi hain. Aapka message delete kar diya gaya."
                    )
                except:
                    # ignore if cannot send (e.g., no permissions)
                    pass
            except:
                pass
            break

#━━━━━━━━━━━━━━━━━━━━ AUTO-DELETE FOR MY MESSAGES (filters.me) ━━━━━━━━━━━━━━━━━━━━
@app.on_message(filters.me)
async def auto_delete_illegal(_, m: Message):
    try:
        content = ""
        if m.text:
            content = m.text.lower()
        elif m.caption:
            content = m.caption.lower()

        for word in cfg.ILLEGAL_WORDS:
            if word.lower() in content:
                await asyncio.sleep(0.1)
                await m.delete()
                return
    except:
        pass

#━━━━━━━━━━━━━━━━━━━━ START COMMAND ━━━━━━━━━━━━━━━━━━━━
@app.on_message(filters.private & filters.command("start"))
async def start(_, m: Message):
    add_user(m.from_user.id)

    if m.from_user.id not in cfg.SUDO:
        await m.reply_text(
            "𝐁𝐇𝐀𝐈 𝐇𝐀𝐂𝐊 𝐒𝐄 𝐏𝐋𝐀𝐘 𝐊𝐑𝐎\n\n💸𝐏𝐑𝐎𝐅𝐈𝐓 𝐊𝐑𝐎🍻"
        )
        return

    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("🗯 ƈɦǟռռɛʟ", url="https://t.me/lnx_store"),
            InlineKeyboardButton("💬 Support", url="https://t.me/teacher_slex")
        ]]
    )

    await m.reply_photo(
        photo="https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhsaR6kRdTPF2ZMEgmgSYjjXU6OcsJhkBe1EWtI1nfbOziINTYzxjlGCMSVh-KoH05Z8MpRWhVV9TIX_ykpjdeGqJ1atXy1TUqrVkohUxlykoZyl67EfMQppHoWYrdHmdi6FMcL9v-Vew2VtaWHWY_eGZt-GN057jLGvYj7UV49g0rXVxoDFXQAYxvaX1xP/s1280/75447.jpg",
        caption=(
            f"**🦊 Hello {m.from_user.mention}!**\n\n"
            "I'm an auto approve bot.\n"
            "I handle join requests & DM users.\n\n"
            "📢 Broadcast : /bcast\n"
            "📊 Users : /users\n\n"
            "__Powered By : @teacher_slex__"
        ),
        reply_markup=keyboard
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
