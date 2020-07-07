# UT Course Monitor
UT Course Monitor is a simple script that allows users to run a course availability checker in the background and notify them if a desired course opens up in the schedule.
This requires Python 3.6+ and Google Chrome, Selenium Chrome drivers

## Get Started
```
git clone <url>
pip install -r requirements.txt
```

Download the webdriver of your favorite browser (only Chrome is supported right now, change ``webdriver.Chrome()`` to desired browser) and add it to the PATH variable or place it in the project folder. 
Chrome drivers are available [here](https://chromedriver.chromium.org/downloads).

You will need a Twillio account to send SMS messages to your phone when a course opens up.
> section in progress

having the UT Registration Plus extension does not affect this script.
This also requires user to be log into their UT_ID and DUO when it starts up. Script will continue executing once you reach the course schedule.
To configure your project for Twillio, create a ``.env`` file and add the following data
```.env

```
otherwise, use the ConsoleEmitter (prints to console) by commenting out Twillio's import statement and initializer.

To run the project, simply run ``python course-monitor.py -link=<link of page> --uid <uid of course 1> <uid of course 2>``
The ``-link`` argument is required and takes in the url of the first page of results of the courses the script should monitor
The ``--uid`` argument is optional (None by default) and takes in a space separated list of course unique ids to keep track of. If you do not use this, all courses on the page will be monitored.
The ``--debug`` argument is optional (False by default) and enables printing data to the console. It is recommended you keep this on.

Example usage
```commandline
python course_monitor.py -link https://utdirect.utexas.edu/apps/registrar/course_schedule/20209/results/?flags=CULTDIVR&search_type_main=CORE&ccyys=20209&fos_fl=&level=&instr_last_name=&instr_first_initial=&fos_cn=&course_number=&start_unique=&end_unique=&mtg_days_st=000000&mtg_start_time_st=00&core_code=060 --uid 37965 --debug
```

## Todo
- [ ] Add messaging to user (Twillio API)

## Contribution
This script is an open-source project that relies on its users to get better. If you would like to add features, please fork and create a PR.
If you would like to add your own notification method, simply extent the NotificationEmitter class and override the constructor and emit() function.