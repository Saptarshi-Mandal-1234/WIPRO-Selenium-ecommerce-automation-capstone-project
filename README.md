# Capstone Assignment 1 — E-Commerce Web Automation (Selenium + Python)

Automates a purchase-style flow on https://automationexercise.com/ and produces
an HTML execution report with screenshots.

## What it does (maps to the 10 requirements)

| # | Requirement                  | Where in code |
|---|-------------------------------|----------------|
| 1 | Launch browser                | `webdriver.Chrome(...)` in `main()` |
| 2 | Login to application          | `/login` page, `data-qa` selectors |
| 3 | Search product                | `#search_product` + `#submit_search` |
| 4 | Add product to cart           | `a.add-to-cart` on a product card |
| 5 | Update quantity               | cart quantity input on `/view_cart` |
| 6 | Verify cart details           | reads `#cart_info_table` rows |
| 7 | Capture screenshots           | `take_screenshot()` after every major step |
| 8 | Read test data from JSON      | `data/test_data.json` via `load_test_data()` |
| 9 | Handle popups/alerts          | `handle_alert_if_present()`, `dismiss_consent_popup_if_present()` |
| 10| Generate execution report     | `TestReport` class → `reports/execution_report.html` |

## Setup

```bash
pip install -r requirements.txt
```

You need **Google Chrome** installed on your machine. `webdriver-manager`
downloads the matching ChromeDriver automatically the first time you run it —
no manual driver setup needed.

## Configure test data

Edit `data/test_data.json`:

```json
{
  "login": {
    "email": "your_registered_email@example.com",
    "password": "your_password"
  },
  "search": { "product_keyword": "Top" },
  "cart": { "product_index_to_add": 0, "quantity_to_set": 3 }
}
```

> Note: automationexercise.com requires a real registered account for login
> to fully succeed. If the credentials aren't valid, the script **does not
> crash** — it logs the login step as SKIP and continues the rest of the
> flow as a guest (search → add to cart → verify cart still works without
> login on this site). Sign up at `/signup` first if you want a true login
> pass.

## Run

```bash
python ecommerce_automation.py
```

A Chrome window will open and run through the flow automatically. When it
finishes:

- Screenshots are saved in `screenshots/`
- The execution report is at `reports/execution_report.html` — open it in
  any browser to see a pass/fail/info table with a screenshot link per step

To run without a visible browser window, uncomment this line in
`ecommerce_automation.py`:

```python
# options.add_argument("--headless=new")
```

## Notes / things you may want to tweak

- `product_index_to_add` picks which product from the search results to add
  (0 = first result).
- The cart-quantity field on this particular demo site is not always
  editable after an item is added (its quantity is usually locked in at
  add-to-cart time). The script tries to update it and logs an `INFO`
  status instead of failing if the field isn't editable — this is expected
  site behavior, not a bug.
- All exceptions are caught so the script always finishes and always writes
  a report, even if a step fails.
