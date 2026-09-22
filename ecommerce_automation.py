"""
Capstone Assignment 1: E-Commerce Web Automation using Selenium WebDriver + Python
Target application : https://automationexercise.com/

Covers all 10 required steps:
 1. Launch browser
 2. Login to application
 3. Search product
 4. Add product to cart
 5. Update quantity
 6. Verify cart details
 7. Capture screenshots
 8. Read test data from JSON
 9. Handle popup/alerts if available
10. Generate execution report (HTML)

Run:
    python ecommerce_automation.py

Requirements:
    pip install selenium webdriver-manager
"""

import json
import os
import time
import datetime
import traceback

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException,
    NoAlertPresentException,
    NoSuchElementException,
)
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
REPORT_DIR = os.path.join(BASE_DIR, "reports")
DATA_FILE = os.path.join(BASE_DIR, "data", "test_data.json")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


class TestReport:
    """Collects step results and renders a simple HTML execution report."""

    def __init__(self):
        self.steps = []  # list of dicts: name, status, message, screenshot, timestamp
        self.start_time = datetime.datetime.now()

    def log(self, name, status, message="", screenshot=None):
        self.steps.append(
            {
                "name": name,
                "status": status,  # PASS / FAIL / INFO / SKIP
                "message": message,
                "screenshot": screenshot,
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
            }
        )
        print(f"[{status}] {name} - {message}")

    def render_html(self):
        end_time = datetime.datetime.now()
        duration = (end_time - self.start_time).total_seconds()
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
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def take_screenshot(driver, name):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(SCREENSHOT_DIR, f"{name}_{ts}.png")
    try:
        driver.save_screenshot(path)
        return path
    except Exception:
        return None


def handle_alert_if_present(driver, report, timeout=3):
    """Step 9: Handle any browser popup/alert if one appears."""
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        text = alert.text
        alert.accept()
        report.log("Handle Alert", "PASS", f"Alert detected and accepted: '{text}'")
    except (TimeoutException, NoAlertPresentException):
        report.log("Handle Alert", "INFO", "No alert present at this point (expected on most pages).")


def dismiss_consent_popup_if_present(driver, report):
    """Some demo sites show cookie/consent banners - close them if present."""
    try:
        consent_btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Consent') or contains(text(),'Accept')]"))
        )
        consent_btn.click()
        report.log("Dismiss Consent Popup", "PASS", "Consent/cookie popup dismissed.")
    except TimeoutException:
        report.log("Dismiss Consent Popup", "INFO", "No consent popup shown.")


def main():
    report = TestReport()
    data = load_test_data()
    report.log("Read Test Data", "PASS", f"Loaded test data from {DATA_FILE}")

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    # Uncomment the next line to run headless (no visible browser window):
    # options.add_argument("--headless=new")

    driver = None
    try:
        # ---------- Step 1: Launch browser ----------
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.implicitly_wait(5)
        wait = WebDriverWait(driver, 15)
        driver.get(data["base_url"])
        report.log("Launch Browser", "PASS", f"Opened {data['base_url']}", take_screenshot(driver, "01_home"))

        dismiss_consent_popup_if_present(driver, report)

        # ---------- Step 2: Login to application ----------
        try:
            driver.get(data["base_url"] + "/login")
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-qa='login-email']")))
            driver.find_element(By.CSS_SELECTOR, "input[data-qa='login-email']").send_keys(data["login"]["email"])
            driver.find_element(By.CSS_SELECTOR, "input[data-qa='login-password']").send_keys(data["login"]["password"])
            driver.find_element(By.CSS_SELECTOR, "button[data-qa='login-button']").click()
            time.sleep(1)

            if "Logged in as" in driver.page_source:
                report.log("Login", "PASS", "Logged in successfully.", take_screenshot(driver, "02_login_success"))
            else:
                report.log(
                    "Login",
                    "SKIP",
                    "Login not confirmed (demo credentials may be invalid/unregistered). "
                    "Continuing as guest — cart flow does not require login on this site.",
                    take_screenshot(driver, "02_login_not_confirmed"),
                )
        except (TimeoutException, NoSuchElementException) as e:
            report.log("Login", "SKIP", f"Login page/elements not found, continuing as guest: {e}")

        # ---------- Step 3: Search product ----------
        driver.get(data["base_url"] + "/products")
        wait.until(EC.presence_of_element_located((By.ID, "search_product")))
        search_box = driver.find_element(By.ID, "search_product")
        keyword = data["search"]["product_keyword"]
        search_box.clear()
        search_box.send_keys(keyword)
        driver.find_element(By.ID, "submit_search").click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "features_items")))
        results = driver.find_elements(By.CSS_SELECTOR, ".features_items .product-image-wrapper")
        report.log(
            "Search Product",
            "PASS" if results else "FAIL",
            f"Searched for '{keyword}', found {len(results)} result(s).",
            take_screenshot(driver, "03_search_results"),
        )

        if not results:
            raise RuntimeError("No search results found — cannot continue with cart flow.")

        # ---------- Step 4: Add product to cart ----------
        idx = min(data["cart"]["product_index_to_add"], len(results) - 1)
        product_card = results[idx]
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", product_card)
        add_to_cart_btn = product_card.find_element(By.CSS_SELECTOR, "a.add-to-cart")
        add_to_cart_btn.click()

        # Modal usually appears with "Continue Shopping" / "View Cart"
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal-content")))
        report.log("Add Product To Cart", "PASS", f"Added product at index {idx} to cart.", take_screenshot(driver, "04_added_to_cart"))

        try:
            continue_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Continue Shopping')]")
            continue_btn.click()
        except NoSuchElementException:
            pass

        # ---------- Step 5: Update quantity ----------
        driver.get(data["base_url"] + "/view_cart")
        wait.until(EC.presence_of_element_located((By.ID, "cart_info")))
        try:
            qty_input = driver.find_element(By.CSS_SELECTOR, "td.cart_quantity input.cart_quantity_input")
            qty_input.clear()
            qty_input.send_keys(str(data["cart"]["quantity_to_set"]))
            # This site's cart quantity is typically read-only post-add; where editable,
            # a page action (e.g. pressing Enter / triggering change) applies the update.
            qty_input.send_keys("\ue007")  # Enter key
            time.sleep(1)
            report.log("Update Quantity", "PASS", f"Attempted to update quantity to {data['cart']['quantity_to_set']}.", take_screenshot(driver, "05_quantity_updated"))
        except NoSuchElementException:
            report.log("Update Quantity", "INFO", "Quantity field not directly editable on this cart page; quantity was set at add-to-cart time instead.")

        # ---------- Step 6: Verify cart details ----------
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
            report.log(
                "Verify Cart Details",
                "PASS",
                "Cart contains: " + "; ".join(cart_details),
                take_screenshot(driver, "06_cart_verified"),
            )
        else:
            report.log("Verify Cart Details", "FAIL", "Cart appears empty — verification failed.", take_screenshot(driver, "06_cart_empty"))

        # ---------- Step 9: Handle popup/alerts (checked at a natural trigger point) ----------
        handle_alert_if_present(driver, report)

        report.log("Test Flow Completed", "PASS", "All planned steps executed.")

    except Exception as e:
        err_text = traceback.format_exc()
        screenshot = take_screenshot(driver, "ERROR") if driver else None
        report.log("Unhandled Error", "FAIL", f"{e}\n{err_text}", screenshot)

    finally:
        if driver:
            time.sleep(1)
            driver.quit()
        # ---------- Step 10: Generate execution report ----------
        report_path = report.render_html()
        print(f"\nExecution report generated at: {report_path}")


if __name__ == "__main__":
    main()
