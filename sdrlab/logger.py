"""
Logging module for SDRLab.
Handles application and simulation logging, custom formats, and outputs to console and files.
"""

import logging
import os
from pathlib import Path
from typing import Optional


class SDRLabLogger:
    """
    Centralized logger configuration class for the SDRLab framework.
    Manages console outputs and log file rotation directories under outputs/logs/.
    """

    _logger: Optional[logging.Logger] = None

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """
        Returns the SDRLab root logger. If not initialized, sets it up with defaults.
        """
        if cls._logger is None:
            cls.setup_logger()
        return cls._logger

    @classmethod
    def setup_logger(
        cls,
        output_dir: str = "outputs",
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
    ) -> logging.Logger:
        """
        Sets up console and file logging. Creates outputs/logs/ if it doesn't exist.
        
        Args:
            output_dir: Root directory for outputting files.
            console_level: Logger level for the console.
            file_level: Logger level for the file handler.
            
        Returns:
            logging.Logger: The configured Logger instance.
        """
        logger = logging.getLogger("sdrlab")
        logger.setLevel(logging.DEBUG)  # Capture all logs at root level

        # Clear existing handlers if already configured
        if logger.handlers:
            for handler in list(logger.handlers):
                handler.close()
                logger.removeHandler(handler)

        # Create output logs directory
        log_dir = Path(output_dir) / "logs"
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # Fallback to current directory if permission error
            log_dir = Path("logs")
            log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "simulation.log"

        # Log formatters
        console_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s"
        )

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File Handler
        try:
            file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
            file_handler.setLevel(file_level)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not create file log handler: {e}")

        cls._logger = logger
        return logger

    @classmethod
    def shutdown(cls) -> None:
        """Closes all log handlers to release file locks (especially on Windows)."""
        if cls._logger is not None:
            for handler in list(cls._logger.handlers):
                handler.close()
                cls._logger.removeHandler(handler)
            cls._logger = None

