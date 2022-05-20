from datetime import datetime


def get_iso_time(epoch_time: int) -> str:
    return datetime.fromtimestamp(epoch_time).isoformat()

