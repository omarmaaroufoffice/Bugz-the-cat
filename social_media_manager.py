import os
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
import mimetypes
import magic
import tweepy
import streamlit as st
import requests

from instagrapi import Client as InstagramClient
import facebook

class SocialMediaManager:
    def __init__(self):
        # Load credentials from environment variables
        self.instagram = self._init_instagram()
        self.twitter = self._init_twitter()
        self.facebook = self._init_facebook()

    def _init_instagram(self) -> Optional[InstagramClient]:
        """Initialize Instagram client."""
        try:
            client = InstagramClient()
            # Try to load existing session
            session_file = Path("instagram_session.json")
            if session_file.exists():
                try:
                    client.load_settings(str(session_file))
                    client.get_timeline_feed()  # Test if session is still valid
                    print("Successfully loaded Instagram session")
                    return client
                except Exception as e:
                    print(f"Error loading Instagram session: {e}")
                    session_file.unlink(missing_ok=True)  # Delete invalid session

            # If no valid session, try to login
            try:
                client.login(
                    os.getenv('INSTAGRAM_USERNAME'),
                    os.getenv('INSTAGRAM_PASSWORD')
                )
                # Save session for future use
                client.dump_settings(str(session_file))
                return client
            except Exception as e:
                st.error(f"""
                Instagram login failed: {e}
                Please check your credentials in the .env file.
                If you're using 2FA, you'll need to enter the code when prompted.
                """)
                return None
        except Exception as e:
            st.error(f"Error initializing Instagram client: {e}")
            return None

    def _init_twitter(self) -> Optional[tweepy.Client]:
        """Initialize Twitter client with v2 API."""
        try:
            # Initialize Twitter API v2 client
            client = tweepy.Client(
                consumer_key=os.getenv('TWITTER_API_KEY'),
                consumer_secret=os.getenv('TWITTER_API_SECRET'),
                access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
                access_token_secret=os.getenv('TWITTER_ACCESS_SECRET')
            )
            
            # Initialize API v1.1 for media upload
            auth = tweepy.OAuth1UserHandler(
                os.getenv('TWITTER_API_KEY'),
                os.getenv('TWITTER_API_SECRET'),
                os.getenv('TWITTER_ACCESS_TOKEN'),
                os.getenv('TWITTER_ACCESS_SECRET')
            )
            self.twitter_api = tweepy.API(auth)
            
            return client
        except Exception as e:
            print(f"Error initializing Twitter client: {e}")
            return None

    def _init_facebook(self) -> Optional[facebook.GraphAPI]:
        """Initialize Facebook client."""
        try:
            return facebook.GraphAPI(
                access_token=os.getenv('FACEBOOK_ACCESS_TOKEN'),
                version="3.1"
            )
        except Exception as e:
            print(f"Error initializing Facebook client: {e}")
            return None

    def post_to_instagram(self, media_path: str, caption: str, hashtags: str) -> bool:
        """Post media to Instagram."""
        try:
            if not self.instagram:
                raise Exception("Instagram client not initialized")

            path = Path(media_path)
            mime_type = magic.from_file(str(path), mime=True)
            
            # Combine caption and hashtags
            full_caption = f"{caption}\n.\n.\n.\n{hashtags}"

            if 'video' in mime_type:
                # Post video
                self.instagram.video_upload(
                    path=str(path),
                    caption=full_caption
                )
            else:
                # Post image
                self.instagram.photo_upload(
                    path=str(path),
                    caption=full_caption
                )
            return True
        except Exception as e:
            print(f"Error posting to Instagram: {e}")
            return False

    def post_to_twitter(self, media_path: str, caption: str, hashtags: str) -> bool:
        """Post media to Twitter using v2 API."""
        try:
            if not self.twitter or not self.twitter_api:
                raise Exception("Twitter client not initialized")

            # Twitter has a 280 character limit
            # Truncate hashtags if needed to fit caption
            total_length = len(caption) + len(hashtags) + 3  # 3 for spacing
            if total_length > 280:
                hashtags = ' '.join(hashtags.split()[:5])  # Use only first 5 hashtags

            # Upload media using v1.1 API
            path = Path(media_path)
            media_type = 'video' if path.suffix.lower() in ['.mp4', '.mov', '.avi'] else 'image'
            
            if media_type == 'video':
                media = self.twitter_api.media_upload(
                    filename=str(path),
                    media_category='tweet_video'
                )
            else:
                media = self.twitter_api.media_upload(filename=str(path))

            # Post tweet with media using v2 API
            self.twitter.create_tweet(
                text=f"{caption}\n{hashtags}",
                media_ids=[media.media_id]
            )
            return True
        except Exception as e:
            print(f"Error posting to Twitter: {e}")
            return False

    def post_to_facebook(self, media_path: str, caption: str, hashtags: str) -> bool:
        """Post media to Facebook."""
        try:
            if not self.facebook:
                raise Exception("Facebook client not initialized")

            path = Path(media_path)
            
            # Get page ID from environment variable
            page_id = os.getenv('FACEBOOK_PAGE_ID')
            
            # Prepare the post
            with open(path, 'rb') as media_file:
                self.facebook.put_photo(
                    image=media_file,
                    message=f"{caption}\n\n{hashtags}",
                    page_id=page_id
                )
            return True
        except Exception as e:
            print(f"Error posting to Facebook: {e}")
            return False

    def post_to_tiktok(self, media_path: str, caption: str, hashtags: str) -> bool:
        """Post video content to TikTok using the TikTok API."""
        try:
            # Check if the file is a video
            path = Path(media_path)
            if path.suffix.lower() not in ['.mp4', '.mov', '.avi']:
                st.error("Only video content can be posted to TikTok. Please upload a video file.")
                return False

            # Check if we have TikTok credentials
            access_token = os.getenv('TIKTOK_ACCESS_TOKEN')
            if not access_token:
                st.warning("""
                TikTok access token not found. Please follow these steps:
                1. Run the get_tiktok_token.py script
                2. Follow the authorization process
                3. Add the generated token to your .env file
                """)
                # Show manual posting instructions as fallback
                st.info("""
                For now, you can post manually:
                1. Open TikTok Studio: https://www.tiktok.com/upload
                2. Upload your video content there directly
                3. Copy-paste the caption and hashtags below
                """)
                formatted_post = f"{caption}\n\n{hashtags}"
                st.text_area("Copy this caption for TikTok:", formatted_post)
                return False

            # Initialize TikTok API client
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            # Step 1: Get video upload URL
            upload_url = "https://open.tiktokapis.com/v2/post/publish/video/init/"
            upload_response = requests.post(
                upload_url,
                headers=headers,
                json={'source_info': {'source': 'FILE_UPLOAD'}}
            )

            if upload_response.status_code != 200:
                st.error(f"Error getting upload URL: {upload_response.text}")
                return False

            upload_info = upload_response.json()
            upload_url = upload_info['data']['upload_url']

            # Step 2: Upload video file
            with open(path, 'rb') as video_file:
                files = {'video': ('video.mp4', video_file, 'video/mp4')}
                upload_result = requests.post(upload_url, files=files)

            if upload_result.status_code != 200:
                st.error(f"Error uploading video: {upload_result.text}")
                return False

            # Step 3: Publish the video
            publish_url = "https://open.tiktokapis.com/v2/post/publish/video/publish/"
            publish_data = {
                'video_id': upload_info['data']['video_id'],
                'post_info': {
                    'title': caption,
                    'privacy_level': 'PUBLIC',
                    'disable_comment': False,
                    'disable_duet': False,
                    'disable_stitch': False,
                    'video_cover_timestamp_ms': 0
                }
            }

            publish_response = requests.post(
                publish_url,
                headers=headers,
                json=publish_data
            )

            if publish_response.status_code != 200:
                st.error(f"Error publishing video: {publish_response.text}")
                return False

            st.success("Video successfully posted to TikTok!")
            return True

        except Exception as e:
            st.error(f"Error posting to TikTok: {e}")
            return False

    def post_to_all_platforms(self, media_path: str, caption: str, hashtags: str) -> Dict[str, bool]:
        """Post media to all available platforms."""
        results = {
            'instagram': self.post_to_instagram(media_path, caption, hashtags),
            'twitter': self.post_to_twitter(media_path, caption, hashtags),
            'facebook': self.post_to_facebook(media_path, caption, hashtags),
            'tiktok': self.post_to_tiktok(media_path, caption, hashtags) if Path(media_path).suffix.lower() in ['.mp4', '.mov'] else False
        }
        return results

    def schedule_post(self, media_path: str, caption: str, hashtags: str, 
                     platforms: List[str], schedule_time: datetime) -> None:
        """Schedule a post for specified platforms at a given time."""
        # This is a placeholder for scheduling functionality
        # You would typically use a task queue like Celery or a cron job for this
        pass 