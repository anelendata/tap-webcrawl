import os, time, wget
from importlib.machinery import SourceFileLoader

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from . import to_csv


DOWNLOAD_TIMEOUT_SEC = 600
SLEEP_FOR_SEC = 10

DOWNLOAD_DIR = "/app/data"


def get_file(target_ext=".xls"):
    filename = None
    for filename in os.listdir(DOWNLOAD_DIR):
        if filename.endswith(target_ext):
            break
    return filename


def run_selenium(params, target_ext=".xls"):
    part_file_ext = ".part"

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

    os.environ["PATH"] = "/usr/bin/"
    test.driver = webdriver.Firefox(firefox_binary="/usr/bin/firefox",
                                    firefox_profile=profile,
                                    executable_path="/usr/bin/geckodriver",
                                    capabilities=cap)
    test.vars = {}

    test.test_untitled(params)

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

    display.stop()

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


def fetch_csv(params, encoding="utf8", offline=False):
    target_ext = "." + params.get("file_type", "xls")

    if not offline:
        filename = run_selenium(params, target_ext)
    else:
        filename = get_file(target_ext)

    print(filename)
    to_csv.from_xls_html(os.path.join(DOWNLOAD_DIR, filename),
                         os.path.join(DOWNLOAD_DIR, "data.csv"),
                         encoding=encoding)

    return os.path.join(DOWNLOAD_DIR, "data.csv")
