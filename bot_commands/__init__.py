# Instagram Telegram Bot Commands Module
"""
This module contains all the command handlers for the Instagram Telegram Bot.

Modules:
- insta_info: Instagram user information and password reset
- meth_analyzer: Instagram account analysis tool
- report_tool: Instagram reporting automation
- session_manager: Instagram session ID generator
"""

__version__ = "1.0.0"
__author__ = "Instagram Bot Developer"

# Import all command setup functions
from .insta_info import setup_insta_commands
from .meth_analyzer import setup_meth_commands
from .report_tool import setup_report_commands
from .session_manager import setup_session_commands

__all__ = [
    'setup_insta_commands',
    'setup_meth_commands', 
    'setup_report_commands',
    'setup_session_commands'
]
