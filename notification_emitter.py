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
    closed = {}
    opened = {}

    for uid, (name, prev_state, new_state) in classes.items():
        prev_severity = statuses.index(prev_state)
        new_severity = statuses.index(new_state)

        category = closed if new_severity > prev_severity else opened
        category[uid] = (name, prev_state, new_state)

    return closed, opened


class NotificationEmitter:

    def __init__(self):
        pass

    def dispatch_emit(self, closed_classes: dict, opened_classes: dict):
        pass

    def emit(self, classes: dict):
        if len(classes) == 0:
            return

        closed_classes, opened_classes = categorize_classes(classes)
        self.dispatch_emit(closed_classes, opened_classes)


class ConsoleEmitter(NotificationEmitter):

    def __init__(self):
        super().__init__()

    def dispatch_emit(self, closed_classes: dict, opened_classes: dict):

        if len(closed_classes) > 0:
            print('Here are the classes that closed up')
            for uid, (name, prev, new) in closed_classes.items():
                print('{} changed from {} to {}!'.format(name, prev, new))

            print('Here are the classes that opened up')
            for uid, (name, prev, new) in opened_classes.items():
                print('{} changed from {} to {}!'.format(name, prev, new))


class SlackEmitter(NotificationEmitter):

    def __init__(self, semester_code: str, token: str, channel: str):
        super().__init__()
        self.semester_code = semester_code
        self.client = slack.WebClient(token=token)
        self.channel = channel

    def build_closed_msg(self, closed_classes: dict) -> str:
        msg = 'These classes closed up\n'

        for uid, (name, old_status, new_status) in closed_classes.items():
            msg += '• {}: {} ({} -> {})\n'.format(uid, name, old_status, new_status)
        msg += '\n'

        return msg

    def build_opened_msg(self, opened_classes: dict) -> str:
        msg = 'These classes opened up\n'

        for uid, (name, old_status, new_status) in opened_classes.items():
            msg += '• {}: {} ({} -> {}) ' \
                   '<https://utdirect.utexas.edu/registration/registration.WBX?' \
                   's_ccyys={}&s_af_unique={}' \
                   '|Register>\n' \
                .format(uid, name, old_status, new_status, self.semester_code, uid)

        msg += 'Register for classes <https://utdirect.utexas.edu/registration/registration.WBX?s_ccyys={}' \
               '|here>.'.format(self.semester_code)
        return msg

    def build_blocks(self, closed_classes: dict, opened_classes: dict) -> list:
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
        if len(closed_classes) > 0 or len(opened_classes) > 0:
            return self.client.chat_postMessage(
                channel=self.channel,
                text='Some courses have changed status!',
                blocks=self.build_blocks(closed_classes, opened_classes))
