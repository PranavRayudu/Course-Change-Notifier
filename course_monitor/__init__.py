from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR


class JobState:
    def __init__(self, job_id: str):
        self.finished = False
        self.job_id = job_id

    def listen_done(self, scheduler):
        scheduler.add_listener(self.job_finished, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    def job_finished(self, event):
        if event.job_id == self.job_id:
            self.finished = True

    def wait_done(self):
        while not self.finished:
            pass