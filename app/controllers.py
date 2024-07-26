# app/controllers.py
from flask import request, jsonify, current_app
from bson.objectid import ObjectId
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import re
import time

def checkapi_items():
   return "Welcome to the Home Page!"

def create_item():
    consignment_number = request.json.get('consignment_number')
    if not consignment_number:
        current_app.logger.error('Missing consignment number')
        return jsonify({'error': 'Missing consignment number'}), 400

    try:
        tracking_info = main_workflow(consignment_number)
        return jsonify(tracking_info)
    except Exception as e:
        current_app.logger.error('Error in create_item: %s', str(e))
        return jsonify({'error': str(e)}), 500

def main_workflow(consignment_number):
    options = webdriver.ChromeOptions()
    # Options for ChromeDriver
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode (no GUI)
    chrome_options.add_argument('--disable-gpu')  # Disable GPU acceleration
    chrome_options.add_argument('--no-sandbox')  # No sandboxing (if needed)
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")

    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://www.indiapost.gov.in/_layouts/15/dop.portal.tracking/trackconsignment.aspx")
        driver.implicitly_wait(1)
        
        try:
            captcha_element = driver.find_element(By.ID, "ctl00_PlaceHolderMain_ucNewLegacyControl_ucCaptcha1_imgMathCaptcha")
        except NoSuchElementException:
            captcha_element = driver.find_element(By.ID, "ctl00_PlaceHolderMain_ucNewLegacyControl_ucCaptcha1_imgCaptcha")

        captcha_url = captcha_element.get_attribute('src')
        current_app.logger.info("Captcha URL: %s", captcha_url)

        query_element = driver.find_element(By.ID, "ctl00_PlaceHolderMain_ucNewLegacyControl_ucCaptcha1_lblCaptcha")
        query_text = query_element.text
        current_app.logger.info("Query: %s", query_text)

        consignment_input = driver.find_element(By.ID, "ctl00_PlaceHolderMain_ucNewLegacyControl_txtOrignlPgTranNo")
        consignment_input.send_keys(consignment_number)

        driver.execute_script("window.open('https://lens.google.com');")
        driver.switch_to.window(driver.window_handles[1])
        if captcha_url:
            output_text = automate_google_lens(driver, captcha_url)

        captcha_input = driver.find_element(By.ID, "ctl00_PlaceHolderMain_ucNewLegacyControl_ucCaptcha1_txtCaptcha")
        captcha_input.send_keys(process_output_based_on_query(output_text, query_text))

        search_button = driver.find_element(By.ID, "ctl00_PlaceHolderMain_ucNewLegacyControl_btnSearch")
        search_button.click()

        WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.col-xs-12.col-md-12")))

        tracking_info = print_tracking_information(driver)
        driver.quit()
        return tracking_info

    except Exception as e:
        current_app.logger.error('Error in main_workflow: %s', str(e))
        driver.quit()
        raise

def automate_google_lens(driver, image_url):
    try:
        driver.get("https://lens.google.com")
        driver.implicitly_wait(10)

        input_field = driver.find_element(By.CSS_SELECTOR, "input[jsname='W7hAGe']")
        input_field.send_keys(image_url)
        search_button = driver.find_element(By.CSS_SELECTOR, "div[jsname='ZtOxCb']")
        search_button.click()
        time.sleep(.25)
        text_mode_button = driver.find_element(By.XPATH, "//button[@aria-label='Switch to Text mode']")
        text_mode_button.click()
        time.sleep(.25)
        select_all_button = driver.find_element(By.XPATH, "//span[contains(text(), 'Select all text')]")
        select_all_button.click()
        time.sleep(.25)

        try:
            output_text_element = driver.find_element(By.XPATH, "//h1[@jsname='r4nke']")
            output_text = output_text_element.text
            current_app.logger.info("Extracted Text: %s", output_text)
        except Exception as e:
            current_app.logger.error("Failed to extract text: %s", str(e))
            output_text = ''
        
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        return output_text

    except Exception as e:
        current_app.logger.error('Error in automate_google_lens: %s', str(e))
        driver.quit()
        raise

def process_output_based_on_query(text, query):
    coutput = ''
    if 'number' in query:
        numbers = re.findall(r'\d+', text)
        if len(numbers) == 1 and len(numbers[0]) > 1:
            numbers = list(numbers[0])
        current_app.logger.info("All numbers extracted: %s", numbers)

        number_words = {'First': 0, 'Second': 1, 'Third': 2, 'Fourth': 3, 'Fifth': 4, 'Sixth': 5}
        number_index = number_words.get(query.split()[2], 0)

        if len(numbers) > number_index:
            current_app.logger.info(f"{query.split()[2]} number: %s", numbers[number_index])
            coutput = numbers[number_index]
        else:
            current_app.logger.info(f"{query.split()[2]} number: Not found")
    elif 'Expression' in query:
        try:
            result = eval(re.sub(r'[^\d\+\-\*/]', '', text))
            current_app.logger.info("Evaluated result: %s", result)
            coutput = result
        except Exception as e:
            current_app.logger.error("Error evaluating expression: %s", str(e))
    else:
        current_app.logger.info("Extracted Text: %s", text)
        coutput = text
    return coutput

def print_tracking_information(driver):
    wait = WebDriverWait(driver, 30)

    try:
        try:
            article_type_row = wait.until(EC.presence_of_element_located((By.XPATH, "//th[contains(text(), 'Article Type')]/../following-sibling::tr/td")))
            article_type = article_type_row.text
        except Exception as e:
            article_type = 'Not Available'

        event_details = wait.until(EC.presence_of_element_located((By.ID, "ctl00_PlaceHolderMain_ucNewLegacyControl_lblMailArticleDtlsOER"))).text
        current_status = wait.until(EC.presence_of_element_located((By.ID, "ctl00_PlaceHolderMain_ucNewLegacyControl_lblMailArticleCurrentStatusOER"))).text
        events_table = wait.until(EC.presence_of_element_located((By.ID, "ctl00_PlaceHolderMain_ucNewLegacyControl_gvTrckMailArticleEvntOER")))

        rows = events_table.find_elements(By.TAG_NAME, "tr")
        events = []
        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            if columns:
                event = {
                    "Date": columns[0].text,
                    "Time": columns[1].text,
                    "Office": columns[2].text,
                    "Event": columns[3].text
                }
                events.append(event)

        return {
            "Article Type": article_type,
            "Event Details": event_details,
            "Current Status": current_status,
            "Events": events
        }

    except Exception as e:
        current_app.logger.error("An error occurred while fetching tracking information: %s", str(e))
        return {}

def get_items():
    try:
        items = list(current_app.db.items.find())
        for item in items:
            item['_id'] = str(item['_id'])
        return jsonify(items), 200
    except Exception as e:
        current_app.logger.error('Error in get_items: %s', str(e))
        return jsonify({'error': str(e)}), 500

def update_item(item_id):
    data = request.get_json()
    result = current_app.db.items.update_one(
        {'_id': ObjectId(item_id)},
        {'$set': {'name': data.get('name')}}
    )
    if result.matched_count == 0:
        return jsonify({'error': 'Item not found'}), 404
    return jsonify({'success': True}), 200

def delete_item(item_id):
    result = current_app.db.items.delete_one({'_id': ObjectId(item_id)})
    if result.deleted_count == 0:
        return jsonify({'error': 'Item not found'}), 404
    return '', 204
