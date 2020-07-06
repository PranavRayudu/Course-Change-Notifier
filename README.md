# UT Course Monitor
UT Course Monitor is a simple script that allows users to run a course availability checker in the background and notify them if a desired course opens up in the schedule.
This requires Python 3.6+

## Get Started
```
git clone <url>
pip install -r requirements.txt
```

Download the webdriver of your faviorite browser and add it to the PATH variable or place it in the project folder. 
Chrome drivers are available [here](https://chromedriver.chromium.org/downloads).

You will need a Twillio account to send SMS messages to your phone when a course opens up.
> section in progress

To configure your project, create a ``.env`` file and add the following data
To run the project, simply run ``python course-monitor.py --page=<link of page>``

## Todo
- [x] Add Twillio API

## Contribution
This script is an open-source project that relies on its users to get better. If you would like to add features, please fork and create a PR.