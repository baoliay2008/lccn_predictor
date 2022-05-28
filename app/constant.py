from collections import namedtuple
from datetime import datetime


CronTimePointWkdHrMin = namedtuple('ContestTimePoint', ['weekday', 'hour', 'minute'])
# Observed that leetcode would update more user's result within 10 minutes after ending,
# so safely set minute to 15 instead 0 in order to wait for final result.
WEEKLY_CONTEST_END = CronTimePointWkdHrMin(
    6,   # Sunday
    4,  # hour
    15,  # minute
)
BIWEEKLY_CONTEST_END = CronTimePointWkdHrMin(
    5,  # Saturday
    16,  # hour
    15,  # minute
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

