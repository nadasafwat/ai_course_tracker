import schedule
import time
import threading


def run_continuously(interval_seconds=1):
    """Run schedule in a background thread."""
    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):
        @staticmethod
        def run():
            while not cease_continuous_run.is_set():
                schedule.run_pending()
                time.sleep(interval_seconds)

    continuous_thread = ScheduleThread()
    continuous_thread.daemon = True
    continuous_thread.start()
    return cease_continuous_run
