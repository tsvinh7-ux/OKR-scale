from odoo import fields

LEVELS = [
    ('company', 'Company'),
    ('department', 'Department'),
    ('individual', 'Individual'),
]

STATUSES = [
    ('on_track', 'On Track'),
    ('at_risk', 'At Risk'),
    ('off_track', 'Off Track'),
    ('achieved', 'Achieved'),
]

CONFIDENCE = [(str(i), str(i)) for i in range(1, 11)]

_STATUS_RANK = {'on_track': 0, 'at_risk': 1, 'off_track': 2}


def time_progress(date_start, date_end, today=None):
    """Percentage (0-100) of the period elapsed at ``today``."""
    if not date_start or not date_end:
        return 0.0
    today = today or fields.Date.today()
    total = (date_end - date_start).days + 1
    if total <= 0 or today < date_start:
        return 0.0
    if today > date_end:
        return 100.0
    return min(100.0, ((today - date_start).days + 1) * 100.0 / total)


def compute_status(progress, expected, confidence):
    """Combine the schedule gap and the owner's confidence into a status.

    The worst of both signals wins, so an owner that is on schedule but
    reports a low confidence is still flagged.
    """
    if progress >= 100:
        return 'achieved'
    gap = (expected or 0.0) - (progress or 0.0)
    by_time = 'on_track' if gap <= 10 else 'at_risk' if gap <= 25 else 'off_track'
    by_confidence = 'on_track'
    if confidence:
        confidence = int(confidence)
        by_confidence = 'on_track' if confidence >= 7 else 'at_risk' if confidence >= 4 else 'off_track'
    return max(by_time, by_confidence, key=_STATUS_RANK.get)
