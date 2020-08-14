# Course Change Notifier
Course Change Notifier is a simple script that allows users to run a course availability checker for UT Austin. It runs in the background and notifies user via Slack if a desired course opens up in the schedule.
This requires Python 3.6+, Google Chrome, and Selenium Chrome drivers.

## Get Started
```
git clone https://github.com/PranavRayudu/Course-Change-Notifier.git
pip install -r requirements.txt
```

Download the webdriver of your favorite browser (only Chrome is supported right now, change ``webdriver.Chrome()`` to desired browser) and add it to the PATH variable or place it in this project folder. 
Chrome drivers are available [here](https://chromedriver.chromium.org/downloads).

Having the UT Registration Plus extension does not affect this script.
This also requires user to accept Duo push everytime it starts up. Script will continue executing once you reach the course schedule page.

#### 1. Setting up UT automatic login and Duo push notifications
Create and add these to your ```.env``` file:
```commandline
EID=<UT EID>
UT_PASS=<UT systems password>
```
In Duo, set push notifications as your preferred method of signing in, so Duo will automatically send a push notification whenever you need to sign in. If you do not do this, you will have to manually click "Send push" whenever it reaches the two-factor authentication screen. Moreover, if you do not approve the push notification before a timeout, you will also have to manually click "Send push" again.

#### 2. Setting up Slack notifications
Course change updated are sent to you via Slack. You can create a workspace [here](https://slack.com/get-started#/create) and your own Slack app [here](https://api.slack.com/apps?new_app=1).
[This](https://howchoo.com/g/yjuxytcyzta/python-send-slack-messages-slackclient) tutorial helps you with setting permissions and getting your access token. More specifically, you need the chat:write bot token scope.
You must also have your bot added to the workspace and channel you want it to post messages to.

To configure your project for Slack, and add the following data to your ```.env``` file
```.env
SLACK_TOKEN=<Bot User OAuth Access Token>
SLACK_CHANNEL=<channel name>  # channel's name, simply whatever follows the '#' of desired channel
```
otherwise, use the ConsoleEmitter (prints to console) by commenting out Slack's import statement and initializer.

#### 3. Running the script
To run the project, simply run ``python course-monitor.py --sem "Fall 2020" --uids <uid of course 1> <uid of course 2>...``
- The ``--sem`` or ``-s`` arguments is required and specifies the semester to look for courses in. Must be in ``<Season> YYYY`` format.
- The ``--uids`` or ``-u`` argument is required and takes in a space separated list of course unique ids to keep track of.
- The ``--period`` or ``-p`` argument is optional (180 by default) and specifies the time in seconds between consecutive course checks.
- The ``--headless`` argument is optional (False by default) and runs the browser without any GUI. Enable this only when you have added your UT credentials to ``.env`` and configured Duo to automatically send a push.

Example usage
```commandline
python course_monitor.py --sem "Fall 2020" --uids 37960 37965 37970 37975 --headless
```

## Todo
- [x] Add direct links to add courses from every message
- [x] Complete tests for course change detection
- [x] Add automatic login to UT ID
- [x] Add support for multiple notification emitters
- [x] Remove dependency on links
- [ ] Allow dynamic scheduling and make server-ready
- [ ] (Dangerous) add automatic registration

## Contribution
If you would like to add features/fix bugs, please fork and create a PR.
If you would like to add your own notification method, simply extent the NotificationEmitter class and override the constructor and __dispatch_emit() function.
