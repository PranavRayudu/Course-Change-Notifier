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
    Emitters = []
    App = None

    uid = db.Column(db.String(5), primary_key=True)
    title = db.Column(db.String(255))
    abbr = db.Column(db.String(10))
    prof = db.Column(db.String(255))
    status = db.Column(db.String(100))
    register = db.Column(db.String(100))
    paused = db.Column(db.Boolean)
    valid = db.Column(db.Boolean)

    def __init__(self, uid: str):
        self.uid = uid
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

    @staticmethod
    def __update_course(course, browser_src: str) -> str:

        def __parse_header(header: str) -> (str, str):
            """splits header text into its course code and name components"""
            header_matches = re.compile(r"([A-Z ]+)(\d{3}\w?) ([-\w' ]+)").match(header.strip())
            course_code = header_matches.group(1).strip() + ' ' + header_matches.group(2).strip()
            course_name = header_matches.group(3).strip()
            return course_code, course_name

        if not browser_src:
            return course.status

        soup = BeautifulSoup(browser_src, 'html.parser')
        table = soup.find('table', {'id': 'details_table'})

        if table:
            row = table.find('tbody').find('tr')
            header = soup.find("section", {"id": "details"}).find("h2")
            course.abbr, course.title = __parse_header(header.text)
            # unique = row.find('td', {'data-th': 'Unique'}).text
            course.prof = row.find('td', {'data-th': 'Instructor'}).text
            course.status = row.find('td', {'data-th': 'Status'}).text
        else:
            course.valid = False

        return course.status

    @staticmethod
    def __changes(course, prev_status) -> dict:
        """Get a dict of changed courses with old and new statuses"""
        changed_course = {}

        if prev_status != course.status:
            changed_course[course.uid] = (course.abbr, course.prof, prev_status, course.status)

        if len(changed_course) > 0:
            d_print('{} changed status'.format(changed_course))
        else:
            d_print('no change in course {}'.format(course.uid))
        return changed_course

    @staticmethod
    def __dispatch_emitters(changes: dict):
        """send class change message on every emitter in emitters"""
        if len(changes) == 0:
            return

        for emitter in Course.Emitters:
            emitter.emit(changes)

    @staticmethod
    def __dispatch_emitters_simple(msg: str):
        for emitter in Course.Emitters:
            emitter.simple_msg(msg)

    @staticmethod
    def get_course(uid_: str):
        with Course.App.app_context():
            return db.session.query(Course).filter_by(uid=uid_).first()

    @staticmethod
    def check(uid: str):
        course = Course.get_course(uid)

        if not course.valid:
            return

        prev_status = course.status
        course.status = course.__update_course(course, Course.Monitor.get_course_page(course.uid))
        if prev_status:
            Course.__dispatch_emitters(Course.__changes(course, prev_status))

            s_rank = statuses.index(course.status)
            p_rank = statuses.index(prev_status)
            if course.register and course.register != 'success' and course.valid and s_rank < 5 and s_rank < p_rank:
                course.register = Course.Monitor.register(course.uid)
                if course.register == 'fail':
                    Course.__dispatch_emitters_simple(
                        'Failed attempted registration for {}: {}'.format(course.uid, course.abbr))
                elif course.register == 'success':
                    Course.__dispatch_emitters_simple(
                        'Successfully registered for {}: {}!'.format(course.uid, course.abbr))

        with Course.App.app_context():
            db.session.add(course)
            db.session.commit()

    @staticmethod
    def get_course_job_ids(uid):
        # job ids: <uid>-c (course check), <uid>-s (start course check), <uid>-e (end course check)
        return '{}-c'.format(uid), '{}-s'.format(uid), '{}-e'.format(uid)

    @staticmethod
    def pause_job(uid: str, scheduler):
        course = Course.get_course(uid)
        if course:
            job_id, _, _ = Course.get_course_job_ids(uid)
            if job := scheduler.get_job(job_id, 'default'):
                job.pause()
            course.paused = True
            db.session.commit()

    @staticmethod
    def resume_job(uid: str, scheduler):
        course = Course.get_course(uid)
        if course:
            job_id, _, _ = Course.get_course_job_ids(uid)
            if job := scheduler.get_job(job_id, 'default'):
                job.resume()
            course.paused = False
            db.session.commit()

    @staticmethod
    def remove_jobs(uid: str, scheduler):
        job_id, job_sid, job_eid = Course.get_course_job_ids(uid)
        if job_c := scheduler.get_job(job_id, 'default'):
            job_c.remove()
        if job_s := scheduler.get_job(job_sid, 'default'):
            job_s.remove()
        if job_e := scheduler.get_job(job_eid, 'default'):
            job_e.remove()

    @staticmethod
    def serialize(course) -> {}:
        return {
            "uid": course.uid,
            "abbr": course.abbr,
            "title": course.title,
            "prof": course.prof,
            "status": course.status if course.valid else 'invalid',
            "register": course.register,
            "paused": course.paused
        }
