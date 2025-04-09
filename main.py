from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.errors import ChatAdminRequiredError

# === STEP 1: FILL IN YOUR DETAILS BELOW ===
api_id = 123456           # <--- Your Telegram API ID (from my.telegram.org)
api_hash = 'your_api_hash_here'  # <--- Your API Hash
channel_username = 'your_channel_username'  # No @, just the username or ID
keep_ids = [111, 222]     # List of message IDs to keep (add your safe ones here)

# === DO NOT EDIT BELOW UNLESS YOU KNOW WHAT YOU'RE DOING ===
with TelegramClient('channel_cleaner_session', api_id, api_hash) as client:
    # Get channel entity
    channel = client.get_entity(channel_username)

    # Get pinned message ID
    try:
        full = client(GetFullChannelRequest(channel))
        pinned_id = full.full_chat.pinned_msg_id
        if pinned_id:
            keep_ids.append(pinned_id)
            print(f"✔️ Pinned message found and protected (ID: {pinned_id})")
    except Exception as e:
        print(f"⚠️ Could not fetch pinned message: {e}")

    # Start deleting messages
    deleted = 0
    skipped = 0

    for message in client.iter_messages(channel):
        if message.id in keep_ids:
            print(f"⏭️ Skipping protected message ID: {message.id}")
            skipped += 1
            continue
        try:
            client.delete_messages(channel, message.id)
            print(f"🗑️ Deleted message ID: {message.id}")
            deleted += 1
        except ChatAdminRequiredError:
            print("❌ Bot doesn't have delete permissions. Make sure your account is admin.")
            break
        except Exception as e:
            print(f"⚠️ Error deleting message ID {message.id}: {e}")

    print(f"\n✅ Done! Deleted: {deleted}, Skipped: {skipped}")
