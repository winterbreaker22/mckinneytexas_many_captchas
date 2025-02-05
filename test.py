import asyncio
import requests
import time
from playwright.async_api import async_playwright
from twocaptcha import TwoCaptcha

API_KEY = 'bb8ef87d36b4959711ed4d1c0ebcd930'
solver = TwoCaptcha(API_KEY)
card_number = '29882001815412'

def get_mt_captcha_token(site_key, page_url):    

    attempts = 0
    max_attempts = 20

    while attempts < max_attempts:
        result = solver.hcaptcha(sitekey=site_key, url=page_url)
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
    site_key = '2942779……c24-acf7-29d4b80d2106'
    login_url = f'https://www.mckinneytexas.org/116/Library'
    page_url = 'https://shop.garena.my/app/100067/idlogin?next=/app/100067/buy/0'

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context()

        page = await context.new_page()
        await page.goto(login_url)

        await page.wait_for_selector("text='Research & Learn'")
        await page.click("text='Research & Learn'")

        await page.wait_for_selector("#main-content")
        await page.click("#main-content .col-xs-12 > .row > .col-xs-4:nth-of-type(3) a img")

        await page.wait_for_selector("text='Open Resource'")
        await page.click("text='Open Resource'")

        await page.check("#chkAgree") 
        await page.click(".action-agree")

        await page.wait_for_selector("#matchcode")
        await page.fill("#matchcode", card_number)
        await page.click("#Log On")

        await asyncio.sleep(1)
        await page.mouse.click(150, 150)
        await page.click("text='U.S. Businesses'")
        
        await page.wait_for_selector("text='Advanced Search'")
        await page.click("text='Advanced Search'")

        await page.wait_for_selector("a.greenMedium")
        await page.click("a.greenMedium")

        await page.wait_for_selector(".pager .page")
        await page.click(".pager .page")
        await page.fill(".pager input[type='text']", "91")
        await page.keyboard.press("Enter")

        captcha_exist = await page.locator("#captchaValidation").count()
        if captcha_exist > 0:
            captcha_id = get_mt_captcha_token(site_key, page.url)
            if captcha_id:
                print(f'CAPTCHA ID: {captcha_id}')
                solution = get_captcha_solution(captcha_id)
                if solution:
                    print(f'Solved CAPTCHA: {solution}')

                    # Inject the MTCaptcha token into the form and submit 
                    await page.fill("#g-recaptcha-response-1cze57gr6ofv", solution)
                    print('Captcha solution injected successfully.')

                    # Wait for navigation after solving CAPTCHA
                    await page.wait_for_load_state('networkidle')
                    print ('arrived!!!')
                    await page.wait_for_timeout(1000)
                    await page.click('input[type="submit"]')
                    print ('done??')
                    await page.wait_for_timeout(7000)
                    print (page.url)

                    if page.url == 'https://shop.garena.my/app/100067/buy/0':
                        print('Login Success!')                         
                else:
                    print('Failed to solve CAPTCHA')
                    return
            else:
                print('Failed to get CAPTCHA ID')
                return
        
        result_exist = await page.locator("#searchResultsHeader").count()
        if result_exist:
            await page.click("#searchResultsHeader #checkboxCol")
            await page.click(".pager .next")

        await page.click('#searchResults .menuPagerBar a.download')
        
        print ('Congratulations!')

        await browser.close()

asyncio.run(main())