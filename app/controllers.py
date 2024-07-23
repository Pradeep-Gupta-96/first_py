from flask import request, jsonify, current_app
from bson.objectid import ObjectId
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import re
import time

def checkapi_items():
   return "ohm shree ganesha deva!"

def create_item():
    consignment_number = request.json.get('consignment_number')
    if not consignment_number:
        return jsonify({'error': 'Missing consignment number'}), 400

    try:
        tracking_info = main_workflow(consignment_number)
        return jsonify(tracking_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def main_workflow(consignment_number):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Optional: use headless mode if no browser UI is needed
    driver = webdriver.Chrome(options=options)
    # driver = webdriver.Chrome()

    # Open the India Post website
    driver.get("https://www.indiapost.gov.in/_layouts/15/dop.portal.tracking/trackconsignment.aspx")
    driver.implicitly_wait(1)  # Waits up to 10 seconds for elements to become available

    try:
        # Try to find the captcha element using the first expected ID
        captcha_element = driver.find_element(By.ID, "ctl00_PlaceHolderMain_ucNewLegacyControl_ucCaptcha1_imgMathCaptcha")
    except NoSuchElementException:
        # If the first ID isn't found, try the second ID
        captcha_element = driver.find_element(By.ID, "ctl00_PlaceHolderMain_ucNewLegacyControl_ucCaptcha1_imgCaptcha")

    captcha_url = captcha_element.get_attribute('src')
    print("Captcha URL:", captcha_url)

    # Get the query type from the webpage
    query_element = driver.find_element(By.ID, "ctl00_PlaceHolderMain_ucNewLegacyControl_ucCaptcha1_lblCaptcha")
    query_text = query_element.text
    print("Query:", query_text)
    # Enter the consignment number
    consignment_input = driver.find_element(By.ID, "ctl00_PlaceHolderMain_ucNewLegacyControl_txtOrignlPgTranNo")
    consignment_input.send_keys(consignment_number)
    # Analyze the captcha using Google Lens in a new tab
    driver.execute_script("window.open('https://lens.google.com');")
    driver.switch_to.window(driver.window_handles[1])
    if captcha_url:
        output_text = automate_google_lens(driver, captcha_url)

    captcha_input = driver.find_element(By.ID, "ctl00_PlaceHolderMain_ucNewLegacyControl_ucCaptcha1_txtCaptcha")
    captcha_input.send_keys(process_output_based_on_query(output_text, query_text))

    # Click the Search button
    search_button = driver.find_element(By.ID, "ctl00_PlaceHolderMain_ucNewLegacyControl_btnSearch")
    search_button.click()

    WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.col-xs-12.col-md-12")))

    # Print the tracking information
    print_tracking_information(driver)
    tracking_info = print_tracking_information(driver) 
    driver.quit()
    return tracking_info
def automate_google_lens(driver, image_url):
    driver.get("https://lens.google.com")
    driver.implicitly_wait(10)  # Ensure the page is loaded

    # Enter the image URL into Google Lens and analyze it
    input_field = driver.find_element(By.CSS_SELECTOR, "input[jsname='W7hAGe']")
    input_field.send_keys(image_url)
    search_button = driver.find_element(By.CSS_SELECTOR, "div[jsname='ZtOxCb']")
    search_button.click()
    driver.implicitly_wait(10)  # Ensure the page is loaded

    # Switch to Text mode
    text_mode_button = driver.find_element(By.XPATH, "//button[@aria-label='Switch to Text mode']")
    text_mode_button.click()
    time.sleep(1)
    # Click 'Select all text' using XPath that directly targets text content
    select_all_button = driver.find_element(By.XPATH, "//span[contains(text(), 'Select all text')]")
    select_all_button.click()
    time.sleep(1) # Ensure the page is loaded

    # Extract the output text from the specified <h1> element
    try:
        output_text_element = driver.find_element(By.XPATH, "//h1[@jsname='r4nke']")
        output_text = output_text_element.text
        print("Extracted Text:", output_text)
    except Exception as e:
        print("Failed to extract text:", e)
    
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return output_text


def process_output_based_on_query(text, query):
    if 'number' in query:
        numbers = re.findall(r'\d+', text)
        # Handle single item with multiple digits
        if len(numbers) == 1 and len(numbers[0]) > 1:
            numbers = list(numbers[0])
        print("All numbers extracted:", numbers)

        number_words = {'First': 0, 'Second': 1, 'Third': 2, 'Fourth': 3, 'Fifth': 4, 'Sixth': 5}
        number_index = number_words[query.split()[2]]

        if len(numbers) > number_index:
            print(f"{query.split()[2]} number:", numbers[number_index])
            coutput=numbers[number_index]
        else:
            print(f"{query.split()[2]} number: Not found")
    elif 'Expression' in query:
        try:
            # Clean and evaluate the expression
            result = eval(re.sub(r'[^\d\+\-\*/]', '', text))
            print("Evaluated result:", result)
            coutput=result
        except Exception as e:
            print("Error evaluating expression:", e)
    else:
        print("Extracted Text:", text)
        coutput=text
    return coutput

def print_tracking_information(driver):
    wait = WebDriverWait(driver, 30)

    try:
        # Wait and get the article type element
        try:

            article_type_row = wait.until(EC.presence_of_element_located((By.XPATH, "//th[contains(text(), 'Article Type')]/../following-sibling::tr/td")))
            article_type = article_type_row.text
        except Exception as err:
            article_type = 'Not Available'

        # Get event details
        event_details = wait.until(EC.presence_of_element_located((By.ID, "ctl00_PlaceHolderMain_ucNewLegacyControl_lblMailArticleDtlsOER"))).text

        # Get current status
        current_status = wait.until(EC.presence_of_element_located((By.ID, "ctl00_PlaceHolderMain_ucNewLegacyControl_lblMailArticleCurrentStatusOER"))).text

        # Get event table
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
        print(f"An error occurred: {str(e)}")
        return {}


def get_items():
    items = list(current_app.db.items.find())
    for item in items:
        item['_id'] = str(item['_id'])
    return jsonify(items), 200

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
