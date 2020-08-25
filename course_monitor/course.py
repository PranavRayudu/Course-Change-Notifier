import json
import re
from json.encoder import JSONEncoder

from bs4 import BeautifulSoup

from course_monitor.course_monitor import CourseMonitor

debug = False


def d_print(msg):
    """Prints status messages only if debug flag is used"""
    if debug:
        print(msg)


class CourseEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Course):
            return {
                "uid": obj.uid,
                "abbr": obj.code,
                "title": obj.title,
                "prof": obj.prof,
                "status": obj.status
            }
        return json.JSONEncoder.default(self, obj)


class Course:

    def __init__(self, uid: str, emitters: []):
        self.uid = uid
        self.emitters = emitters
        self.code, self.title = None, None
        self.prof = None
        self.prev_status, self.status = None, None
        self.job = None
        self.start_job = None
        self.end_job = None

    @staticmethod
    def valid_uid(uid: str):
        uid = str(uid)
        return uid.isdigit() and len(uid) == 5

    def __eq__(self, obj):
        return isinstance(obj, Course) and obj.uid == self.uid

    def __hash__(self):
        return int(self.uid)

    def __str__(self):
        if self.code and self.title:
            return "{}: {} ({})".format(self.code, self.title, self.uid)
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
            self.code, self.title = __parse_header(header.text)
            # unique = row.find('td', {'data-th': 'Unique'}).text
            self.prof = row.find('td', {'data-th': 'Instructor'}).text
            self.status = row.find('td', {'data-th': 'Status'}).text
            return self.status
        else:
            raise Exception("Current page does not contain any course information")

    def __changes(self) -> dict:
        """Get a dict of changed courses with old and new statuses"""
        changed_course = {}

        if self.prev_status != self.status:
            changed_course[self.uid] = (self.code, self.prof, self.prev_status, self.status)

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

    def check(self):
        self.prev_status = self.status
        self.status = self.__update_course(CourseMonitor.get_course_page(self.uid))
        if self.prev_status:
            self.__dispatch_emitters(self.__changes())