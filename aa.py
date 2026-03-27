import json
import os
from playwright.sync_api import sync_playwright

COOKIE_DIR = "cookies"
URL = "https://shopee.ph/user/voucher-wallet"


# ================= APPLY COOKIES =================
def apply_cookies(context, cookie_file):
    with open(cookie_file, "r") as f:
        raw = json.load(f)

    cookies = []
    for c in raw:
        cookies.append({
            "name": c["name"],
            "value": c["value"],
            "domain": c.get("domain", ".shopee.ph"),
            "path": c.get("path", "/"),
            "httpOnly": c.get("httpOnly", False),
            "secure": c.get("secure", True)
        })

    context.add_cookies(cookies)


# ================= CHECK ACCOUNT =================
def check_account(p, cookie_file):
    account_name = os.path.splitext(os.path.basename(cookie_file))[0]
    results = []

    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    # 🔥 Step 1: open Shopee first
    page.goto("https://shopee.ph")
    page.wait_for_timeout(3000)

    # 🔥 Step 2: apply cookies
    apply_cookies(context, cookie_file)

    # 🔥 Step 3: reload to activate session
    page.reload()
    page.wait_for_timeout(5000)

    # 🔍 login check
    if "login" in page.url:
        print(f"[!] {account_name} → NOT LOGGED IN")
        browser.close()
        return account_name, []

    print(f"[+] {account_name} → Logged in")

    # ================= LISTENER =================
    def handle_response(response):
        try:
            if "voucher" not in response.url:
                return

            data = response.json()
            vouchers = data.get("data", {}).get("user_voucher_list", [])

            for v in vouchers:
                discount_percent = v.get("discount_percentage", 0)

                if not discount_percent or not (90 <= discount_percent <= 100):
                    continue

                info = v.get("voucher", {})

                name = info.get("voucher_name") or v.get("voucher_name") or "N/A"
                code = info.get("voucher_code") or v.get("voucher_code") or "N/A"
                min_spend = info.get("min_spend") or v.get("min_spend") or "N/A"

                results.append({
                    "name": name,
                    "code": code,
                    "discount": discount_percent,
                    "min_spend": min_spend
                })

        except:
            pass

    page.on("response", handle_response)

    # 🔥 open voucher page
    page.goto(URL)
    page.wait_for_timeout(6000)

    # trigger API
    page.mouse.wheel(0, 4000)
    page.wait_for_timeout(3000)

    browser.close()

    return account_name, results


# ================= MAIN =================
def main():
    cookie_files = [
        os.path.join(COOKIE_DIR, f)
        for f in os.listdir(COOKIE_DIR)
        if f.endswith(".json")
    ]

    if not cookie_files:
        print("[!] No cookie files found")
        return

    print(f"[+] Checking {len(cookie_files)} accounts...\n")

    all_results = []

    with sync_playwright() as p:
        for cookie in cookie_files:
            acc, res = check_account(p, cookie)
            all_results.append((acc, res))

    # ================= OUTPUT =================
    print("\n===== RESULT =====\n")

    found_any = False

    for acc, vouchers in all_results:
        if not vouchers:
            continue

        found_any = True

        print(f"🔥 {acc}")
        print("-" * 40)

        for v in vouchers:
            print(f"Name      : {v['name']}")
            print(f"Code      : {v['code']}")
            print(f"Discount  : {v['discount']}%")
            print(f"Min Spend : {v['min_spend']}")
            print("-" * 30)

        print()

    if not found_any:
        print("❌ No 90–100% vouchers found in any account")

    print("\n[+] Done.")


if __name__ == "__main__":
    main()