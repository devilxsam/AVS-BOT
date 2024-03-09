# config.py

# Telegram API credentials
API_ID = 22741640  # Replace with your API ID
API_HASH = "c435fe7ad0a6398ccd9337839a3666e3"  # Replace with your API hash
BOT_TOKEN = "7107471730:AAHtTEMsmBEpHX_RqltdfH1v2UoUvfnJAwA"  # Replace with your bot token

# Channel settings
PRIVATE_CHANNEL_ID = -1002124678832  # Replace with the actual ID of your private channel

# Thumbnail settings
THUMBNAIL_SIZE = (320, 240)  # Adjust the size of the thumbnail as needed

# Other constants
MAX_RETRY_ATTEMPTS = 3  # Maximum number of retry attempts for downloading media
WAIT_TIME_BETWEEN_RETRIES = 5  # Wait time (in seconds) between retry attempts

# JSON file settings
USER_DATA_JSON_FILE = "user_data_list.json"  # Path to the JSON file to store user data

# Admin user ID
ADMIN_USER_ID = 6271019610  # Replace with your admin user ID

# Messages
START_MESSAGE = "Hello! I am Terabox Video Downloader Bot. Send me '/get_random_media' to receive a random media file from the private channel."

PROCESSING_MESSAGE = "Please wait, the video is being processed. This may take a moment."

BROADCAST_SUCCESS_MESSAGE = "Broadcast completed successfully."

NO_MESSAGE_PROVIDED_ERROR = "Error: No message provided."

UNAUTHORIZED_ERROR_MESSAGE = "You are not authorized to use the /broadcast command. Please contact the admin @TADxAdminBot."

BROADCAST_ERROR_MESSAGE = "An error occurred during the broadcast."
