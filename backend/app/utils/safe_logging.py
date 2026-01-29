"""
Safe Logging Utility - Windows-Compatible Logging

This module provides emoji-free logging functions to prevent encoding issues.
All emojis are replaced with ASCII equivalents.
"""

import logging
from typing import Any


def safe_log_info(logger: logging.Logger, message: str, *args: Any) -> None:
    """Log info message with emoji replacement"""
    safe_message = _replace_emojis(message)
    logger.info(safe_message, *args)


def safe_log_error(logger: logging.Logger, message: str, *args: Any) -> None:
    """Log error message with emoji replacement"""
    safe_message = _replace_emojis(message)
    logger.error(safe_message, *args)


def safe_log_warning(logger: logging.Logger, message: str, *args: Any) -> None:
    """Log warning message with emoji replacement"""
    safe_message = _replace_emojis(message)
    logger.warning(safe_message, *args)


def safe_log_debug(logger: logging.Logger, message: str, *args: Any) -> None:
    """Log debug message with emoji replacement"""
    safe_message = _replace_emojis(message)
    logger.debug(safe_message, *args)


def _replace_emojis(message: str) -> str:
    """Replace emojis with ASCII equivalents"""
    emoji_replacements = {
        "🎯": "[TARGET]",
        "🔄": "[RETRY]", 
        "✅": "[OK]",
        "❌": "[ERROR]",
        "⚠️": "[WARNING]",
        "🚨": "[CRITICAL]",
        "🎉": "[SUCCESS]",
        "🔍": "[CHECK]",
        "🚫": "[BLOCKED]",
        "🏥": "[HEALTH]",
        "💡": "[INFO]",
        "📊": "[DATA]",
        "🧪": "[TEST]",
        "🔧": "[FIX]",
        "🛡️": "[GUARD]",
        "⭐": "[STAR]",
        "🚀": "[LAUNCH]",
        "📋": "[LIST]",
        "🔐": "[SECURE]",
        "♻️": "[CACHE]",
        "🧩": "[PUZZLE]",
        "🎨": "[DESIGN]",
        "📈": "[METRICS]",
        "🔔": "[NOTIFY]",
        "💾": "[SAVE]",
        "🗂️": "[FILE]",
        "🌟": "[FEATURE]",
        "⏰": "[TIME]",
        "🎪": "[EVENT]",
        "🔮": "[PREDICT]",
        "🎭": "[MOCK]",
        "🏆": "[WINNER]",
        "🎲": "[RANDOM]",
        "🔬": "[ANALYZE]",
        "📝": "[NOTE]",
        "🎵": "[AUDIO]",
        "🖼️": "[IMAGE]",
        "📱": "[MOBILE]",
        "💻": "[DESKTOP]",
        "🌐": "[WEB]",
        "📡": "[NETWORK]",
        "🔌": "[PLUGIN]",
        "⚡": "[FAST]",
        "🔥": "[HOT]",
        "❄️": "[COLD]",
        "🌈": "[COLOR]",
        "🎪": "[CIRCUS]",
        "🎨": "[ART]",
        "🎭": "[THEATER]",
        "🎪": "[CARNIVAL]"
    }
    
    safe_message = message
    for emoji, replacement in emoji_replacements.items():
        safe_message = safe_message.replace(emoji, replacement)
    
    return safe_message


# Convenience functions for common patterns
def log_success(logger: logging.Logger, message: str, *args: Any) -> None:
    """Log success message"""
    safe_log_info(logger, f"[OK] {message}", *args)


def log_error(logger: logging.Logger, message: str, *args: Any) -> None:
    """Log error message"""
    safe_log_error(logger, f"[ERROR] {message}", *args)


def log_warning(logger: logging.Logger, message: str, *args: Any) -> None:
    """Log warning message"""
    safe_log_warning(logger, f"[WARNING] {message}", *args)


def log_retry(logger: logging.Logger, message: str, *args: Any) -> None:
    """Log retry message"""
    safe_log_info(logger, f"[RETRY] {message}", *args)


def log_target(logger: logging.Logger, message: str, *args: Any) -> None:
    """Log target/goal message"""
    safe_log_info(logger, f"[TARGET] {message}", *args)