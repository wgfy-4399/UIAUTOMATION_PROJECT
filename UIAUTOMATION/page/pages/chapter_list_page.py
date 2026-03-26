from time import sleep

from selenium.webdriver.common.by import By

from utils.driver_utils import get_driver
from page.base_page import BasePage




class ChapterList(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
