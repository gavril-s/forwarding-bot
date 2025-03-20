# Telegram Channel Forwarding Bot

A simple Telegram bot that forwards messages from specified channels to a target channel.

## Features

- Forward messages from multiple source channels to a target channel
- Configure source channels via direct messages with the bot (admin only)
- Simple JSON-based configuration without requiring a database

## Setup

1. Clone this repository
2. Create a virtual environment and install dependencies:
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Create a Telegram bot using [BotFather](https://t.me/botfather) and get your API token
4. Add the bot to your source and target channels with admin privileges
5. Create a `config.json` file with the following structure:
   ```json
   {
     "token": "YOUR_BOT_TOKEN",
     "admin_id": YOUR_TELEGRAM_USER_ID,
     "target_channel": "YOUR_TARGET_CHANNEL_ID",
     "source_channels": []
   }
   ```
6. Run the bot:
   ```
   python main.py
   ```

## Admin Commands

- `/add_channel CHANNEL_ID` - Add a channel to the source channels list
- `/remove_channel CHANNEL_ID` - Remove a channel from the source channels list
- `/list_channels` - List all source channels
- `/help` - Show available commands

## Requirements

- Python 3.7+
- python-telegram-bot library

## License

MIT
