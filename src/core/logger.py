"""
PhotoGeoView Logger Configuration
Centralized logging setup for the entire application
"""

import json
import logging
import logging.config
import os
from pathlib import Path
from typing import Optional


class LoggerManager:
    """
    Centralized logger management class for PhotoGeoView
    Handles initialization and configuration of all loggers
    """

    _initialized = False
    _config_path = Path(__file__).parent.parent / "config" / "logging.json"

    @classmethod
    def initialize(cls, config_path: Optional[Path] = None) -> None:
        """
        Initialize logging configuration

        Args:
            config_path: Optional path to logging config file
        """
        if cls._initialized:
            return

        if config_path:
            cls._config_path = config_path

        # Ensure logs directory exists
        logs_dir = Path(__file__).parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)

        try:
            with open(cls._config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Update file paths to be absolute
            base_path = Path(__file__).parent.parent
            for handler_config in config.get('handlers', {}).values():
                if 'filename' in handler_config:
                    filename = handler_config['filename']
                    if not os.path.isabs(filename):
                        handler_config['filename'] = str(base_path / filename)

            logging.config.dictConfig(config)
            cls._initialized = True

            # Test logging
            logger = logging.getLogger('PhotoGeoView')
            logger.info("Logger initialized successfully")

        except Exception as e:
            # Fallback to basic configuration
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(),
                    logging.FileHandler(logs_dir / 'fallback.log')
                ]
            )
            logger = logging.getLogger('PhotoGeoView')
            logger.error(f"Failed to load logging config: {e}")
            logger.info("Using fallback logging configuration")
            cls._initialized = True

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        Get a logger instance for the given name

        Args:
            name: Logger name (typically __name__)

        Returns:
            Configured logger instance
        """
        if not LoggerManager._initialized:
            LoggerManager.initialize()

        # Ensure logger name starts with PhotoGeoView
        if not name.startswith('PhotoGeoView'):
            if name == '__main__':
                name = 'PhotoGeoView.main'
            else:
                # Extract module path and prepend PhotoGeoView
                parts = name.split('.')
                if 'src' in parts:
                    idx = parts.index('src')
                    name = 'PhotoGeoView.' + '.'.join(parts[idx+1:])
                else:
                    name = f'PhotoGeoView.{name}'

        return logging.getLogger(name)

    @staticmethod
    def set_level(logger_name: str, level: str) -> None:
        """
        Dynamically change logger level

        Args:
            logger_name: Name of the logger
            level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        logger = logging.getLogger(logger_name)
        numeric_level = getattr(logging, level.upper(), None)
        if numeric_level is not None:
            logger.setLevel(numeric_level)
            LoggerManager.get_logger('PhotoGeoView.core.logger').info(
                f"Changed {logger_name} log level to {level}"
            )


# Convenience function for easy import
def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger

    Usage:
        from src.core.logger import get_logger
        logger = get_logger(__name__)
    """
    return LoggerManager.get_logger(name)


# Initialize logging when module is imported
LoggerManager.initialize()
