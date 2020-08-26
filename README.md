# Course Change Notifier
Course Change Notifier is a simple script that allows users to run a course availability checker for UT Austin. It runs in the background and notifies user via Slack if a desired course opens up in the schedule.
This requires Python 3.8+, Google Chrome, and Selenium Chrome drivers.

## Get Started
```.commandline
git clone https://github.com/PranavRayudu/Course-Change-Notifier.git
pip install -r requirements.txt
```

Download the webdriver of your favorite browser (only Chrome is supported right now, change ``webdriver.Chrome()`` to desired browser) and add it to the PATH variable or place it in this project folder. 
Chrome drivers are available [here](https://chromedriver.chromium.org/downloads).

Having the UT Registration Plus extension does not affect this script.
This also requires user to accept Duo push everytime it starts up. Script will continue executing once you reach the course schedule page.

#### 1. Setting up UT automatic login and Duo push notifications
Create and add these to your ```.env``` file:
```.env
EID=<UT EID>
UT_PASS=<UT systems password>
SEM=<Current Semester, ex: "Fall 2020" (with quotes)> # this is required unless you specify semester in arguments
```

#### 2. Setting up Slack notifications
Course change updated are sent to you via Slack. You can create a workspace [here](https://slack.com/get-started#/create) and your own Slack app [here](https://api.slack.com/apps?new_app=1).
[This](https://howchoo.com/g/yjuxytcyzta/python-send-slack-messages-slackclient) tutorial helps you with setting permissions and getting your access token. More specifically, you need the chat:write bot token scope.
You must also have your bot added to the workspace and channel you want it to post messages to.

To configure your project for Slack, and add the following data to your ```.env``` file
```.env
SLACK_TOKEN=<Bot User OAuth Access Token>
SLACK_CHANNEL=<channel name>  # channel's name, simply whatever follows the '#' of desired channel
```
otherwise, use the ConsoleEmitter (prints to console)

#### 3. Set up start and end times of day (optional)
You can configure course checks to happen only during a specific time period of the day. To do so, add the following to your ``.env`` file
By default, course checks will happen for the entire 24hrs of a day.
```..env
# all times are specified in military time with no separator between hours and minutes 
START=1112 # start checking at 11:12am
END=1803 # end checking at 6:03pm 
```

#### 4. Running the script (only for local.py - server.py is still experimental)
To run the project, simply run ``python local.py --sem "Fall 2020" --uids <uid of course 1> <uid of course 2>...``
- The ``--sem`` or ``-s`` arguments is required (unless specified in ``.env``) and specifies the semester to look for courses in. Must be in ``<Season> YYYY`` format.
- The ``--uids`` or ``-u`` argument is optional and takes in a space separated list of course unique ids to keep track of.
- The ``--period`` or ``-p`` argument is optional (180 by default) and specifies the time in seconds between consecutive course checks.
- The ``--headless`` argument is optional (False by default) and runs the browser without any GUI. Enable this only when you have added your UT credentials to ``.env`` and configured Duo to automatically send a push.
- The ``--verbose`` argument is optional (False by default) and shows debug print statements in the terminal. Enable this for debugging.

#### 5. Issuing commands while the script is running
The command line can be used to issue arguments to the scheduler:
- ``add <uid>`` adds a course to be tracker and course list
- ``remove <uid>`` will stop that course from being tracker and from the course list
- ``pause <uid>`` pauses a course from being tracked (but keeps it in the course list)
= ``resume <uid>`` resumes a paused course to continue tracking
- ``list`` will list all courses currently being tracked and 
- ``clear`` will remove all courses from being tracked
- ``exit`` stops and exists the script
> Note: it is not recommended to use the ``--verbose`` flag with commands

Example usage
```commandline
python local.py --sem "Fall 2020" --uids 37960 37965 37970 37975 --headless
```

#### 6. Use ``server.py`` to use web gui (experimental)
Add ``FLASK_ENV=development`` and ``SECRET_KEY=<random hash>`` to your ``.env`` file
Run ``server.py`` and React project in ``/client`` together 

## Todo
- [x] Add direct links to add courses from every message
- [x] Complete tests for course change detection
- [x] Add automatic login to UT ID
- [x] Add support for multiple notification emitters
- [x] Remove dependency on links
- [x] Allow dynamic scheduling and make server-ready
- [ ] (Dangerous) add automatic registration

## Contribution
If you would like to add features/fix bugs, please fork and create a PR.
If you would like to add your own notification method, simply extent the NotificationEmitter class and override the constructor and __dispatch_emit() function.
