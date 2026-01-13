import json
import urllib.request
import urllib.parse
import sys
import os

def get_input(prompt):
    print(prompt, end=': ', flush=True)
    return sys.stdin.readline().strip()

def main():
    print("--- Strava Refresh Token Setup ---")
    print("This script will help you exchange your Authorization Code for a Refresh Token.")
    
    # 1. Client ID
    while True:
        client_id_input = get_input("Enter your Client ID (should be a number, e.g., 12345)")
        if client_id_input.isdigit():
            client_id = client_id_input
            break
        print("Error: Client ID must be an integer.")

    # 2. Client Secret
    client_secret = get_input("Enter your Client Secret")

    # 3. Authorization Code
    print("\nIf you haven't gotten the Authorization Code yet, visit this URL in your browser:")
    print(f"http://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=activity:read_all")
    print("\nAfter authorizing, copy the 'code' parameter from the redirected URL (http://localhost/exchange_token?state=&code=...)")
    
    code = get_input("\nEnter the Authorization Code")

    # Exchange for token
    url = "https://www.strava.com/oauth/token"
    data = urllib.parse.urlencode({
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code'
    }).encode('utf-8')

    print("\nExchanging code for token...")
    try:
        req = urllib.request.Request(url, data=data, method='POST')
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        refresh_token = result.get('refresh_token')
        print("\nSUCCESS!")
        print("-" * 20)
        print(f"Refresh Token: {refresh_token}")
        print("-" * 20)
        
        # Save to .env
        env_content = f"""STRAVA_CLIENT_ID={client_id}
STRAVA_CLIENT_SECRET={client_secret}
STRAVA_REFRESH_TOKEN={refresh_token}
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("Credentials saved to .env file.")
        print("You can now run 'python backup.py' to back up your activities.")
        
    except urllib.error.HTTPError as e:
        print(f"\nError: {e}")
        try:
            error_body = e.read().decode('utf-8')
            print(f"Details: {error_body}")
        except:
            pass
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()

