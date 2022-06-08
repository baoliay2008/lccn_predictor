from collections import namedtuple
from datetime import datetime

DEFAULT_NEW_USER_CONTEST_INFO = {  # will not have mutable values, just use `copy.copy()` is OK.
    "attendedContestsCount": 0,
    "rating": 1500.0,
}

CronTimePointWkdHrMin = namedtuple('ContestTimePoint', ['weekday', 'hour', 'minute'])
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


SingleContestDatetime = namedtuple('SingleContestDatetime', ['num', 'datetime'])
WEEKLY_CONTEST_BASE = SingleContestDatetime(
    294,
    datetime(2022, 5, 22, 2, 30),
)
BIWEEKLY_CONTEST_BASE = SingleContestDatetime(
    78,
    datetime(2022, 5, 14, 14, 30),
)

