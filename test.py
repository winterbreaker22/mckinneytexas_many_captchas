import asyncio
import requests
import time
from playwright.async_api import async_playwright
from twocaptcha import TwoCaptcha

API_KEY = 'bb8ef87d36b4959711ed4d1c0ebcd930'
solver = TwoCaptcha(API_KEY)

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
    login_url = f'https://www.referenceusa.com/Static/TermsAndConditions/True/855773dd-5695-4062-bae4-752955cfb3d6/https%5E3a%5E2f%5E2fwww.referenceusa.com%5E2f/ValidReferringUrlChallengeRequired'
    page_url = 'https://shop.garena.my/app/100067/idlogin?next=/app/100067/buy/0'

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context()

        page = await context.new_page()
        await page.goto(login_url)

        await page.wait_for_selector('iframe')

        captcha_id = get_mt_captcha_token(site_key, page_url)
        if captcha_id:
            print(f'CAPTCHA ID: {captcha_id}')
            solution = get_captcha_solution(captcha_id)
            if solution:
                print(f'Solved CAPTCHA: {solution}')

                # Inject the MTCaptcha token into the form and submit 
                iframe_element = await page.wait_for_selector('iframe') 
                frame = await iframe_element.content_frame()
                await frame.wait_for_load_state('networkidle')
                await frame.evaluate(f'token => window.captchaCallback("{solution}")', solution)
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
        

        await page.click('input[type="submit"]')
        await page.wait_for_selector('#form')
        await page.click('text="115 Diamond"')
        await page.wait_for_selector('text="Wallet"')
        await page.click('text="Wallet"')
        await page.click('#pc_div_669')
        await page.wait_for_selector('#sign-in-email')
        await page.fill('#sign-in-email', 'sandeshbc911@gmail.com')
        await page.fill('#signInPassword', '66Fh@tX4npFLAjZ')
        await page.click('#signin-email-submit-button')
        await page.wait_for_selector('input[name="security_key"]')
        await page.fill('input[name="security_key"]')
        await page.click('input[type="submit"]')
        await page.wait_for_selector('text="Back to merchant"')
        await page.click('text="Back to merchant"')
        await page.wait_for_selector('text="Congratulations!"')
        print ('Congratulations!')

        await browser.close()

asyncio.run(main())