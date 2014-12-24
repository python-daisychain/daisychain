from daisychain.decorators import cache_for
import time

@cache_for(seconds=0.5)
def check_time():
    return time.time()

def test_cache_for():
    first_answer = check_time()
    while check_time() == first_answer:
        time.sleep(0.001)
    assert 0.4 <= (check_time() - first_answer) <= 0.6, "cache_for decorator cached for greater than +/- 0.1 seconds over the limit"

def test_bad_cache_for():
    try:
        wrapper = cache_for(this_is_not_a_td_kwarg=False)
    except TypeError:
        pass
    else:
        assert False, "cache_for should have thrown a type error for the known bad kwarg 'this_is_not_a_td_kwarg'"
