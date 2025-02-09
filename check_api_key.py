import requests

API_KEY = '22baccc6f0d5aa915d61d378dc899c30'

def check_balance(api_key):
    url = f'http://2captcha.com/res.php?key={api_key}&action=getbalance'

    try:
        response = requests.get(url)
        if response.status_code == 200:
            balance = float(response.text)
            return balance
        else:
            print(f'Error: {response.status_code} - {response.text}')
            return None
    except requests.exceptions.RequestException as e:
        print(f'Request Error: {e}')
        return None

if __name__ == "__main__":
    balance = check_balance(API_KEY)
    if balance is not None:
        print(f'Current balance: ${balance}')