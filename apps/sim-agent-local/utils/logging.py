#!/usr/bin/env python3
"""
Logging configuration for Local SIM Agent API

Provides structured logging with proper formatting and levels.
"""

import logging
import sys
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console

def setup_logging(level: str = "INFO", format_type: str = "rich") -> None:
    """Setup logging configuration
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        format_type: Format type ('rich' for development, 'json' for production)
    """
    # Clear any existing handlers
    logging.getLogger().handlers.clear()
    
    # Set logging level
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    if format_type == "rich":
        # Rich handler for development
        console = Console(stderr=True)
        handler = RichHandler(
            console=console,
            show_time=True,
            show_path=True,
            markup=True,
            rich_tracebacks=True
        )
        
        formatter = logging.Formatter(
            fmt="%(message)s",
            datefmt="[%X]"
        )
    else:
        # Standard handler for production
        handler = logging.StreamHandler(sys.stdout)
        
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)
    
    # Configure specific loggers
    configure_loggers(log_level)

def configure_loggers(level: int) -> None:
    """Configure specific logger levels"""
    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # Set our application loggers
    logging.getLogger("main").setLevel(level)
    logging.getLogger("services").setLevel(level)
    logging.getLogger("api").setLevel(level)
    logging.getLogger("utils").setLevel(level)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)