def run_once(f):
    """
    Decorator definition to ensure one-time use of a function call, even from within a loop.
    """

    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)

    wrapper.has_run = False
    return wrapper
