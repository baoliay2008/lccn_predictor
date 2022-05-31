import sys
from datetime import datetime
from loguru import logger


def get_iso_time(epoch_time: int) -> str:
    return datetime.fromtimestamp(epoch_time).isoformat()


def start_loguru():
    from app.config import get_yaml_config
    try:
        loguru_config = get_yaml_config().get("loguru")
        logger.add(
            sink=loguru_config["sink"],
            rotation=loguru_config["rotation"],
            level=loguru_config["level"],
        )
    except Exception as e:
        logger.error(f"Failed to start loguru, check loguru config in config.yaml file. {e}")
        sys.exit(1)

