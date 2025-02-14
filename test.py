import asyncio
import requests
import re
import os
import sys
import subprocess
from playwright.async_api import async_playwright
from playwright.async_api import Page
from twocaptcha import TwoCaptcha

API_KEY = '22baccc6f0d5aa915d61d378dc899c30'
solver = TwoCaptcha(API_KEY)
print ("solver: ", solver)
card_number = '29882001815412'
PAGE_NUMBER_FILE = "PN"

def ensure_playwright_browsers():
    try:
        subprocess.run(["playwright", "install", "--with-deps"], check=True, shell=True)
    except Exception as e:
        print(f"Error installing Playwright: {e}")

def save_page_number(page_number):
    with open(PAGE_NUMBER_FILE, "w") as file:
        file.write(str(page_number))

def load_page_number():
    try:
        with open(PAGE_NUMBER_FILE, "r") as file:
            return int(file.read().strip())
    except (FileNotFoundError, ValueError):
        return 1

async def safe_click(page: Page, selector, max_retries=3, wait_time=3):
    for attempt in range(max_retries):
        try:
            await page.wait_for_selector(selector, timeout=10000)
            await page.click(selector)
            return  
        except TimeoutError:
            print(f"Attempt {attempt+1}: Element {selector} not found. Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
    print(f"Failed to click {selector} after {max_retries} attempts.")

def send_captcha_request(api_key: str, sitekey: str, site_url: str):
    captcha_request_payload = {
        "key": api_key,  
        "method": "hcaptcha", 
        "sitekey": sitekey,  
        "pageurl": site_url, 
        "json": 1  
    }
    response = requests.post("http://2captcha.com/in.php", data=captcha_request_payload)
    return response.json()

def get_captcha_solution(api_key: str, captcha_id: str):
    solution_payload = {
        "key": api_key,
        "action": "get",
        "id": captcha_id,
        "json": 1
    }
    response = requests.get("http://2captcha.com/res.php", params=solution_payload)
    return response.json()

async def extract_and_solve_hcaptcha(page: Page, api_key: str):
    try:
        await page.wait_for_load_state("networkidle")
        
        iframe_elements = await page.query_selector_all("iframe[src*='hcaptcha.com']")
        sitekey = None

        for iframe in iframe_elements:
            iframe_src = await iframe.get_attribute("src")
            if iframe_src:
                match = re.search(r"sitekey=([a-f0-9\-]{36})", iframe_src)
                if match:
                    sitekey = match.group(1)
                    print(f"Found hCaptcha sitekey: {sitekey}")
                    break

        if not sitekey:
            print("Sitekey not found.")
            return None

        site_url = page.url

        captcha_request_result = await asyncio.to_thread(send_captcha_request, api_key, sitekey, site_url)

        if captcha_request_result.get("status") != 1:
            print(f"Error sending captcha to 2Captcha: {captcha_request_result}")
            return None

        captcha_id = captcha_request_result.get("request")
        print(f"Captcha submitted. ID: {captcha_id}")

        while True:
            solution_result = await asyncio.to_thread(get_captcha_solution, api_key, captcha_id)

            if solution_result.get("status") == 1:
                captcha_solution = solution_result.get("request")
                print(f"Captcha solved: {captcha_solution}")
                return captcha_solution
            elif solution_result.get("request") == "CAPCHA_NOT_READY":
                await asyncio.sleep(2) 
            else:
                print(f"Error solving captcha: {solution_result}")
                return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

async def main():
    page_number = load_page_number()
    login_url = f'https://www.mckinneytexas.org/116/Library'

    while page_number < 732431:
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=False, slow_mo=500)
            context = await browser.new_context()

            start_page = await context.new_page()
            await start_page.goto(login_url)

            await start_page.wait_for_selector("text='Research & Learn'")

            async with context.expect_page() as resource_list_page_info:
                await start_page.click("text='Research & Learn'")  
            resource_list_page = await resource_list_page_info.value
            await resource_list_page.wait_for_load_state()
            await resource_list_page.wait_for_selector("#main-content")

            await resource_list_page.click("#main-content .col-xs-12 > .row > .col-xs-4:nth-of-type(3) a img")

            await resource_list_page.wait_for_selector("text='Open Resource'")

            async with context.expect_page() as home_page_info:
                await resource_list_page.click("text='Open Resource'")
            home_page = await home_page_info.value
            await home_page.wait_for_load_state()
            await home_page.wait_for_selector("#chkAgree")
            await safe_click(home_page, "#chkAgree", max_retries=3, wait_time=3)
            await safe_click(home_page, ".action-agree", max_retries=3, wait_time=3)
            await home_page.wait_for_selector("#matchcode")
            await home_page.fill("#matchcode", card_number)
            await home_page.click("#logOn .buttons .originButton > span > span")

            await asyncio.sleep(1)
            await home_page.mouse.click(150, 150)

            await home_page.wait_for_selector("li#UsBusiness > h5")
            await home_page.click("li#UsBusiness > h5")
            
            await home_page.wait_for_selector("text='Advanced Search'")
            await home_page.click("text='Advanced Search'")

            await asyncio.sleep(3)
            checkbox_selector = "#VerifiedOnly"  
            if not home_page.is_checked(checkbox_selector):
                home_page.check(checkbox_selector)
            await safe_click(home_page, "a.greenMedium", max_retries=3, wait_time=3)

            await home_page.wait_for_selector("#searchResults .menuPagerBar .pager .page")
            await home_page.click("#searchResults .menuPagerBar .pager .page")
            await home_page.fill("#searchResults .menuPagerBar .pager input[type='text']", str(page_number))
            await home_page.keyboard.press("Enter")

            for i in range(10):
                captcha_exist = await home_page.locator("#hcaptcha").count()
                print (f"captcha count: {captcha_exist}")
                if captcha_exist > 0:
                    print("Captcha!!!")
                    token = await extract_and_solve_hcaptcha(home_page, API_KEY)
                    print(f"token: {token}")
                    
                    await home_page.evaluate(f"onCaptchaSubmit('{token}');")
                    await asyncio.sleep(3)

                await home_page.wait_for_selector("#searchResultsHeader")
                result_exist = await home_page.locator("#searchResultsHeader").count()
                if result_exist > 0:
                    await home_page.click("#searchResultsHeader #checkboxCol")
                    await home_page.click("#searchResults .menuPagerBar .pager .next")
                    await asyncio.sleep(2)

            await home_page.click('#searchResults .menuPagerBar a.download')
            await home_page.wait_for_selector("#detailDetail")
            await home_page.click("#detailDetail")

            if getattr(sys, 'frozen', False):  # Running as an EXE
                base_directory = os.path.dirname(sys.executable)
            else:  # Running as a Python script
                base_directory = os.path.dirname(os.path.abspath(__file__))

            download_directory = os.path.join(base_directory, "downloads")
            os.makedirs(download_directory, exist_ok=True)  
            async with home_page.expect_download() as download_info:
                await home_page.click("text='Download Records'")
            await asyncio.sleep(5)

            download = await download_info.value
            new_filename = f"{str(page_number + 9)}.csv"  
            os.makedirs(download_directory, exist_ok=True)
            file_path = os.path.join(download_directory, new_filename)
            await download.save_as(file_path)

            print(f"{new_filename} file downloaded and saved as: {file_path}")

            await browser.close()
        page_number = page_number + 10
        save_page_number(page_number)

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"
ensure_playwright_browsers()
asyncio.run(main())