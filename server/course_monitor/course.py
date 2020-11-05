import re
from bs4 import BeautifulSoup

from server.course_monitor.database import db

debug = False
statuses = [
    'open',
    'open; reserved',
    'reserved',
    'waitlisted',
    'waitlisted; reserved',
    'closed',
    'cancelled'
]


def d_print(msg):
    """Prints status messages only if debug flag is used"""
    if debug:
        print(msg)

class Course(db.Model):
    Monitor = None

    uid = db.Column(db.String(5), primary_key=True)
    title = db.Column(db.String(255))
    abbr = db.Column(db.String(10))
    prof = db.Column(db.String(255))

    def __init__(self, uid: str, emitters: []):
        self.uid = uid
        self.emitters = emitters
        self.abbr, self.title = None, None
        self.prof = None
        self.prev_status, self.status = None, None
        self.register = None
        self.paused = False
        self.valid = True

    def __eq__(self, obj):
        return isinstance(obj, Course) and obj.uid == self.uid

    def __hash__(self):
        return int(self.uid)

    def __repr__(self):
        return '<{}: {}>'.format(self.uid, self.abbr)

    def __str__(self):
        if self.abbr and self.title:
            return "{}: {} ({})".format(self.abbr, self.title, self.uid)
        return self.uid

    def __update_course(self, browser_src: str) -> str:

        def __parse_header(header: str) -> (str, str):
            """splits header text into its course code and name components"""
            header_matches = re.compile(r"([A-Z ]+)(\d{3}\w?) ([-\w' ]+)").match(header.strip())
            course_code = header_matches.group(1).strip() + ' ' + header_matches.group(2).strip()
            course_name = header_matches.group(3).strip()
            return course_code, course_name

        if not browser_src:
            return self.status

        soup = BeautifulSoup(browser_src, 'html.parser')
        table = soup.find('table', {'id': 'details_table'})

        if table:
            row = table.find('tbody').find('tr')
            header = soup.find("section", {"id": "details"}).find("h2")
            self.abbr, self.title = __parse_header(header.text)
            # unique = row.find('td', {'data-th': 'Unique'}).text
            self.prof = row.find('td', {'data-th': 'Instructor'}).text
            self.status = row.find('td', {'data-th': 'Status'}).text
        else:
            self.valid = False

        return self.status

    def __changes(self) -> dict:
        """Get a dict of changed courses with old and new statuses"""
        changed_course = {}

        if self.prev_status != self.status:
            changed_course[self.uid] = (self.abbr, self.prof, self.prev_status, self.status)

        if len(changed_course) > 0:
            d_print('{} that changed status'.format(changed_course))
        else:
            d_print('no change in course {}'.format(self.uid))
        return changed_course

    def __dispatch_emitters(self, changes: dict):
        """send class change message on every emitter in emitters"""
        if len(changes) == 0:
            return

        for emitter in self.emitters:
            emitter.emit(changes)

    def __dispatch_emitters_simple(self, msg: str):
        for emitter in self.emitters:
            emitter.simple_msg(msg)

    def check(self):
        if not self.valid:
            return

        self.prev_status = self.status
        self.status = self.__update_course(Course.Monitor.get_course_page(self.uid))
        if self.prev_status:
            self.__dispatch_emitters(self.__changes())

            s_rank = statuses.index(self.status)
            p_rank = statuses.index(self.prev_status)
            if self.register and self.register != 'success' and self.valid and s_rank < 5 and s_rank < p_rank:
                self.register = Course.Monitor.register(self.uid)
                if self.register == 'fail':
                    self.__dispatch_emitters_simple(
                        'Failed attempted registration for {}: {}'.format(self.uid, self.abbr))
                elif self.register == 'success':
                    self.__dispatch_emitters_simple(
                        'Successfully registered for {}: {}!'.format(self.uid, self.abbr))

    def get_course_job_ids(self):
        # job ids: <uid>-c (course check), <uid>-s (start course check), <uid>-e (end course check)
        return '{}-c'.format(self.uid), '{}-s'.format(self.uid), '{}-e'.format(self.uid)

    def pause_job(self, scheduler):
        job_id, _, _ = self.get_course_job_ids()
        if job := scheduler.get_job(job_id, 'default'):
            job.pause()
        self.paused = True

    def resume_job(self, scheduler):
        job_id, _, _ = self.get_course_job_ids()
        if job := scheduler.get_job(job_id, 'default'):
            job.resume()
        self.paused = False

    def remove_jobs(self, scheduler):

        job_id, job_sid, job_eid = self.get_course_job_ids()
        if job := scheduler.get_job(job_id, 'default'):
            job.remove()
        if job := scheduler.get_job(job_sid, 'default'):
            job.remove()
        if job := scheduler.get_job(job_eid, 'default'):
            job.remove()

    def serialize(self) -> {}:
        return {
            "uid": self.uid,
            "abbr": self.abbr,
            "title": self.title,
            "prof": self.prof,
            "status": self.status if self.valid else 'invalid',
            "register": self.register,
            "paused": self.paused
        }
