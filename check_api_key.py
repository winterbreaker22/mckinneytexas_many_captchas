import requests

API_KEY = 'bb8ef87d36b4959711ed4d1c0ebcd930'

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