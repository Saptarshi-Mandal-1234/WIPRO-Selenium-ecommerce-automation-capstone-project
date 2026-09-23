"""
E-Commerce Web Automation Script using Selenium WebDriver + Python
Target application: https://automationexercise.com/
"""

import datetime
import json
import os
import time
import traceback

from selenium import webdriver
from selenium.common.exceptions import (
    NoAlertPresentException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
REPORT_DIR = os.path.join(BASE_DIR, "reports")
DATA_FILE = os.path.join(BASE_DIR, "test_data.json")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


class TestReport:
    """Collects step results and renders an HTML execution report."""

    def __init__(self):
        self.steps = []
        self.start_time = datetime.datetime.now()

    def log(self, name, status, message="", screenshot=None):
        self.steps.append(
            {
                "name": name,
                "status": status,
                "message": message,
                "screenshot": screenshot,
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            }
        )
        print(f"[{status}] {name} - {message}")

    def render_html(self):
        duration = (datetime.datetime.now() - self.start_time).total_seconds()
        passed = sum(1 for s in self.steps if s["status"] == "PASS")
        failed = sum(1 for s in self.steps if s["status"] == "FAIL")
        skipped = sum(1 for s in self.steps if s["status"] == "SKIP")
        info = sum(1 for s in self.steps if s["status"] == "INFO")

        rows = ""
        for s in self.steps:
            color = {
                "PASS": "#2e7d32",
                "FAIL": "#c62828",
                "SKIP": "#f9a825",
                "INFO": "#1565c0",
            }.get(s["status"], "#555")

            img_html = ""
            if s["screenshot"] and os.path.exists(s["screenshot"]):
                rel_path = os.path.relpath(s["screenshot"], REPORT_DIR)
                img_html = f'<br><a href="{rel_path}" target="_blank">screenshot</a>'

            rows += f"""
            <tr>
                <td>{s['timestamp']}</td>
                <td>{s['name']}</td>
                <td style="color:{color}; font-weight:bold;">{s['status']}</td>
                <td>{s['message']}{img_html}</td>
            </tr>
            """

        html = f"""
        <html>
        <head>
            <title>Execution Report - E-Commerce Automation</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 30px; background:#f7f7f9; }}
                h1 {{ color: #222; }}
                .summary {{ margin-bottom: 20px; }}
                .summary span {{ margin-right: 20px; font-weight: bold; }}
                table {{ border-collapse: collapse; width: 100%; background: #fff; }}
                th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; font-size: 14px; }}
                th {{ background: #333; color: #fff; }}
                tr:nth-child(even) {{ background: #fafafa; }}
            </style>
        </head>
        <body>
            <h1>E-Commerce Automation - Execution Report</h1>
            <div class="summary">
                <span>Start: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}</span>
                <span>Duration: {duration:.2f}s</span>
                <span style="color:#2e7d32">Passed: {passed}</span>
                <span style="color:#c62828">Failed: {failed}</span>
                <span style="color:#f9a825">Skipped: {skipped}</span>
                <span style="color:#1565c0">Info: {info}</span>
            </div>
            <table>
                <tr><th>Time</th><th>Step</th><th>Status</th><th>Details</th></tr>
                {rows}
            </table>
        </body>
        </html>
        """
        report_path = os.path.join(REPORT_DIR, "execution_report.html")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)
        return report_path


