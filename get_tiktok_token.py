import streamlit as st
import requests
from urllib.parse import urlencode, quote_plus
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# TikTok API credentials
CLIENT_KEY = os.getenv('TIKTOK_CLIENT_KEY')
CLIENT_SECRET = os.getenv('TIKTOK_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8501/'  # Added trailing slash

def main():
    st.title("TikTok Access Token Generator")
    
    # Display current configuration
    st.write("Current Configuration:")
    st.code(f"""
    Client Key: {CLIENT_KEY}
    Redirect URI: {REDIRECT_URI}
    """)
    
    # Step 1: Generate authorization URL with properly encoded parameters
    auth_params = {
        'client_key': CLIENT_KEY,
        'response_type': 'code',
        'scope': 'user.info.basic,video.list,video.upload',
        'redirect_uri': REDIRECT_URI,
        'state': 'your_state'
    }
    
    # Properly encode the URL parameters
    encoded_params = "&".join([f"{k}={quote_plus(str(v))}" for k, v in auth_params.items()])
    auth_url = f"https://www.tiktok.com/auth/authorize/?{encoded_params}"
    
    st.write("Step 1: Verify your TikTok Developer Account setup:")
    st.markdown("""
    1. Go to [TikTok for Developers](https://developers.tiktok.com/)
    2. Ensure your app is configured with:
        - Correct Client Key
        - Exact Redirect URI: `http://localhost:8501/`
        - Required Scopes: `user.info.basic`, `video.list`, `video.upload`
    """)
    
    st.write("\nStep 2: Click the link below to authorize your TikTok account:")
    st.markdown(f"[Authorize TikTok]({auth_url})")
    
    # Step 3: Handle the authorization code
    st.write("\nStep 3: After authorization, you'll be redirected back. Copy the 'code' parameter from the URL.")
    auth_code = st.text_input("Enter the authorization code:")
    
    if auth_code:
        # Exchange authorization code for access token
        token_url = "https://open.tiktokapis.com/v2/oauth/token/"
        token_data = {
            'client_key': CLIENT_KEY,
            'client_secret': CLIENT_SECRET,
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI
        }
        
        try:
            response = requests.post(token_url, data=token_data)
            if response.status_code == 200:
                token_info = response.json()
                st.success("Access token obtained successfully!")
                
                # Display the access token
                st.write("\nYour access token (add this to your .env file):")
                st.code(f"TIKTOK_ACCESS_TOKEN={token_info['access_token']}")
                
                # Display token expiration
                st.write(f"\nToken expires in: {token_info['expires_in']} seconds")
                st.write("Make sure to refresh your token before it expires.")
                
                # Save to .env file option
                if st.button("Save to .env file"):
                    try:
                        with open('.env', 'r') as f:
                            env_content = f.read()
                        
                        # Replace or add TIKTOK_ACCESS_TOKEN
                        if 'TIKTOK_ACCESS_TOKEN=' in env_content:
                            env_lines = env_content.split('\n')
                            new_lines = []
                            for line in env_lines:
                                if line.startswith('TIKTOK_ACCESS_TOKEN='):
                                    new_lines.append(f"TIKTOK_ACCESS_TOKEN={token_info['access_token']}")
                                else:
                                    new_lines.append(line)
                            env_content = '\n'.join(new_lines)
                        else:
                            env_content += f"\nTIKTOK_ACCESS_TOKEN={token_info['access_token']}"
                        
                        with open('.env', 'w') as f:
                            f.write(env_content)
                        
                        st.success("Access token saved to .env file!")
                    except Exception as e:
                        st.error(f"Error saving to .env file: {e}")
            else:
                st.error(f"Error obtaining access token: {response.text}")
        except Exception as e:
            st.error(f"Error making token request: {e}")

if __name__ == "__main__":
    main() 