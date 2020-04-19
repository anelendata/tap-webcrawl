import os, wget

from pyvirtualdisplay import Display
from selenium import webdriver

from . import selenium_ide
from . import to_csv


DOWNLOAD_DIR = "/app/data"

def run_selenium():
    display = Display(visible=0, size=(1024, 768))
    display.start()

    test = selenium_ide.TestDefaultSuite()

    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", DOWNLOAD_DIR)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "multipart/x-zip,application/zip,application/x-zip-compressed,application/x-compressed,application/msword,application/csv,text/csv,image/png ,image/jpeg, application/pdf, text/html,text/plain,  application/excel, application/vnd.ms-excel, application/x-excel, application/x-msexcel, application/octet-stream, application/x-gzip")

    test.driver = webdriver.Firefox(firefox_profile=profile)
    test.vars = {}

    test.test_untitled()

def fetch_csv():
    run_selenium()

    filename = None
    for filename in os.listdir(DOWNLOAD_DIR):
        if filename.endswith(".xls"):
            break

    to_csv.from_xls_html(os.path.join(DOWNLOAD_DIR, filename),
                         os.path.join(DOWNLOAD_DIR, "data.csv"))

    return os.path.join(DOWNLOAD_DIR, "data.csv")
