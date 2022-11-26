from datetime import datetime
from typing import NamedTuple, Final


DEFAULT_NEW_USER_ATTENDED_CONTESTS_COUNT: Final[int] = 0
DEFAULT_NEW_USER_RATING: Final[float] = 1500.0


class CronTimePointWkdHrMin(NamedTuple):
    weekday: int
    hour: int
    minute: int


# Observed that leetcode would update more user's result within 10 minutes after ending,
# so safely set minute to 15 instead 0 in order to wait for final result.
WEEKLY_CONTEST_START = CronTimePointWkdHrMin(
    6,   # Sunday
    2,  # hour
    30,  # minute
)
BIWEEKLY_CONTEST_START = CronTimePointWkdHrMin(
    5,  # Saturday
    14,  # hour
    30,  # minute
)


class SingleContestDatetime(NamedTuple):
    num: int
    dt: datetime


# Take "weekly-contest-294" and "biweekly-contest-78" as two baselines
WEEKLY_CONTEST_BASE = SingleContestDatetime(
    294,
    datetime(2022, 5, 22, 2, 30),
)
BIWEEKLY_CONTEST_BASE = SingleContestDatetime(
    78,
    datetime(2022, 5, 14, 14, 30),
)

