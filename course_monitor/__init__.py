import time

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from course_monitor import course
from course_monitor import monitor
from course_monitor import emitter

Course = course.Course
CourseEncoder = course.CourseEncoder
Monitor = monitor.Monitor
ConsoleEmitter = emitter.ConsoleEmitter
SlackEmitter = emitter.SlackEmitter
Course.Monitor = Monitor


def set_debug(debug=True):
    course.debug = debug
    monitor.debug = debug


class JobState:
    def __init__(self, job_id: str):
        self.done = False
        self.job_id = job_id

    def listen_done(self, scheduler):
        scheduler.add_listener(self.job_done, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    def job_done(self, event):
        if event.job_id == self.job_id:
            self.done = True

    def wait_done(self, timeout=60):
        start = time.time()
        elapsed = 0  # in seconds
        while not self.done and elapsed < timeout:
            elapsed = time.time() - start  # in seconds