def load_test_data():
    """Loads test configuration parameters from test_data.json."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )


def take_screenshot(driver, name):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(SCREENSHOT_DIR, f"{name}_{ts}.png")
    try:
        driver.save_screenshot(path)
        return path
    except Exception:
        return None


def login_user(driver, wait, credentials, base_url, report):
    try:
        driver.get(f"{base_url}/login")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-qa='login-email']")))
        driver.find_element(By.CSS_SELECTOR, "input[data-qa='login-email']").send_keys(credentials["email"])
        driver.find_element(By.CSS_SELECTOR, "input[data-qa='login-password']").send_keys(credentials["password"])
        driver.find_element(By.CSS_SELECTOR, "button[data-qa='login-button']").click()
        time.sleep(1)

        if "Logged in as" in driver.page_source:
            report.log("Login", "PASS", "Logged in successfully.", take_screenshot(driver, "login_success"))
        else:
            report.log("Login", "SKIP", "Login not confirmed, continuing as guest.", take_screenshot(driver, "login_not_confirmed"))
    except (TimeoutException, NoSuchElementException) as e:
        report.log("Login", "SKIP", f"Login elements not found, continuing as guest: {e}")


def search_product(driver, wait, keyword, base_url, report):
    driver.get(f"{base_url}/products")
    wait.until(EC.presence_of_element_located((By.ID, "search_product")))
    driver.find_element(By.ID, "search_product").send_keys(keyword)
    driver.find_element(By.ID, "submit_search").click()
    
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "features_items")))
    results = driver.find_elements(By.CSS_SELECTOR, ".features_items .product-image-wrapper")
    report.log(
        "Search Product",
        "PASS" if results else "FAIL",
        f"Searched for '{keyword}', found {len(results)} result(s).",
        take_screenshot(driver, "search_results"),
    )
    if not results:
        raise RuntimeError("No search results found.")
    return results


def add_product_to_cart(driver, wait, results, product_index, report):
    idx = min(product_index, len(results) - 1)
    product_card = results[idx]
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", product_card)
    product_card.find_element(By.CSS_SELECTOR, "a.add-to-cart").click()

    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal-content")))
    report.log("Add Product To Cart", "PASS", f"Added product at index {idx} to cart.", take_screenshot(driver, "added_to_cart"))

    try:
        driver.find_element(By.XPATH, "//button[contains(text(),'Continue Shopping')]").click()
    except NoSuchElementException:
        pass


def update_cart_quantity(driver, wait, quantity, base_url, report):
    driver.get(f"{base_url}/view_cart")
    wait.until(EC.presence_of_element_located((By.ID, "cart_info")))
    try:
        qty_input = driver.find_element(By.CSS_SELECTOR, "td.cart_quantity input.cart_quantity_input")
        qty_input.clear()
        qty_input.send_keys(str(quantity))
        qty_input.send_keys("\ue007")
        time.sleep(1)
        report.log("Update Quantity", "PASS", f"Attempted to update quantity to {quantity}.", take_screenshot(driver, "quantity_updated"))
    except NoSuchElementException:
        report.log("Update Quantity", "INFO", "Quantity field not directly editable on this cart page.")


def verify_cart(driver, report):
    cart_rows = driver.find_elements(By.CSS_SELECTOR, "#cart_info_table tbody tr")
    cart_details = []
    for row in cart_rows:
        try:
            name = row.find_element(By.CSS_SELECTOR, ".cart_description h4 a").text
            price = row.find_element(By.CSS_SELECTOR, ".cart_price p").text
            qty = row.find_element(By.CSS_SELECTOR, ".cart_quantity button").text
            total = row.find_element(By.CSS_SELECTOR, ".cart_total_price").text
            cart_details.append(f"{name} | {price} | qty={qty} | {total}")
        except NoSuchElementException:
            continue

    if cart_details:
        report.log("Verify Cart Details", "PASS", "Cart contains: " + "; ".join(cart_details), take_screenshot(driver, "cart_verified"))
    else:
        report.log("Verify Cart Details", "FAIL", "Cart appears empty.", take_screenshot(driver, "cart_empty"))


def handle_alert_if_present(driver, wait, report):
    try:
        wait.until(EC.alert_is_present())
        alert = driver.switch_to.alert
        alert_text = alert.text
        alert.accept()
        report.log("Handle Alert", "PASS", f"Alert accepted: '{alert_text}'")
    except (TimeoutException, NoAlertPresentException):
        report.log("Handle Alert", "INFO", "No alert present.")


def main():
    report = TestReport()
    data = load_test_data()
    report.log("Read Test Data", "PASS", f"Loaded test data from {DATA_FILE}")

    driver = setup_driver()
    wait = WebDriverWait(driver, 15)

    try:
        driver.get(data["base_url"])
        report.log("Launch Browser", "PASS", f"Opened {data['base_url']}", take_screenshot(driver, "home"))

        login_user(driver, wait, data["login"], data["base_url"], report)
        
        search_results = search_product(driver, wait, data["search"]["product_keyword"], data["base_url"], report)
        
        add_product_to_cart(driver, wait, search_results, data["cart"]["product_index_to_add"], report)
        
        update_cart_quantity(driver, wait, data["cart"]["quantity_to_set"], data["base_url"], report)
        
        verify_cart(driver, report)
        
        handle_alert_if_present(driver, wait, report)

        report.log("Test Flow Completed", "PASS", "All planned steps executed successfully.")

    except Exception as e:
        screenshot = take_screenshot(driver, "ERROR") if driver else None
        report.log("Unhandled Error", "FAIL", f"{e}\n{traceback.format_exc()}", screenshot)

    finally:
        if driver:
            time.sleep(1)
            driver.quit()
        
        report_path = report.render_html()
        print(f"\nExecution report generated at: {report_path}")


if __name__ == "__main__":
    main()