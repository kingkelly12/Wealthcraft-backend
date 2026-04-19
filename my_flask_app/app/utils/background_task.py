import threading
from functools import wraps
from flask import current_app

def run_in_background(func, *args, **kwargs):
    """
    Runs a function in a background thread.
    Passes along the Flask application context if available,
    allowing the background thread to safely execute database
    operations and access app config.
    """
    app = None
    try:
        app = current_app._get_current_object()
    except Exception:
        pass

    def wrapper():
        if app:
            with app.app_context():
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    app.logger.error(f"Background task {func.__name__} failed: {e}", exc_info=True)
        else:
            try:
                func(*args, **kwargs)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Background task {func.__name__} failed: {e}", exc_info=True)

    thread = threading.Thread(target=wrapper)
    thread.daemon = True
    thread.start()
    return thread
