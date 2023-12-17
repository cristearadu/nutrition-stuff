import os
import json
from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options as ChromeOptions


MAIN_URL = "https://www.mega-image.ro/Dulciuri-si-snacks/c/006"
COOKIES = (By.XPATH, '//button[@data-testid="cookie-popup-accept"]')
MAIN_PRODUCT_LOCATOR = (By.XPATH, '//a[@data-testid="product-block-name-link"]')
LOAD_MORE_WRAPPER = (By.XPATH, '//*[@data-testid="vertical-load-more-wrapper"]')
PRODUCT_TITLE = (By.XPATH, '//*[@data-testid="product-common-header-title"]')
NUTRITIONAL_TABLE = ['Grasimi', 'Valoare energetica', 'Fibre', 'Sodiu', 'Proteine', 'Grasimi saturate']
OTHER_PRODUCT_INFO = ['Ingrediente', 'Alergeni']


def create_chromedriver_instance():
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration

    webdriver_manager = ChromeDriverManager()
    webdriver_manager.install()  # Install or update ChromeDriver

    # Create the ChromeDriver instance
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()  # Maximizing window to ensure proper scrolling
    driver.set_window_position(0, 0)  # Setting window position
    driver.set_window_size(1920, 1080)  # Setting window size
    driver.set_page_load_timeout(30)  # Setting page load timeout

    return driver


def write_into_json_file(python_dict, filename='total_products.json'):
    with open(filename, 'w+') as json_file:
        json.dump(python_dict, json_file, indent=2)


def get_product_names():
    WebDriverWait(driver, 10).until(EC.presence_of_element_located(MAIN_PRODUCT_LOCATOR))
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located(LOAD_MORE_WRAPPER))
    load_more_element = driver.find_element(*LOAD_MORE_WRAPPER)

    while True:
        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'auto', block: 'center' });", load_more_element)
        try:
            WebDriverWait(driver, 10).until_not(EC.presence_of_element_located(LOAD_MORE_WRAPPER))
            total_products_list = driver.find_elements(*MAIN_PRODUCT_LOCATOR)
            break
        except TimeoutException:
            print("The list has not finished loading")

    total_products_dict = {}
    for product_element in total_products_list:
        product_name = product_element.text
        total_products_dict[product_name] = {'link': product_element.get_attribute("href")}

    write_into_json_file(total_products_dict)
    return total_products_dict


def extract_product_data():
    for product_name, product_info in total_products.items():
        product_link = product_info['link']
        driver.get(product_link)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located(PRODUCT_TITLE))
        product_title = driver.find_element(*PRODUCT_TITLE)
        assert product_name in product_title.text, f"something went wrong, the name is not in the title:" \
                                                   f" product name -{product_name}- product title -{product_title}-"

        nutritional_info = {}

        for nutrient in NUTRITIONAL_TABLE:
            nutrient_custom_xpath = (By.XPATH, f'//td[contains(text(),"{nutrient}")]/../td[2]')
            try:
                nutrient_element = driver.find_element(*nutrient_custom_xpath)
                nutrient_value = nutrient_element.get_attribute("innerText").strip()
            except NoSuchElementException:
                nutrient_value = "N/A"
            nutritional_info[nutrient] = nutrient_value

        total_products[product_name]['nutritional_info'] = nutritional_info

        for other_info_title in OTHER_PRODUCT_INFO:
            ingredients_custom_xpath = (By.XPATH, f'//*[contains(text(), "{other_info_title}")]/'
                                                  'ancestor::*[@data-testid="more-than"]/div')
            try:
                other_element = driver.find_element(*ingredients_custom_xpath)
                other_element_value = other_element.get_attribute("innerText").strip()
            except NoSuchElementException:
                other_element_value = "N/A"
            total_products[product_name][other_info_title] = other_element_value

        write_into_json_file(total_products)


if __name__ == "__main__":
    try:
        driver = create_chromedriver_instance()
        driver.get(MAIN_URL)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located(COOKIES))
        element_to_click = driver.find_element(*COOKIES)
        element_to_click.click()

        file_exists = os.path.exists('total_products.json')
        if file_exists:
            with open('total_products.json', 'r') as json_file:
                total_products = json.load(json_file)
        else:
            total_products = get_product_names()
            extract_product_data()

    finally:
        driver.quit()
