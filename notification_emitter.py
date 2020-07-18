import slack

statuses = [
    'open',
    'open; reserved',
    'reserved',
    'waitlisted',
    'waitlisted; reserved',
    'cancelled',
    'closed']


def categorize_classes(classes: dict) -> (dict, dict):
    """sort classes into closed and opened category and return 2 dicts with value (classname, old status, new status)"""
    closed = {}
    opened = {}

    for uid, (code, prof, prev_state, new_state) in classes.items():
        prev_severity = statuses.index(prev_state)
        new_severity = statuses.index(new_state)

        category = closed if new_severity > prev_severity else opened
        category[uid] = (code, prof, prev_state, new_state)

    return closed, opened


class NotificationEmitter:

    def dispatch_emit(self, closed_classes: dict, opened_classes: dict):
        pass

    def emit(self, classes: dict):
        if len(classes) == 0:
            return

        closed_classes, opened_classes = categorize_classes(classes)
        self.dispatch_emit(closed_classes, opened_classes)


class ConsoleEmitter(NotificationEmitter):

    def dispatch_emit(self, closed_classes: dict, opened_classes: dict):

        if len(closed_classes) > 0:
            print('Here are the classes that closed up')
            for uid, (code, prof, prev, new) in closed_classes.items():
                print('{} by {} changed from {} to {}!'.format(code, prof, prev, new))
        if len(opened_classes) > 0:
            print('Here are the classes that opened up')
            for uid, (code, prof, prev, new) in opened_classes.items():
                print('{} by {} changed from {} to {}!'.format(code, prof, prev, new))


class SlackEmitter(NotificationEmitter):

    def __init__(self, semester_code: str, token: str, channel: str):
        """stores the semester code/id and creates SlackBot using OAuth access token and channel ID to post to"""
        self.semester_code = semester_code
        self.channel = channel
        self.client = slack.WebClient(token=token)
        res = self.client.auth_test()
        if not res['ok']:
            print("Unable to verify Slack authentication")
            exit()
        res = self.client.api_test()
        if not res['ok']:
            print("Unable to verify Slack API access")
            exit()

    def build_closed_msg(self, closed_classes: dict) -> str:
        """builds message text for classes that have closed up"""

        if len(closed_classes) == 0:
            return ''

        msg = 'These classes closed up:\n' if len(closed_classes) > 1 else 'This class closed up:\n'

        for uid, (code, prof, old_status, new_status) in closed_classes.items():
            msg += '• {}: {} by {} ({} → {})\n'.format(uid, code, prof, old_status, new_status)
        msg += '\n'

        return msg

    def build_opened_msg(self, opened_classes: dict) -> str:
        """builds message text for classes that opened up, along with registration links for each class"""

        if len(opened_classes) == 0:
            return ''

        msg = 'These classes opened up:\n' if len(opened_classes) > 1 else 'This class opened up:\n'

        for uid, (code, prof, old_status, new_status) in opened_classes.items():
            msg += '• <https://utdirect.utexas.edu/registration/registration.WBX?' \
                   's_ccyys={}&s_af_unique={}' \
                   '|{}>: {} by {} ({} → {}) \n' \
                .format(self.semester_code, uid, uid, code, prof, old_status, new_status)

        msg += 'Register for classes <https://utdirect.utexas.edu/registration/registration.WBX?s_ccyys={}' \
               '|here>.'.format(self.semester_code)
        return msg

    def build_blocks(self, closed_classes: dict, opened_classes: dict) -> list:
        """builds list of block sections with class info in markdown to send in Slack message"""
        blocks = []

        if len(closed_classes) > 0:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": self.build_closed_msg(closed_classes)
                }})

        if len(opened_classes) > 0:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": self.build_opened_msg(opened_classes)
                }})

        return blocks

    def dispatch_emit(self, closed_classes: dict, opened_classes: dict):
        """sends message with closed and opened classes info via Slack client to channel specified in channel id"""
        if len(closed_classes) > 0 or len(opened_classes) > 0:
            return self.client.chat_postMessage(
                channel=self.channel,
                text='Some courses have changed status!',
                blocks=self.build_blocks(closed_classes, opened_classes))


def dispatch_all_emitters(emitters: [], classes: dict):
    """send class change message on every emitter in emitters"""
    for emitter in emitters:
        emitter.emit(classes)
