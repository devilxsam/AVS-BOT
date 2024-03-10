# main.py

import asyncio
import json
import random
import os
import cv2
from telethon import TelegramClient, events, types
from telethon.errors import TimedOutError
import subprocess

# Import configurations from config.py
from config import *

# Load existing user data from the JSON file
try:
    with open(USER_DATA_JSON_FILE, "r") as file:
        user_data = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    # Handle the case when the file is not found or not in the expected JSON format
    user_data = []

# Dictionary to track whether a video is currently being processed for a user
user_video_processing = {}
# Queue to manage command requests
command_queue = asyncio.Queue()

bot = TelegramClient("tele", API_ID, API_HASH)

@bot.on(
    events.NewMessage(
        pattern="/start",
        incoming=True,
        outgoing=False,
        func=lambda x: x.is_private,
    )
)
async def start(event):
    try:
        user_id = event.sender_id

        # Check if user already exists in user_data list
        user_entry = next((user for user in user_data if user["user_id"] == user_id), None)

        if user_entry is None:
            # If user doesn't exist, add a new entry
            user_data.append({"user_id": user_id, "username": event.sender.username, "usage_count": 0})
        else:
            # If user already exists, increment the usage count
            user_entry["usage_count"] += 1

        # Save updated user data to the JSON file
        with open(USER_DATA_JSON_FILE, "w") as file:
            json.dump(user_data, file)

        # Rest of your existing /start logic
        await event.reply(START_MESSAGE, parse_mode="markdown")

    except Exception as e:
        print(f"Error in /start command: {e}")
        await event.reply("An error occurred. Please try again later.")

@bot.on(
    events.NewMessage(
        pattern="/broadcast",
        incoming=True,
        outgoing=True,
    )
)
async def broadcast(event):
    try:
        if event.sender_id != ADMIN_USER_ID:
            # If user is not the admin, inform the user and exit
            await event.reply(UNAUTHORIZED_ERROR_MESSAGE)
            return

        # Extract the message from the command or from the reply
        _, *message_args = event.message.text.split(" ", 1)
        message_text = message_args[0] if message_args else None

        if not message_text and event.reply_to_msg_id:
            # If no message provided and there's a reply, use the replied message as the broadcast message
            reply_message = await event.get_reply_message()
            message_text = reply_message.text if reply_message.text else None

        if not message_text:
            # If no message is provided and there's no reply, inform the admin and exit
            await event.reply(NO_MESSAGE_PROVIDED_ERROR)
            return

        # Iterate through user IDs and send the broadcast message
        for user_info in user_data:
            user_id = user_info["user_id"]

            # Skip sending the broadcast message to the admin
            if user_id == ADMIN_USER_ID:
                continue

            try:
                await bot.send_message(user_id, message_text)
            except Exception as e:
                print(f"Error sending broadcast message to user {user_id}: {e}")

        # Inform the admin about the completion of the broadcast
        await event.reply(BROADCAST_SUCCESS_MESSAGE)

    except Exception as e:
        print(f"Error in /broadcast command: {e}")
        await event.reply(BROADCAST_ERROR_MESSAGE)

@bot.on(events.NewMessage(pattern="/get_random_media$", incoming=True, outgoing=False))
async def get_random_media(event):
    try:
        user_id = event.sender_id

        if user_id in user_video_processing and user_video_processing[user_id]:
            raise ValueError(PROCESSING_MESSAGE)

        # Set flag to indicate video processing
        user_video_processing[user_id] = True

        # Enqueue the command request
        await command_queue.put((event, user_id))

        # Inform the user that the video is being sent
        await event.reply(PLEASEWAIT_MESSAGE)

    except ValueError as ve:
        await event.reply(str(ve))
    except Exception as e:
        print(f"Error getting or sending random media: {e}")
        await event.reply("An error occurred. Please try again later.")

@bot.on(events.NewMessage(pattern="/users", incoming=True, outgoing=False))
async def get_users(event):
    try:
        if event.sender_id != ADMIN_USER_ID:
            # If user is not the admin, inform the user and exit
            await event.reply(UNAUTHORIZED_ERROR_MESSAGE)
            return

        # Get the list of user IDs and their usage counts
        users_info = [(user_info["user_id"], user_info["usage_count"]) for user_info in user_data]

        # Calculate the total number of users
        total_users = len(users_info)

        # Create a formatted message with user IDs and usage counts
        users_message = "\n".join([f"User ID: {user_id}, Usage Count: {usage_count}" for user_id, usage_count in users_info])

        # Send the message to the admin
        await event.reply(f"Total Users: {total_users}\nList of Users:\n{users_message}")

    except Exception as e:
        print(f"Error in /users command: {e}")
        await event.reply("An error occurred while fetching user data. Please try again later.")

