import os
import pickle as pk
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.wait import WebDriverWait

debug = False


def d_print(msg):
    """Prints status messages only if debug flag is used"""
    if debug:
        print(msg)


class Monitor:
    browser, sid, usr_name, passwd, cookies = None, None, None, None, None
    login_fail = False

    @staticmethod
    def __course_link_builder(sid: str, uid: str):
        return 'https://utdirect.utexas.edu/apps/registrar/course_schedule/{}/{}/' \
            .format(sid, uid)

    @staticmethod
    def __register_link_builder(sid: str, uid: str):
        return 'https://utdirect.utexas.edu/registration/registration.WBX?' \
               's_ccyys={}&s_af_unique={}'.format(sid, uid)

    @staticmethod
    def logged_in() -> bool:
        return ('UT Austin Registrar:' in Monitor.browser.title and
                'course search' in Monitor.browser.title) or \
               'Registration' in Monitor.browser.title

    @staticmethod
    def __do_login_seq() -> bool:

        if Monitor.login_fail:
            return False

        browser = Monitor.browser
        try:
            if 'Sign in with your UT EID' in browser.title:

                heading = browser.find_element_by_xpath("//div[@id='message']/h1").text

                if 'Sign in with your UT EID' in heading:

                    if Monitor.usr_name and Monitor.passwd:
                        username_field = browser.find_element_by_id('username')
                        username_field.clear()
                        username_field.send_keys(Monitor.usr_name)

                        password_field = browser.find_element_by_id('password')
                        password_field.clear()
                        password_field.send_keys(Monitor.passwd)

                        login_btn = browser.find_element_by_xpath("//input[@type='submit']")
                        login_btn.click()

                elif 'Multi-Factor Authentication Required' in heading:

                    iframe = browser.find_element_by_id('duo_iframe')

                    try:
                        browser.switch_to.frame(iframe)
                        messages = browser.find_elements_by_xpath(
                            "//div[@id='messages-view']"
                            "/div[@class='messages-list']"
                            "/div")

                        push_active = False
                        for message in messages:
                            if message.get_attribute('aria-hidden') == 'true':
                                continue
                            if 'info' in message.get_attribute('class'):
                                push_active = 'Pushed a login request to your device...' in message.text
                                break
                            if 'error' in message.get_attribute('class'):
                                Monitor.login_fail = True
                                break

                        if not push_active and not Monitor.login_fail:

                            remember_me = browser.find_element_by_xpath(
                                "//div[@class='stay-logged-in']"
                                "/label[@class='remember_me_label_field']"
                                "/input[@type='checkbox']")

                            if not remember_me.is_selected():
                                remember_me.click()

                            # send push button
                            browser.find_element_by_xpath(
                                "(//button[contains(@class, 'auth-button')])[1]").click()
                    except StaleElementReferenceException:
                        pass  # in case the frame changed, to prevent error
                    browser.switch_to.default_content()
        except Exception:
            pass
        return Monitor.logged_in()

    @staticmethod
    def login():
        Monitor.login_fail = False  # method acts as a reset for manual login

        Monitor.load_cookies()
        Monitor.__goto_page("https://utdirect.utexas.edu/apps/registrar/course_schedule/{}/"
                            .format(Monitor.sid))
        Monitor.save_cookies()
        return Monitor.logged_in()

    @staticmethod
    def save_cookies():
        Monitor.cookies = Monitor.browser.get_cookies()
        # print(current_user.cookies)
        # pk.dump(Monitor.browser.get_cookies(), open(Monitor.cookie_path, "wb"))  # save cookies

    @staticmethod
    def load_cookies():
        Monitor.browser.get("https://www.utexas.edu/")
        print(Monitor.cookies)
        if Monitor.cookies:
            for cookie in Monitor.cookies:
                Monitor.browser.add_cookie(cookie)

    @staticmethod
    def register(uid: str, add_waitlist=True):

        def click_submit():
            form = Monitor.browser.find_element_by_id('regform')
            submit = form.find_element_by_name('s_submit')
            submit.click()

        print("attempting to register for course {}".format(uid))
        Monitor.__goto_page(Monitor.__register_link_builder(Monitor.sid, uid))

        click_submit()

        waitlist = Monitor.browser.find_elements_by_id('s_request_STAWL')
        if len(waitlist) > 0 and add_waitlist:
            waitlist[0].click()
            click_submit()
        status_msg = Monitor.browser.find_element_by_id('n_message').text
        return 'fail' if 'unsuccessful' in status_msg else 'success'

    @staticmethod
    def __goto_page(link: str):
        print('browser going to {}'.format(link))
        Monitor.browser.get(link)

        # wait until user logs in and the courses can be seen
        try:
            WebDriverWait(Monitor.browser, timeout=60) \
                .until(lambda x: Monitor.__do_login_seq())
        except TimeoutException:
            # fail login here and force manual login
            Monitor.login_fail = True
        return Monitor.browser

    @staticmethod
    def get_course_page(uid: str):
        if Monitor.login_fail:
            return None
        return Monitor.__goto_page(
            Monitor.__course_link_builder(Monitor.sid, uid)).page_source
