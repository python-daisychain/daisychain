import functools
import datetime


class cache_for(object):
    """
    Decorator that caches the results of a function to be returned on subsequent calls for an amount of time
    based off of a timedelta and so it takes in the same kwargs as a 'datetime.timedelta' object
    """
    def __init__(self, **td_kwargs):
        self.expiration_time = datetime.datetime.now()
        self.interval = datetime.timedelta(**td_kwargs)
        self.cached_value = None

    def __call__(self, f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if self.expiration_time < datetime.datetime.now():
                self.cached_value = f(*args, **kwargs)
                self.expiration_time = datetime.datetime.now() + self.interval
            return self.cached_value
        return wrapper
