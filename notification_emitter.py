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

    def emit(self, closed_classes, opened_classes):
        pass

    def emit_msg(self, classes):
        if len(classes) == 0:
            return
        else:
            closed_classes, opened_classes = categorize_classes(classes)
            self.emit(closed_classes, opened_classes)


class ConsoleEmitter(NotificationEmitter):

    def __init__(self):
        super().__init__()

    def emit(self, closed_classes, opened_classes):

        if len(closed_classes) > 0:
            print('Here are the classes that closed up')
            for uid, (name, prev, new) in closed_classes.items():
                print('{} changed from {} to {}!'.format(name, prev, new))

            print('Here are the classes that opened up')
            for uid, (name, prev, new) in opened_classes.items():
                print('{} changed from {} to {}!'.format(name, prev, new))


class TwillioMsgEmitter(NotificationEmitter):

    def __init__(self):
        super().__init__()

    def emit(self, closed_classes, opened_classes):
        pass
