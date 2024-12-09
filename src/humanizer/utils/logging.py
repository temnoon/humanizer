# src/humanizer/utils/logging.py
import logging
from typing import Optional

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get configured logger instance"""
    logger = logging.getLogger(name or "humanizer")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
