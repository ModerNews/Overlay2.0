import datetime


class TimerState(object):
    """
    Helper class for managing current timer state
    """
    def __init__(self):
        self.started_at: datetime.datetime = datetime.datetime.now()
        self.running: bool = False
        self.time: int = 0
        self.sound: bool = True

    def to_dict(self) -> dict:
        """
        Simple function for serialization to dict object

        :return: serialized Timer State object
        """
        return {"running": self.running,
                "time": self.time,
                "startedAt": self.started_at.strftime("%Y-%m-%dT%H:%M:%S%f")[:-3] + "Z",
                "sound": self.sound
        }


    def update_timer(self) -> None:
        """
        Modify timer state to fit stopped timer
        """
        if self.running:
            now = datetime.datetime.now()
            timer_val = (now - self.started_at).total_seconds()

            self.time = max(self.time - timer_val, 0)

            self.started_at = now
