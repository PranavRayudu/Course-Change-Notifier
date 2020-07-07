# Course Change Notifier
Course Change Notifier is a simple script that allows users to run a course availability checker for UT Austin in the background and notify them via Slack if a desired course opens up in the schedule.
This requires Python 3.6+ and Google Chrome, Selenium Chrome drivers

## Get Started
```
git clone https://github.com/PranavRayudu/Course-Change-Notifier.git
pip install -r requirements.txt
```

Download the webdriver of your favorite browser (only Chrome is supported right now, change ``webdriver.Chrome()`` to desired browser) and add it to the PATH variable or place it in this project folder. 
Chrome drivers are available [here](https://chromedriver.chromium.org/downloads).

Having the UT Registration Plus extension does not affect this script.
This also requires user to log into their UT ID and Duo everytime it starts up. Script will continue executing once you reach the course schedule page.

Course change updated are sent to you via Slack. You can create a workspace [here](https://slack.com/get-started#/create) and your own Slack app [here](https://api.slack.com/apps?new_app=1).
[This](https://howchoo.com/g/yjuxytcyzta/python-send-slack-messages-slackclient) tutorial helps you with setting permissions and getting your access token.
Moreover, be sure to add your bot to the workspace and channel you want it to post messages to.

To configure your project for Slack, create a ``.env`` file and add the following data
```.env
SLACK_TOKEN=<Bot User OAuth Access Token>
SLACK_CHANNEL=<Channel Id> # see https://stackoverflow.com/questions/40940327/what-is-the-simplest-way-to-find-a-slack-team-id-and-a-channel-id
```
otherwise, use the ConsoleEmitter (prints to console) by commenting out Slack's import statement and initializer.

To run the project, simply run ``python course-monitor.py -link=<link of page> --uid <uid of course 1> <uid of course 2>...``
The ``-link`` argument is required and takes in the url of the first page of results of the courses the script should monitor
The ``--uid`` argument is optional (None by default) and takes in a space separated list of course unique ids to keep track of. If you do not use this, all courses on the page will be monitored.
The ``--debug`` argument is optional (False by default) and enables printing data to the console. It is recommended you keep this on.

Example usage
```commandline
python course_monitor.py -link https://utdirect.utexas.edu/apps/registrar/course_schedule/20209/results/?flags=CULTDIVR&search_type_main=CORE&ccyys=20209&fos_fl=&level=&instr_last_name=&instr_first_initial=&fos_cn=&course_number=&start_unique=&end_unique=&mtg_days_st=000000&mtg_start_time_st=00&core_code=060 --uid 37965 --debug
```

## Todo
- [ ] Add debug statements for Slack client
- [ ] Add direct links to add courses from every message
- [ ] Complete tests for course change detection 

## Contribution
This script is an open-source project that relies on its users to get better. If you would like to add features, please fork and create a PR.
If you would like to add your own notification method, simply extent the NotificationEmitter class and override the constructor and emit() function.