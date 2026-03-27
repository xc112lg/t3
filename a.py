import json
from playwright.sync_api import sync_playwright

COOKIE_FILE = "cookie.txt"
URL = "https://shopee.ph/user/voucher-wallet"


# ================= LOAD COOKIES =================
def load_cookies():
    with open(COOKIE_FILE, "r") as f:
        raw = json.load(f)

    cookies = []
    for c in raw:
        cookies.append({
            "name": c["name"],
            "value": c["value"],
            "domain": ".shopee.ph",
            "path": "/"
        })

    return cookies


# ================= MAIN =================
def main():
    cookies = load_cookies()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        context.add_cookies(cookies)

        page = context.new_page()

        print("[+] Listening for voucher API...")

        found = False

        # ================= LISTENER =================
        def handle_response(response):
            nonlocal found

            try:
                if "voucher" not in response.url:
                    return

                data = response.json()

                if not isinstance(data, dict):
                    return

                vouchers = data.get("data", {}).get("user_voucher_list", [])

                if vouchers and not found:
                    found = True

                    print("\n🔥 FILTERED VOUCHERS (90–100%) 🔥\n")

                    matched = 0

                    for v in vouchers:
                        info = v.get("voucher", {})

                        # ✅ FIXED FIELD EXTRACTION
                        name = info.get("voucher_name") or v.get("voucher_name") or "N/A"
                        code = info.get("voucher_code") or v.get("voucher_code") or "N/A"
                        min_spend = info.get("min_spend") or v.get("min_spend") or "N/A"

                        discount_percent = v.get("discount_percentage", 0)

                        # ✅ FILTER 90–100%
                        if not discount_percent or not (90 <= discount_percent <= 100):
                            continue

                        matched += 1

                        print(f"Name      : {name}")
                        print(f"Code      : {code}")
                        print(f"Discount  : {discount_percent}%")
                        print(f"Min Spend : {min_spend}")
                        print("-" * 40)

                    print(f"\n[+] Found {matched} vouchers (90–100% only)\n")

            except:
                pass

        page.on("response", handle_response)

        print("[+] Opening voucher wallet...")
        page.goto(URL)

        page.wait_for_timeout(5000)

        # ================= SILENT SCROLL =================
        for _ in range(5):
            page.mouse.wheel(0, 5000)
            page.wait_for_timeout(2000)

        # ================= SILENT TAB CLICK =================
        tabs = page.locator("div[role='tab']").all()

        for tab in tabs:
            try:
                tab.click()
                page.wait_for_timeout(3000)
            except:
                pass

        page.wait_for_timeout(5000)

        if not found:
            print("\n[!] No vouchers detected")
            print("- Cookies expired")
            print("- No vouchers available")

        if "login" in page.url:
            print("[!] Redirected to login → invalid cookies")

        print("\n[+] Done.")

        input("\nPress ENTER to close...")
        browser.close()


if __name__ == "__main__":
    main()