async def process_command_queue():
    while True:
        # Dequeue the command request
        event, user_id = await command_queue.get()

        try:
            channel_id = PRIVATE_CHANNEL_ID
            message_id = random.randint(1, TOTAL_FILES)

            retries = 3
            for attempt in range(retries):
                try:
                    message = await bot.get_messages(channel_id, ids=message_id)
                    if message.media:
                        await download_and_send_media(event, message)
                        break  # Break the loop if successful
                    else:
                        user_video_processing[user_id] = False  # Reset flag if no media found
                except TimedOutError as e:
                    print(f"Timed out, retrying ({attempt + 1}/{retries})...")
                    await asyncio.sleep(5)  # Wait for a few seconds before retrying
            else:
                # If all retries fail, handle the error or raise an exception
                raise Exception("Failed to download media after multiple attempts.")

        except Exception as e:
            print(f"Error getting or sending random media: {e}")
            await event.reply("An error occurred. Please try again later.")

        finally:
            user_video_processing[user_id] = False  # Reset flag after processing
            command_queue.task_done()

async def download_and_send_media(event, media_message):
    try:
        file_path = await bot.download_media(media_message)
        file_size_bytes = os.path.getsize(file_path)
        file_size_mb = file_size_bytes / (1024 * 1024)
        random_number = random.randint(1000, 9999)

        # Generate thumbnail
        thumbnail_path = generate_thumbnail(file_path)

        caption = f"Title: TADxBotz_Video_no_{random_number}\nFile Size: {file_size_mb:.2f} MB\n\nEnjoy the video ❤️"

        await bot.send_file(event.chat_id, file_path, caption=caption, thumb=thumbnail_path)

        # Optionally, delete the downloaded file and thumbnail to save space
        os.remove(file_path)
        os.remove(thumbnail_path)

    except Exception as e:
        print(f"Error sending media to user: {e}")
        await event.reply("An error occurred while sending media. Please try again later.")

# Update the /totalvideo command to change TOTAL_FILES in config.py
@bot.on(events.NewMessage(pattern="/totalvideo", incoming=True, outgoing=False))
async def update_total_files(event):
    try:
        if event.sender_id != ADMIN_USER_ID:
            await event.reply(UNAUTHORIZED_ERROR_MESSAGE)
            return

        _, *value_args = event.message.text.split(" ", 1)
        new_total_files = int(value_args[0]) if value_args else None

        if new_total_files is not None:
            # Update the TOTAL_FILES in config.py
            with open("config.py", "r", encoding="utf-8") as config_file:
                config_lines = config_file.readlines()

            with open("config.py", "w", encoding="utf-8") as config_file:
                for line in config_lines:
                    if "TOTAL_FILES" in line:
                        config_file.write(f'TOTAL_FILES = {new_total_files}\n')
                    else:
                        config_file.write(line)

            # Restart the bot using subprocess
            subprocess.run(["python", "main.py"])

            await event.reply(f"Total files updated to {new_total_files}. Bot is restarting...")

        else:
            await event.reply("Invalid command format. Please use /totalvideo {value}")

    except Exception as e:
        print(f"Error in /totalvideo command: {e}")
        await event.reply("An error occurred. Please try again later.")      

def generate_thumbnail(video_path, output_path='thumbnail.jpg'):
    try:
        # Open the video file
        cap = cv2.VideoCapture(video_path)

        # Read the first frame
        ret, frame = cap.read()

        # Resize the frame to create the thumbnail
        thumbnail = cv2.resize(frame, (320, 240))  # You can adjust the size as needed

        # Save the thumbnail as an image file
        cv2.imwrite(output_path, thumbnail)

        # Release the video capture object
        cap.release()

        return output_path

    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return None

async def main():
    try:
        # Start the command processing loop
        command_processing_task = asyncio.create_task(process_command_queue())

        # Start the bot
        await bot.start(bot_token=BOT_TOKEN)
        await bot.run_until_disconnected()

        # Wait for the command processing loop to complete
        await command_processing_task

    except KeyboardInterrupt:
        print("Bot manually stopped. Performing cleanup...")
        await bot.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
