# Simple AFK system plugin
import time
from typing import Dict

from pyrogram import filters

from Elevenyts import app

# In-memory AFK storage: user_id -> {reason, since, name}
AFK: Dict[int, Dict] = {}


def _format_duration(seconds: float) -> str:
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    parts = []
    if d:
        parts.append(f"{d}d")
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)


@app.on_message(filters.command(["afk"]) & ~app.bl_users)
async def set_afk(_, message):
    user = message.from_user
    if not user:
        return
    reason = " ".join(message.command[1:]) if message.command and len(message.command) > 1 else "Away"
    AFK[user.id] = {"reason": reason, "since": time.time(), "name": user.first_name or user.username or str(user.id)}
    await message.reply_text(f"{AFK[user.id]['name']} is now AFK: {reason}")


@app.on_message(filters.command(["back", "unafk"]) & ~app.bl_users)
async def remove_afk_cmd(_, message):
    user = message.from_user
    if not user:
        return
    if user.id in AFK:
        AFK.pop(user.id, None)
        await message.reply_text("Welcome back! I removed your AFK status.")
    else:
        await message.reply_text("You were not marked as AFK.")


@app.on_message(filters.text & ~app.bl_users)
async def afk_handler(_, message):
    # If an AFK user sends any message, consider them back
    user = message.from_user
    if user and user.id in AFK:
        AFK.pop(user.id, None)
        await message.reply_text("Welcome back! I removed your AFK status.")
        return

    # If the message replies to someone who is AFK, notify
    if message.reply_to_message and message.reply_to_message.from_user:
        ru = message.reply_to_message.from_user
        if ru.id in AFK:
            info = AFK[ru.id]
            dur = _format_duration(time.time() - info["since"])
            await message.reply_text(f"{info['name']} is AFK: {info['reason']} (since {dur} ago)")
            return

    # Check for text_mention entities (explicit user objects)
    if message.entities:
        for ent in message.entities:
            if ent.type == "text_mention" and getattr(ent, "user", None):
                tu = ent.user
                if tu.id in AFK:
                    info = AFK[tu.id]
                    dur = _format_duration(time.time() - info["since"])
                    await message.reply_text(f"{info['name']} is AFK: {info['reason']} (since {dur} ago)")
                    return
