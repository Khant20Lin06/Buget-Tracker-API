# accounts/helpers.py
from django.utils.timezone import localtime
from django.utils.dateformat import format as dj_format

def mmt(dt):
    """
    Return Myanmar-time datetime as: 2025-06-26 10:45:30 PM
    """
    if dt is None:
        return None
    # Y = 4-digit year │ m = 2-digit month │ d = 2-digit day
    # h = 12-hour (01-12) │ i = minutes │ s = seconds │ A = AM/PM
    return dj_format(localtime(dt), "Y-m-d h:i:s A")

