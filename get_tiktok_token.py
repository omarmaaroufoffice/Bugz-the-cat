import streamlit as st
import requests
from urllib.parse import urlencode, quote_plus, parse_qs, urlparse
import os
from dotenv import load_dotenv
from pathlib import Path
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# TikTok API credentials
CLIENT_KEY = os.getenv('TIKTOK_CLIENT_KEY')
CLIENT_SECRET = os.getenv('TIKTOK_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8501/'

def update_env_file(token_info):
    """Update the .env file with the new token."""
    env_path = Path('.env')
    if not env_path.exists():
        return False
    
    try:
        # Read current .env content
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Update or add token
        token_line = f"TIKTOK_ACCESS_TOKEN={token_info['access_token']}\n"
        token_found = False
        
        for i, line in enumerate(lines):
            if line.startswith('TIKTOK_ACCESS_TOKEN='):
                lines[i] = token_line
                token_found = True
                break
        
        if not token_found:
            lines.append('\n' + token_line)
        
        # Write back to .env
        with open(env_path, 'w') as f:
            f.writelines(lines)
        
        return True
    except Exception as e:
        st.error(f"Error updating .env file: {e}")
        return False

def main():
    st.title("🎵 TikTok Access Token Generator")
    
    if not CLIENT_KEY or not CLIENT_SECRET:
        st.error("""
        Missing TikTok API credentials!
        Please add TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET to your .env file.
        You can get these from the TikTok Developer Portal.
        """)
        return
    
    # Display setup instructions
    with st.expander("📋 Setup Instructions", expanded=True):
        st.markdown("""
        ### Before You Begin
        1. Go to [TikTok for Developers](https://developers.tiktok.com/)
        2. Create or select your app
        3. Configure your app with these settings:
            - Redirect URI: `http://localhost:8501/`
            - Required Scopes: 
                - `user.info.basic`
                - `video.list`
                - `video.upload`
        
        ### Getting Your Access Token
        1. Click the "Start Authorization" button below
        2. Log in to TikTok if prompted
        3. Authorize the app
        4. Copy the entire redirect URL
        5. Paste it in the input field below
        """)
    
    # Step 1: Generate authorization URL
    auth_params = {
        'client_key': CLIENT_KEY,
        'response_type': 'code',
        'scope': 'user.info.basic,video.list,video.upload',
        'redirect_uri': REDIRECT_URI,
        'state': 'tiktok_auth'
    }
    
    encoded_params = urlencode(auth_params, quote_via=quote_plus)
    auth_url = f"https://www.tiktok.com/auth/authorize/?{encoded_params}"
    
    if st.button("🚀 Start Authorization"):
        st.markdown(f"[Click here to authorize with TikTok]({auth_url})")
    
    # Step 2: Handle the redirect
    st.subheader("Enter Redirect URL")
    redirect_url = st.text_input(
        "After authorizing, paste the complete URL you were redirected to:",
        help="The URL should start with 'http://localhost:8501/' and contain a 'code' parameter"
    )
    
    if redirect_url:
        try:
            # Parse the URL to get the authorization code
            parsed_url = urlparse(redirect_url)
            params = parse_qs(parsed_url.query)
            
            if 'code' not in params:
                st.error("No authorization code found in the URL. Please make sure you copied the entire URL.")
                return
            
            auth_code = params['code'][0]
            
            # Exchange authorization code for access token
            token_url = "https://open.tiktokapis.com/v2/oauth/token/"
            token_data = {
                'client_key': CLIENT_KEY,
                'client_secret': CLIENT_SECRET,
                'code': auth_code,
                'grant_type': 'authorization_code',
                'redirect_uri': REDIRECT_URI
            }
            
            with st.spinner("Getting access token..."):
                response = requests.post(token_url, data=token_data)
                
                if response.status_code == 200:
                    token_info = response.json()
                    
                    # Update .env file
                    if update_env_file(token_info):
                        st.success("✅ Access token successfully saved to .env file!")
                    else:
                        st.warning("""
                        Could not automatically update .env file.
                        Please manually add this line to your .env file:
                        """)
                        st.code(f"TIKTOK_ACCESS_TOKEN={token_info['access_token']}")
                    
                    # Display token information
                    st.info(f"""
                    Token Details:
                    - Expires in: {token_info['expires_in']} seconds
                    - Refresh token expires in: {token_info.get('refresh_expires_in', 'N/A')} seconds
                    
                    Make sure to refresh your token before it expires!
                    """)
                    
                    # Save token info to a file for reference
                    token_file = Path('tiktok_token_info.json')
                    token_info['generated_at'] = str(datetime.now())
                    with open(token_file, 'w') as f:
                        json.dump(token_info, f, indent=2)
                    
                else:
                    st.error(f"""
                    Error getting access token. 
                    Status code: {response.status_code}
                    Response: {response.text}
                    """)
        
        except Exception as e:
            st.error(f"Error processing authorization: {e}")

if __name__ == "__main__":
    main() 