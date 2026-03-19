import os
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

def translate_to_english(arabic_str):
    replacements = {
        "يناير": "January", "فبراير": "February", "مارس": "March",
        "أبريل": "April", "مايو": "May", "يونيو": "June",
        "يوليو": "July", "أغسطس": "August", "سبتمبر": "September",
        "أكتوبر": "October", "نوفمبر": "November", "ديسمبر": "December",
        "صباحاً": "AM", "مساءً": "PM"
    }
    for ar, en in replacements.items():
        arabic_str = arabic_str.replace(ar, en)
    return arabic_str

def get_mapped_status(text):
    if "لا يوجد بيانات" in text: return "no data yet"
    if "اكتمال الطلب" in text or "تم التسليم" in text: return "delivered"
    if "التسليم" in text: return "out for delivery"
    if "النقل والمعالجة" in text: return "passed customs"
    if "الشحن" in text: return "received"
    if "التسجيل" in text: return "registered"
    return "UNKNOWN"

def check_orders(orders_list, headless=True):
    options = uc.ChromeOptions()
    if headless:
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36')

    driver = uc.Chrome(options=options, version_main=145)
    driver.set_window_size(1920, 1080)
    url = "https://egyptpost.gov.eg/ar-EG/Home/EServices/Track-And-Trace"
    updated_any = False

    try:
        driver.get(url)
        for order in orders_list:
            oid = order['order_id']
            # Default flag to False at start of check
            order['is_updated'] = False 

            try:
                search_input = WebDriverWait(driver, 20).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "input.input0"))
                )
                search_input.clear()
                search_input.send_keys(oid)

                search_btn = driver.find_element(By.CSS_SELECTOR, "a.custBtn")
                driver.execute_script("arguments[0].click();", search_btn)

                WebDriverWait(driver, 20).until(
                    lambda d: d.find_elements(By.CSS_SELECTOR, ".order__container.--progress, .order__container.--done") or 
                             "لا يوجد بيانات" in d.find_element(By.TAG_NAME, "body").text
                )

                steps = driver.find_elements(By.CSS_SELECTOR, ".order__container.--progress, .order__container.--done")
                
                if not steps:
                    status, new_time = "no data yet", "N/A"
                else:
                    latest_step = steps[-1]
                    status = get_mapped_status(latest_step.text)
                    lines = [l.strip() for l in latest_step.text.split('\n') if l.strip()]
                    arabic_time = f"{lines[-2]} {lines[-1]}" if len(lines) >= 2 else "Unknown Time"
                    new_time = translate_to_english(arabic_time)
                
                if new_time != order['last_update']:
                    logger.warning(f"Change detected for {oid}")
                    order['last_status'] = status
                    order['last_update'] = new_time
                    order['is_updated'] = True
                    updated_any = True
                
                driver.get(url) 

            except Exception as e:
                logger.error(f"Error scanning {oid}: {e}")
                driver.get(url)

    finally:
        driver.quit()
        return updated_any