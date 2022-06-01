import sys
from datetime import datetime
from loguru import logger


def get_iso_time(epoch_time: int) -> str:
    return datetime.fromtimestamp(epoch_time).isoformat()


def start_loguru(process: str = "main"):
    """
    error-prone warning: misuse process parameter (for example, use main in fastapi process
    or reassign a different value) will mess up logs.
    TODO: could set a global singleton variable to make sure this function will only be called once in a single process.
    :param process: "main" for main.py backend process, "api" for fastapi http-server process.
    :return:
    """
    from app.config import get_yaml_config
    try:
        loguru_config = get_yaml_config().get("loguru").get(process)
        logger.add(
            sink=loguru_config["sink"],
            rotation=loguru_config["rotation"],
            level=loguru_config["level"],
        )
    except Exception as e:
        logger.error(f"Failed to start loguru, check loguru config in config.yaml file. error={e}")
        sys.exit(1)

