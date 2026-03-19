import json
import os
import logging
from tracker import check_orders 
from notifier import send_order_update_email, MailConfigError, MailAuthError, MailDeliveryError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    db_path = 'orders.json'
    if not os.path.exists(db_path):
        logger.error(f"File {db_path} not found.")
        return

    # 1. Load Data
    with open(db_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 2. Run Scraper
    logger.info("Starting sync with Egypt Post...")
    # check_orders must set order['is_updated'] = True when new_time != last_update
    has_updates = check_orders(data['orders'])

    # 3. Process Notifications
    if has_updates:
        logger.info("Updates found. Filtering for notification...")
        
        for order in data['orders']:
            # Only send if the order was actually modified this session
            if order.get('is_updated') == True:
                try:
                    send_order_update_email(order)
                except (MailConfigError, MailAuthError) as e:
                    logger.critical(f"Stopping execution: {e}")
                    break 
                except MailDeliveryError as e:
                    logger.error(f"Failed to notify for {order['order_id']}: {e}")
                finally:
                    order.pop('is_updated', None)
            else:
                logger.info(f"No changes for {order['order_id']}. Skipping email.")

        # 4. Save clean data back to JSON
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info("Database updated and saved.")
    
    else:
        logger.info("No updates detected across all tracked items.")

if __name__ == "__main__":
    main()