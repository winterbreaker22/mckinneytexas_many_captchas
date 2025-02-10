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


async def extract_request_key(page):
    try:
        js_code = """
        let requestKeys = [];
        let bodyContent = document.body.innerHTML;

        // Regex to capture 'requestKey' in the format requestKey: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
        let regex = /requestKey\\s*[:=]\\s*'(\\w{32})'/g;

        // Find all matches in the body content
        let matches;
        while ((matches = regex.exec(bodyContent)) !== null) {
            requestKeys.push(matches[1]);
        }

        // Now search inline JavaScript code inside <script> tags
        let scriptTags = document.getElementsByTagName('script');

        for (let script of scriptTags) {
            if (script.innerHTML) {
                let scriptMatches;
                while ((scriptMatches = regex.exec(script.innerHTML)) !== null) {
                    requestKeys.push(scriptMatches[1]);
                }
            }
        }

        // Ensure unique keys
        requestKeys = [...new Set(requestKeys)];

        // Return all found requestKeys
        requestKeys;
        """

        request_keys = await page.evaluate(js_code)

        if not request_keys:
            print("No requestKeys found.")
            return None

        print(f"All found requestKeys: {request_keys}")

        url = page.url
        temp_key = url.split("/")[-1]  

        filtered_keys = [key for key in request_keys if key != temp_key]

        if filtered_keys:
            print(f"Filtered requestKeys (excluding temp_key): {filtered_keys}")
        else:
            print("No valid requestKeys found after filtering.")

        return filtered_keys 

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def bypass_hcaptcha(api_key, site_url, site_key):
    try:
        payload = {
            "key": api_key,
            "method": "recaptcha",
            "sitekey": site_key,
            "pageurl": site_url,
            "json": 1
        }
        response = requests.post("http://2captcha.com/in.php", data=payload)
        result = response.json()
        print ("result: ", result)

        if result["status"] != 1:
            raise Exception(f"Error sending captcha to 2Captcha: {result['request']}")

        captcha_id = result["request"]
        print(f"Captcha ID: {captcha_id}")

        for _ in range(30): 
            time.sleep(5)  
            res = requests.get(f"http://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}&json=1")
            result = res.json()

            if result["status"] == 1:
                print(f"Solved captcha token: {result['request']}")
                return result["request"]  
            elif result["request"] != "CAPCHA_NOT_READY":
                raise Exception(f"Error solving captcha: {result['request']}")

        raise Exception("Failed to get captcha solution in time.")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise e
    

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
                site_keys = await extract_request_key(home_page)
                print ("sitekey: ", site_keys[0])
                print("page url: ", page_url)
                token = bypass_hcaptcha(API_KEY, page_url, site_keys[0])
            
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