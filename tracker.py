import json
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuration
SERIAL_DEBUG    = True
HEADLESS_MODE   = True
GITHUB_WORKFLOW = False

def d_print(*args, **kwargs):
    if SERIAL_DEBUG:
        kwargs.setdefault('flush', True)
        print(*args, **kwargs)

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

def check_orders(orders_list):
    options = uc.ChromeOptions()
    
    # Environment detection logic
    is_github = GITHUB_WORKFLOW or (os.getenv('GITHUB_ACTIONS') == 'true')
    
    if is_github or HEADLESS_MODE:
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36')

    # GitHub Actions runners manage their own driver versions
    if is_github:
        driver = uc.Chrome(options=options)
    else:
        # Local Debian laptop uses the forced v145 driver
        driver = uc.Chrome(options=options, version_main=145)
        
    url = "https://egyptpost.gov.eg/ar-EG/Home/EServices/Track-And-Trace"
    updated_any = False

    try:
        d_print(f"[>] Initializing Session (Force GitHub Mode: {is_github})...")
        driver.get(url)

        for order in orders_list:
            oid = order['order_id']
            d_print(f"[SCANNING] ID: {oid}")

            try:
                # 1. Wait for input
                search_input = WebDriverWait(driver, 20, poll_frequency=0.1).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "input.input0"))
                )
                search_input.clear()
                search_input.send_keys(oid)

                # 2. Click search
                search_btn = WebDriverWait(driver, 10, poll_frequency=0.1).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.custBtn"))
                )
                driver.execute_script("arguments[0].click();", search_btn)

                # 3. Hybrid Wait for Result or No Data
                WebDriverWait(driver, 20, poll_frequency=0.1).until(
                    lambda d: d.find_elements(By.CSS_SELECTOR, ".order__container.--progress, .order__container.--done") or 
                             "لا يوجد بيانات" in d.find_element(By.TAG_NAME, "body").text
                )

                steps = driver.find_elements(By.CSS_SELECTOR, ".order__container.--progress, .order__container.--done")
                
                if not steps:
                    status, new_time = "no data yet", "N/A"
                else:
                    latest_step = steps[-1]
                    status = get_mapped_status(latest_step.text)
                    lines = [line.strip() for line in latest_step.text.split('\n') if line.strip()]
                    arabic_time = f"{lines[-2]} {lines[-1]}" if len(lines) >= 2 else "Unknown Time"
                    new_time = translate_to_english(arabic_time)
                
                # 4. Check for Updates
                if new_time != order['last_update']:
                    d_print(f"   >>> ALERT: {status.upper()} | {new_time}")
                    order['last_status'], order['last_update'] = status, new_time
                    updated_any = True
                else:
                    d_print(f"   >>> OK: {status} ({new_time})")

                driver.get(url) 

            except Exception as e:
                d_print(f"   [!] Error on {oid}. Skipping...")
                driver.get(url)
                continue

    finally:
        d_print("[>] Closing Chrome Session...")
        driver.quit()
        return updated_any

def main():
    if not os.path.exists('orders.json'): 
        print("Error: orders.json not found.")
        return
        
    with open('orders.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    has_updates = check_orders(data['orders'])

    if has_updates:
        with open('orders.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        d_print("\n[DONE] Database updated.")
    else:
        d_print("\n[DONE] No status changes.")

if __name__ == "__main__":
    main()