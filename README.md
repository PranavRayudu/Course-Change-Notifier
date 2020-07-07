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

If you have the UT Schedule extension, auto-load may need to be turned off. 
This also requires user to be logged into their UT_ID and DUO (with remember for 30 days) beforehand.
To configure your project, create a ``.env`` file and add the following data
To run the project, simply run ``python course-monitor.py -link=<link of page> --uid 12345 101010``
The ``-link`` argument is required and takes in the url of the first page of results of the courses the script should monitor
The ``--uid`` argument is optional and takes in a space separated list of course unique ids to keep track of. If you do not use this, then all courses will be monitored.

## Todo
- [ ] Add course comparision
- [ ] Add messaging to user (Twillio API)

## Contribution
This script is an open-source project that relies on its users to get better. If you would like to add features, please fork and create a PR.