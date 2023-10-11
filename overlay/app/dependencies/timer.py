import datetime


class TimerState(object):
    def __init__(self):
        self.started_at: datetime.datetime = datetime.datetime.now()
        self.running: bool = False
        self.time: int = 0
        self.ending_sound: bool = True

    def __dict__(self):
        return {
                "running": self.running,
                "startedAt": self.started_at.timestamp(),
                "time": self.time,
                "endingSound": self.ending_sound,
                }


def update_timer(timer_object):
    if timer_object.running:
        now = datetime.datetime.now()
        timer_val = (now - timer_object.started_at).total_seconds()
        timer_object.time = max(timer_object.time - timer_val, 0)
        timer_object.started_at = now
    return timer_object
