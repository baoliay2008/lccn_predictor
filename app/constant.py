from collections import namedtuple
from datetime import datetime


CronTimePointWkdHrMin = namedtuple('ContestTimePoint', ['weekday', 'hour', 'minute'])
WEEKLY_CONTEST_END = CronTimePointWkdHrMin(
    6,   # Sunday
    4,  # hour
    0,  # minute
)
BIWEEKLY_CONTEST_END = CronTimePointWkdHrMin(
    5,  # Saturday
    16,  # hour
    0,  # minute
)


SingleContestDatetime = namedtuple('SingleContestDatetime', ['num', 'datetime'])
WEEKLY_CONTEST_BASE = SingleContestDatetime(
    294,
    datetime(2022, 5, 22, 4, 0),
)
BIWEEKLY_CONTEST_BASE = SingleContestDatetime(
    78,
    datetime(2022, 5, 14, 16, 0),
)

