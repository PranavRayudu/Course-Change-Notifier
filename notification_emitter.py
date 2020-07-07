import slack

statuses = [
    'open',
    'open; reserved',
    'reserved',
    'waitlisted',
    'waitlisted; reserved',
    'cancelled',
    'closed']


def categorize_classes(classes):
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

    def emit(self, closed_classes: dict, opened_classes: dict):
        pass

    def emit_msg(self, classes: dict):
        if len(classes) == 0:
            return
        else:
            closed_classes, opened_classes = categorize_classes(classes)
            self.emit(closed_classes, opened_classes)


class ConsoleEmitter(NotificationEmitter):

    def __init__(self):
        super().__init__()

    def emit(self, closed_classes: dict, opened_classes: dict):

        if len(closed_classes) > 0:
            print('Here are the classes that closed up')
            for uid, (name, prev, new) in closed_classes.items():
                print('{} changed from {} to {}!'.format(name, prev, new))

            print('Here are the classes that opened up')
            for uid, (name, prev, new) in opened_classes.items():
                print('{} changed from {} to {}!'.format(name, prev, new))


def build_msg(closed_classes: dict, opened_classes: dict):
    msg = ''

    if len(closed_classes) > 0:
        msg += 'These classes closed up\n'

        for uid, (name, old_status, new_status) in closed_classes.items():
            msg += '- {}: {} ({} -> {})\n'.format(uid, name, old_status, new_status)
        msg += '\n'

    if len(opened_classes) > 0:
        msg += 'These classes opened up\n'

        for uid, (name, old_status, new_status) in opened_classes.items():
            msg += '- {}: {} ({} -> {})\n'.format(uid, name, old_status, new_status)

        msg += 'register for class here {}'.format('https://utdirect.utexas.edu/registration/chooseSemester.WBX')

    # add link to registration if possible, formatted as
    # https://utdirect.utexas.edu/registration/registration.WBX?s_ccyys=
    # <20209 | semester code>&s_af_unique=<00495 | course unique id>
    return msg


class SlackEmitter(NotificationEmitter):

    def __init__(self, token: str, channel: str):
        super().__init__()
        self.client = slack.WebClient(token=token)
        self.channel = channel

    def emit(self, closed_classes: dict, opened_classes: dict):
        if len(closed_classes) > 0 or len(opened_classes) > 0:
            self.client.chat_postMessage(
                channel=self.channel,
                text=build_msg(closed_classes, opened_classes))
