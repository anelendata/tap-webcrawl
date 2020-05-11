import json, logging, os, sys, time, wget
from importlib.machinery import SourceFileLoader

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from . import to_csv


logging.basicConfig(stream=sys.stdout,
                    format="%(asctime)s - " + str(__name__) + " - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO)
logger = logging.getLogger(__name__)


DOWNLOAD_TIMEOUT_SEC = 600
SLEEP_FOR_SEC = 10

DOWNLOAD_DIR = "/app/data"


def get_file(target_ext=".xls"):
    filename = None
    for filename in os.listdir(DOWNLOAD_DIR):
        if filename.endswith(target_ext):
            break
    return filename


def install_ff_extension(driver, extension_path):
    """
    Must be the full path to an XPI file!
    """
    driver.install_addon(extension_path, temporary=True)


def subscribe_acp_msg(driver):
    js = """window.addEventListener('message', function (event) {
            if (typeof event.data.sender === 'undefined' || event.data.sender != 'antiCaptchaPlugin') {
                        return;
                    }

                // event.data contains all the data that were passed
                console.log(JSON.stringify(event.data));
                var node = document.createElement("P");
                var textnode = document.createTextNode(JSON.stringify(event.data));
                node.appendChild(textnode);
                document.body.appendChild(node);
            });"""
    return driver.execute_script(js)


# The API messages sending directly to the plugin
# For example for the anti-captcha.com API key init which is required for the plugin work
# Works only on the normal HTML web page
# https://antcpt.com/blank.html in our case
# Won't work on pages like about:blank etc
def acp_api_send_request(driver, message_type, data={}):
    message = {
               # this receiver has to be always set as antiCaptchaPlugin
               "receiver": "antiCaptchaPlugin",
               # request type, for example setOptions
               "type": message_type,
               # merge with additional data
               **data
    }
    # run JS code in the web page context
    # preceicely we send a standard window.postMessage method
    return driver.execute_script("return window.postMessage({}, '*');".format(json.dumps(message)))


def antcpt_auth(driver, auth_key):
   # Go to the empty page for setting the API key through the plugin API request
    driver.get("https://antcpt.com/blank.html")
    # Setting up the anti-captcha.com API key
    # replace YOUR-ANTI-CAPTCHA-API-KEY to your actual API key, which you can get from here:
    # https://anti-captcha.com/clients/settings/apisetup
    subscribe_acp_msg(driver)
    msg = {"options": {"enable": True, "antiCaptchaApiKey": auth_key}}
    acp_api_send_request(driver, "setOptions", msg)
    time.sleep(3)


def wait_for_download(target_ext):
    part_file_ext = ".part"
    file_size = 0
    prev_file_size = 0

    part_file_size = 0
    prev_part_file_size = 0

    # Wait for downlaod
    elapsed_time = 0
    while elapsed_time < DOWNLOAD_TIMEOUT_SEC:
        elapsed_time = elapsed_time + SLEEP_FOR_SEC
        time.sleep(SLEEP_FOR_SEC)

        filename = get_file(target_ext=target_ext)
        part_filename = get_file(target_ext=part_file_ext)

        if not filename and not part_filename:
            continue

        if filename:
            file_size = os.stat(os.path.join(DOWNLOAD_DIR, filename)).st_size
        if part_filename:
            part_file_size = os.stat(os.path.join(DOWNLOAD_DIR, part_filename)).st_size

        if prev_file_size == file_size and prev_part_file_size == part_file_size:  # No progress for <SLEEP_FOR_SEC> seconds
            break

        prev_file_size = file_size
        prev_part_file_size = part_file_size

    # Wait for copying part to real
    elapsed_time = 0
    while file_size == 0 and elapsed_time < DOWNLOAD_TIMEOUT_SEC:
        elapsed_time = elapsed_time + SLEEP_FOR_SEC
        time.sleep(SLEEP_FOR_SEC)
        filename = get_file(target_ext=target_ext)
        file_size = os.stat(os.path.join(DOWNLOAD_DIR, filename)).st_size

    if not filename:
        raise Exception("File failed to download")

    if file_size == 0:
        raise Exception("File is empty")

    return filename


def run_selenium(params, target_ext="html"):
    anticaptcha_key = params.get("anticaptcha_key")
    selenium_ide_python_file = params["selenium_ide_script"]
    display = Display(visible=0, size=(1024, 768))
    display.start()

    selenium_ide = SourceFileLoader("module.name", selenium_ide_python_file).load_module()
    test = selenium_ide.TestDefaultSuite()

    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", DOWNLOAD_DIR)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "multipart/x-zip,application/zip,application/x-zip-compressed,application/x-compressed,application/msword,application/csv,text/csv,image/png ,image/jpeg, application/pdf, text/html,text/plain,  application/excel, application/vnd.ms-excel, application/x-excel, application/x-msexcel, application/octet-stream, application/x-gzip")

    cap = DesiredCapabilities().FIREFOX
    cap["marionette"] = True

    # Enable logging
    # cap["loggingPrefs"] = { "browser":"ALL" }
    # profile.set_preference("webdriver.log.file", "./firefox_console.txt")

    os.environ["PATH"] = "/usr/bin/"
    test.driver = webdriver.Firefox(firefox_binary="/usr/bin/firefox",
                                    firefox_profile=profile,
                                    executable_path="/usr/bin/geckodriver",
                                    capabilities=cap)
    test.vars = {}

    if anticaptcha_key is not None:
        # https://antcpt.com/eng/information/recaptcha-2-selenium.html#selenium_captcha_solve_example
        # https://anti-captcha.com/mainpage
        # https://intoli.com/blog/firefox-extensions-with-selenium/
        extension_path = "/usr/local/anticaptcha-plugin_v0.49.xpi"
        # extension_path = "/volume/thirdparty/web_driver/anticaptcha-plugin_v0.49.xpi"
        install_ff_extension(test.driver, extension_path)
        logger.info("Sending antiCaptchaApiKey")
        antcpt_auth(test.driver, anticaptcha_key)

    filename = None
    for attr in dir(test):
        if attr[0:5] == "test_" and callable(getattr(test, attr)):
            logger.info("Running " + attr)
            getattr(test, attr)(params)
        if target_ext == "html":
            filename = attr[5:] + "_" + params["html_result_filename"]
            with open(filename, "a") as f:
              html = test.driver.execute_script("return document.documentElement.outerHTML;")
              f.write(html)

    if target_ext is not None and target_ext != "html":
        filename = wait_for_download(target_ext)

    display.stop()

    return filename


def fetch_csv(params, encoding="utf8", offline=False):
    target_ext = "." + params.get("file_type", "html")
    dst_filename = params.get("csv_destination_filename", "data.csv")

    if not offline:
        filename = run_selenium(params, target_ext)
    else:
        filename = get_file(target_ext)

    logger.info("file: %s (offline mode: %s)" % (os.path.join(DOWNLOAD_DIR, filename), str(offline)))

    if target_ext == "xls":
        to_csv.from_xls_html(os.path.join(DOWNLOAD_DIR, filename),
                             os.path.join(DOWNLOAD_DIR, dst_filename),
                             encoding=encoding)

    return os.path.join(DOWNLOAD_DIR, dst_filename)
