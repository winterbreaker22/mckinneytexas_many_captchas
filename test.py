import asyncio
import requests
import time
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright.async_api import Page
from twocaptcha import TwoCaptcha
from urllib.parse import urlparse

API_KEY = '22baccc6f0d5aa915d61d378dc899c30'
solver = TwoCaptcha(API_KEY)
print ("solver: ", solver)
card_number = '29882001815412'

async def extract_request_key(page: Page):
    """
    Captures JavaScript files from an existing Playwright page instance and extracts their content.
    Args:
        page (Page): A Playwright Page instance.

    Returns:
        dict: A dictionary where keys are JavaScript file URLs and values are their contents.
    """
    try:
        # Store JavaScript files in a list
        js_files = []

        # Intercept and capture JavaScript requests
        async def handle_request(request):
            if request.resource_type == "script":
                js_files.append(request.url)

        # Attach the request handler to the page
        page.on("request", handle_request)

        # Wait for the page to load (adjust time if necessary)
        await page.wait_for_load_state("networkidle")

        # Fetch the JavaScript content
        js_content = {}
        for js_url in js_files:
            try:
                response = await page.request.get(js_url)
                js_content[js_url] = await response.text()
            except Exception as e:
                print(f"Failed to fetch {js_url}: {e}")

        # Detach the request handler after extraction
        page.off("request", handle_request)

        return js_content
    except Exception as e:
        print(f"An error occurred: {e}")
        return {}

def get_captcha_token(site_key, page_url):    
    attempts = 0
    max_attempts = 20

    while attempts < max_attempts:
        result = solver.hcaptcha(sitekey=site_key, url=page_url)
        print ("result: ", result)
        if not result['captchaId']:
            print ('Captcha unresolved')
            attempts += 1
        else: 
            captcha_id = result['captchaId']
            return captcha_id


def get_captcha_solution(captcha_id):
    url = f'http://2captcha.com/res.php?key={API_KEY}&action=get&id={captcha_id}&json=1'
    max_attempts = 20
    attempts = 0

    while attempts < max_attempts:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1:
                    return result.get('request')
                elif result.get('request') == 'CAPCHA_NOT_READY':
                    print('Captcha not ready, sleeping for 5 seconds...')
                    time.sleep(5)
                    attempts += 1
                else:
                    print(f'Error solving captcha: {result["request"]}')
                    return None
            else:
                print(f'Error checking captcha status: {response.status_code} - {response.text}')
                return None
        except requests.exceptions.RequestException as e:
            print(f'Request Error: {e}')
            return None

    print('Max attempts reached. Captcha solving failed.')
    return None


async def main():
    login_url = f'https://www.mckinneytexas.org/116/Library'

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context()

        start_page = await context.new_page()
        await start_page.goto(login_url)

        await start_page.wait_for_selector("text='Research & Learn'")
        await start_page.click("text='Research & Learn'")

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
        await home_page.click("#chkAgree")
        await home_page.click(".action-agree")
        await home_page.wait_for_selector("#matchcode")
        await home_page.fill("#matchcode", card_number)
        await home_page.click("#logOn .buttons .originButton > span > span")

        await asyncio.sleep(1)
        await home_page.mouse.click(150, 150)

        await home_page.wait_for_selector("text='U.S. Businesses'")
        await home_page.click("text='U.S. Businesses'")
        
        await home_page.wait_for_selector("text='Advanced Search'")
        await home_page.click("text='Advanced Search'")

        await home_page.wait_for_selector("a.greenMedium")
        await home_page.click("a.greenMedium")

        await home_page.wait_for_selector(".pager .page")
        await home_page.click(".pager .page")
        await home_page.fill(".pager input[type='text']", "101")
        await home_page.keyboard.press("Enter")

        for i in range(10):
            captcha_exist = await home_page.locator("#hcaptcha").count()
            if captcha_exist > 0:
                print("Captcha!!!")
                page_url = home_page.url
                site_key = extract_request_key(home_page)
                print ("sitekey: ", site_key)
                print("page url: ", page_url)
                captcha_id = get_captcha_token(site_key, page_url)
                if captcha_id:
                    print(f'CAPTCHA ID: {captcha_id}')
                    solution = get_captcha_solution(captcha_id)
                    if solution:
                        print(f'Solved CAPTCHA: {solution}')

                        await home_page.fill("#g-recaptcha-response-1cze57gr6ofv", solution)
                        print('Captcha solution injected successfully.')

                        await home_page.wait_for_load_state('networkidle')
                        print ('arrived!!!')
                        await home_page.wait_for_timeout(1000)
                        await home_page.click('input[type="submit"]')
                        print ('done??')
                        await home_page.wait_for_timeout(7000)
                        print (home_page.url)
                        
                    else:
                        print('Failed to solve CAPTCHA')
                        return
                else:
                    print('Failed to get CAPTCHA ID')
                    return
            
            result_exist = await home_page.locator("#searchResultsHeader").count()
            if result_exist > 0:
                await home_page.click("#searchResultsHeader #checkboxCol")
                await home_page.click(".pager .next")
                await asyncio.sleep(2)

        await home_page.click('#searchResults .menuPagerBar a.download')
        await home_page.wait_for_selector("#detailDetail")
        await home_page.click("#detailDetail")
        await home_page.click("text='Download Records'")

        print ('Congratulations!')

        await browser.close()

asyncio.run(main())