#!/usr/bin/env python3
import json
import logging
import os
from typing import Dict, List, Any, Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration file path
CONFIG_FILE = "config.json"


class ForwardingBot:
    def __init__(self, config_path: str = CONFIG_FILE):
        self.config_path = config_path
        self.config = self.load_config()

        # Extract configuration values
        self.token = self.config["token"]
        self.admin_id = self.config["admin_id"]
        self.target_channel = self.config["target_channel"]
        self.source_channels = self.config["source_channels"]

        # Initialize the application
        self.application = Application.builder().token(self.token).build()

        # Add handlers
        self.setup_handlers()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            logger.error(f"Configuration file {self.config_path} not found.")
            # Create a default config file
            default_config = {
                "token": "YOUR_BOT_TOKEN",
                "admin_id": 123456789,
                "target_channel": "@your_target_channel",
                "source_channels": [],
            }
            with open(self.config_path, "w") as file:
                json.dump(default_config, file, indent=2)
            return default_config
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in configuration file {self.config_path}.")
            raise

    def save_config(self) -> None:
        """Save current configuration to JSON file."""
        # Update the config dictionary with current values
        self.config["admin_id"] = self.admin_id
        self.config["target_channel"] = self.target_channel
        self.config["source_channels"] = self.source_channels

        # Write to file
        with open(self.config_path, "w") as file:
            json.dump(self.config, file, indent=2)
        logger.info("Configuration saved successfully.")

    def setup_handlers(self) -> None:
        """Set up message and command handlers."""
        # Command handlers (admin only)
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(
            CommandHandler("add_channel", self.cmd_add_channel)
        )
        self.application.add_handler(
            CommandHandler("remove_channel", self.cmd_remove_channel)
        )
        self.application.add_handler(
            CommandHandler("list_channels", self.cmd_list_channels)
        )

        # Message handler for forwarding messages
        self.application.add_handler(
            MessageHandler(
                filters.ChatType.CHANNEL & ~filters.COMMAND, self.forward_message
            )
        )

        # Error handler
        self.application.add_error_handler(self.error_handler)

    async def cmd_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Send a welcome message when the command /start is issued."""
        if not update.effective_user or update.effective_user.id != self.admin_id:
            return

        await update.message.reply_text(
            "Welcome to the Channel Forwarding Bot!\n\n"
            "Use /help to see available commands."
        )

    async def cmd_help(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Send a help message when the command /help is issued."""
        if not update.effective_user or update.effective_user.id != self.admin_id:
            return

        await update.message.reply_text(
            "Available commands:\n\n"
            "/add_channel CHANNEL_ID - Add a channel to forward messages from\n"
            "/remove_channel CHANNEL_ID - Remove a channel from the list\n"
            "/list_channels - Show all channels being monitored\n"
            "/help - Show this help message"
        )

    async def cmd_add_channel(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Add a channel to the source channels list."""
        if not update.effective_user or update.effective_user.id != self.admin_id:
            return

        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "Please provide a channel ID or username.\n"
                "Example: /add_channel @channel_name or /add_channel -1001234567890"
            )
            return

        channel_id = context.args[0]

        # Check if channel is already in the list
        if channel_id in self.source_channels:
            await update.message.reply_text(
                f"Channel {channel_id} is already in the list."
            )
            return

        # Add channel to the list
        self.source_channels.append(channel_id)
        self.save_config()

        await update.message.reply_text(f"Channel {channel_id} added successfully.")

    async def cmd_remove_channel(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Remove a channel from the source channels list."""
        if not update.effective_user or update.effective_user.id != self.admin_id:
            return

        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "Please provide a channel ID or username.\n"
                "Example: /remove_channel @channel_name or /remove_channel -1001234567890"
            )
            return

        channel_id = context.args[0]

        # Check if channel is in the list
        if channel_id not in self.source_channels:
            await update.message.reply_text(f"Channel {channel_id} is not in the list.")
            return

        # Remove channel from the list
        self.source_channels.remove(channel_id)
        self.save_config()

        await update.message.reply_text(f"Channel {channel_id} removed successfully.")

    async def cmd_list_channels(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """List all source channels."""
        if not update.effective_user or update.effective_user.id != self.admin_id:
            return

        if not self.source_channels:
            await update.message.reply_text(
                "No channels are currently being monitored."
            )
            return

        channels_text = "\n".join([f"- {channel}" for channel in self.source_channels])
        await update.message.reply_text(
            f"Currently monitoring the following channels:\n\n{channels_text}"
        )

    def has_media_attachment(self, message) -> bool:
        """Check if a message has any media attachments."""
        if not message:
            return False
            
        # Check for various types of media attachments
        media_attributes = [
            'photo', 'video', 'document', 'audio', 'animation',
            'sticker', 'voice', 'video_note', 'contact', 'location',
            'venue', 'poll', 'dice', 'game', 'invoice', 'successful_payment'
        ]
        
        return any(getattr(message, attr, None) for attr in media_attributes)

    async def forward_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Forward messages from source channels to the target channel."""
        if not update.effective_chat or not update.effective_message:
            return

        # Get the chat ID of the source channel
        source_chat_id = update.effective_chat.id
        source_chat_username = update.effective_chat.username

        # Check if this channel is in our source channels list
        source_identifier = (
            f"@{source_chat_username}" if source_chat_username else str(source_chat_id)
        )

        if (
            source_identifier not in self.source_channels
            and str(source_chat_id) not in self.source_channels
        ):
            logger.debug(f"Message from non-monitored channel: {source_identifier}")
            return
            
        # Check if the message has media attachments
        if not self.has_media_attachment(update.effective_message):
            logger.info(f"Skipping plain text message from {source_identifier}")
            return

        # Forward the message to the target channel
        try:
            await update.effective_message.forward(chat_id=self.target_channel)
            logger.info(
                f"Message with media forwarded from {source_identifier} to {self.target_channel}"
            )
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")

    async def error_handler(
        self, update: object, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Log errors caused by updates."""
        logger.error(f"Update caused error: {context.error}")

    def run(self) -> None:
        """Run the bot until the user presses Ctrl-C."""
        logger.info("Starting bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    bot = ForwardingBot()
    bot.run()
