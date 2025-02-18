import os
import json
from datetime import datetime, timedelta
import pytz
from pathlib import Path
import google.generativeai as genai
from PIL import Image
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import re
import sqlite3
from social_media_manager import SocialMediaManager

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the Gemini model DO NOT CHANGE THIS
#MODEL: gemini-2.0-flash
model = genai.GenerativeModel('gemini-2.0-flash')

class CatContentAnalyzer:
    def __init__(self):
        self.categories = [
            "Cuteness Factor",
            "Action/Entertainment Value",
            "Uniqueness",
            "Image/Video Quality",
            "Trend Alignment"
        ]
        self.analyzed_content = []
        self.instagram_hashtags = [
            "#catsofinstagram", "#catstagram", "#cats", "#cat", "#kitty",
            "#meow", "#catlife", "#instacat", "#catlovers", "#catlover",
            "#catoftheday", "#catlove", "#kitten", "#pets", "#catworld"
        ]
        self.social_media = SocialMediaManager()
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database and create necessary tables."""
        self.conn = sqlite3.connect('cat_content.db')
        self.cursor = self.conn.cursor()

        # Create tables if they don't exist
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS content_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT,
            original_filename TEXT,
            media_type TEXT,
            total_score INTEGER,
            caption TEXT,
            hashtags TEXT,
            engagement_tips TEXT,
            key_strengths TEXT,
            improvement_suggestions TEXT,
            timestamp DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS category_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER,
            category TEXT,
            score INTEGER,
            FOREIGN KEY (analysis_id) REFERENCES content_analysis (id)
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS posting_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER,
            platform TEXT,
            status TEXT,
            posted_at DATETIME,
            FOREIGN KEY (analysis_id) REFERENCES content_analysis (id)
        )
        ''')

        self.conn.commit()

    def _save_to_database(self, analysis):
        """Save analysis results to SQLite database."""
        try:
            # Insert main analysis data
            self.cursor.execute('''
            INSERT INTO content_analysis (
                file_path, original_filename, media_type, total_score,
                caption, hashtags, engagement_tips, key_strengths,
                improvement_suggestions, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                analysis['file_path'],
                analysis.get('original_filename', os.path.basename(analysis['file_path'])),
                analysis['media_type'],
                analysis['total_score'],
                analysis['caption'],
                analysis['hashtags'],
                analysis['engagement_tips'],
                analysis['key_strengths'],
                analysis['improvement_suggestions'],
                analysis['timestamp']
            ))
            
            analysis_id = self.cursor.lastrowid

            # Insert category scores
            for category, score in analysis['scores'].items():
                self.cursor.execute('''
                INSERT INTO category_scores (analysis_id, category, score)
                VALUES (?, ?, ?)
                ''', (analysis_id, category, score))

            self.conn.commit()
            return analysis_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error saving to database: {e}")
            raise

    def _load_from_database(self, analysis_id):
        """Load analysis results from SQLite database."""
        try:
            # Get main analysis data
            self.cursor.execute('''
            SELECT * FROM content_analysis WHERE id = ?
            ''', (analysis_id,))
            analysis_data = self.cursor.fetchone()

            if not analysis_data:
                return None

            # Get category scores
            self.cursor.execute('''
            SELECT category, score FROM category_scores WHERE analysis_id = ?
            ''', (analysis_id,))
            scores = {row[0]: row[1] for row in self.cursor.fetchall()}

            # Reconstruct analysis dictionary
            analysis = {
                'file_path': analysis_data[1],
                'original_filename': analysis_data[2],
                'media_type': analysis_data[3],
                'total_score': analysis_data[4],
                'caption': analysis_data[5],
                'hashtags': analysis_data[6],
                'engagement_tips': analysis_data[7],
                'key_strengths': analysis_data[8],
                'improvement_suggestions': analysis_data[9],
                'timestamp': analysis_data[10],
                'scores': scores
            }

            return analysis
        except Exception as e:
            print(f"Error loading from database: {e}")
            return None

    def record_post(self, analysis_id, platform, status):
        """Record posting history in the database."""
        try:
            self.cursor.execute('''
            INSERT INTO posting_history (analysis_id, platform, status, posted_at)
            VALUES (?, ?, ?, ?)
            ''', (analysis_id, platform, status, datetime.now(pytz.UTC)))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Error recording post history: {e}")

    def get_posting_history(self):
        """Get posting history from the database."""
        try:
            self.cursor.execute('''
            SELECT ca.original_filename, ph.platform, ph.status, ph.posted_at
            FROM posting_history ph
            JOIN content_analysis ca ON ph.analysis_id = ca.id
            ORDER BY ph.posted_at DESC
            ''')
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error getting posting history: {e}")
            return []

    def analyze_media(self, media_path):
        """Analyze a single media file (image or video)."""
        file_path = Path(media_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Media file not found: {media_path}")

        # Determine if it's an image or video
        is_video = file_path.suffix.lower() in ['.mp4', '.mov', '.avi']
        
        # Generate Instagram-specific analysis prompt
        prompt = f"""
        Analyze this {'video' if is_video else 'image'} of a cat for Instagram virality potential, focusing on Instagram's specific engagement patterns and algorithm preferences.

        Score each category from 1-10 and provide detailed reasoning with Instagram-specific insights:
        1. Cuteness Factor (Instagram users' emotional response potential)
        2. Action/Entertainment Value (Instagram engagement and save/share potential)
        3. Uniqueness (Standing out in Instagram cat content)
        4. Image/Video Quality (Instagram's visual quality standards)
        5. Trend Alignment (Current Instagram cat content trends)
        
        For Instagram optimization, provide:
        1. Engaging Caption:
           - Write a caption that encourages interaction
           - Include a call-to-action
           - Use emojis strategically
           - Keep it under 125 characters for optimal display
        
        2. Hashtag Strategy:
           - Mix popular and niche cat hashtags (max 15)
           - Include trending hashtags if relevant
           - Order from most to least relevant
        
        3. Posting Recommendations:
           - Best time to post for maximum reach
           - Ideal day of the week
           - Instagram-specific content tips
        
        4. Engagement Optimization:
           - Suggestions for Instagram Stories/Reels potential
           - Ideas for carousel posts if applicable
           - Poll/Quiz suggestions for Stories
        
        5. Key Strengths for Instagram:
           - What makes this content save-worthy
           - Share potential
           - Viral trigger elements
        
        6. Instagram-Specific Improvements:
           - How to optimize for the Instagram algorithm
           - Format/crop suggestions
           - Enhancement ideas for better engagement
        """

        try:
            if is_video:
                # For videos, use the first frame
                import cv2
                cap = cv2.VideoCapture(str(file_path))
                ret, frame = cap.read()
                if ret:
                    # Convert BGR to RGB
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # Convert to PIL Image
                    image = Image.fromarray(frame)
                    cap.release()
                else:
                    raise Exception("Could not read video file")
            else:
                # For images, use PIL
                image = Image.open(file_path)

            # Generate content using the model
            response = model.generate_content([prompt, image])
            response.resolve()

            # Parse the response and extract scores
            analysis = self._parse_analysis(response.text)
            analysis['file_path'] = str(file_path)
            analysis['media_type'] = 'video' if is_video else 'image'
            
            # Save to database
            analysis_id = self._save_to_database(analysis)
            analysis['id'] = analysis_id
            
            self.analyzed_content.append(analysis)
            return analysis
            
        except Exception as e:
            print(f"Error analyzing media: {e}")
            raise

    def _parse_analysis(self, response_text):
        """Parse the Gemini response into structured data."""
        try:
            # Extract scores using simple parsing
            scores = {}
            for category in self.categories:
                # Look for numbers after category name
                category_index = response_text.find(category)
                if category_index != -1:
                    score_text = response_text[category_index:category_index+100]
                    # Extract first number found (1-10)
                    import re
                    score_match = re.search(r'(\d+)(?:/10)?', score_text)
                    if score_match:
                        scores[category] = int(score_match.group(1))
                    else:
                        scores[category] = 5  # Default score if not found

            # Extract other components with Instagram-specific parsing
            caption_start = response_text.lower().find("caption")
            hashtags_start = response_text.find("#")
            engagement_start = response_text.lower().find("engagement optimization")
            strengths_start = response_text.lower().find("key strengths")
            improvements_start = response_text.lower().find("improvements")
            
            # Enhanced analysis dictionary with Instagram-specific fields
            analysis = {
                'scores': scores,
                'total_score': sum(scores.values()),
                'caption': self._clean_text(response_text[caption_start:hashtags_start].strip() if caption_start != -1 else ""),
                'hashtags': self._extract_hashtags(response_text[hashtags_start:] if hashtags_start != -1 else ""),
                'engagement_tips': self._clean_text(response_text[engagement_start:strengths_start].strip() if engagement_start != -1 else ""),
                'key_strengths': self._clean_text(response_text[strengths_start:improvements_start].strip() if strengths_start != -1 else ""),
                'improvement_suggestions': self._clean_text(response_text[improvements_start:].strip() if improvements_start != -1 else ""),
                'timestamp': datetime.now(pytz.UTC),
            }
            
            return analysis
        except Exception as e:
            print(f"Error parsing analysis: {e}")
            return None

    def _clean_text(self, text):
        """Clean and format text for better readability."""
        if not text:
            return ""
        # Remove multiple spaces and newlines
        cleaned = ' '.join(text.split())
        # Remove section headers
        cleaned = re.sub(r'^(Caption:|Hashtags:|Engagement Optimization:|Key Strengths:|Improvements:)\s*', '', cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    def _extract_hashtags(self, text):
        """Extract and validate Instagram hashtags."""
        if not text:
            return []
        # Find all hashtags in the text
        hashtags = re.findall(r'#\w+', text)
        # Ensure we don't exceed Instagram's limit
        hashtags = hashtags[:30]  # Instagram's maximum hashtag limit
        # Add some popular cat hashtags if we have space
        if len(hashtags) < 30:
            remaining = 30 - len(hashtags)
            hashtags.extend(self.instagram_hashtags[:remaining])
        return ' '.join(hashtags)

    def generate_posting_schedule(self):
        """Generate an optimal posting schedule for analyzed content."""
        if not self.analyzed_content:
            return []

        # Sort content by total score
        sorted_content = sorted(
            self.analyzed_content,
            key=lambda x: x['total_score'],
            reverse=True
        )

        # Define optimal posting times (Eastern Time)
        optimal_times = [
            (11, 0),  # 11:00 AM
            (14, 0),  # 2:00 PM
            (19, 0),  # 7:00 PM
            (21, 0),  # 9:00 PM
        ]

        et_tz = pytz.timezone('US/Eastern')
        now = datetime.now(et_tz)
        
        schedule = []
        for i, content in enumerate(sorted_content):
            # Calculate next optimal posting time
            post_time = now.replace(
                hour=optimal_times[i % len(optimal_times)][0],
                minute=optimal_times[i % len(optimal_times)][1],
                second=0,
                microsecond=0
            )
            
            # If time is in the past, move to next day
            if post_time <= now:
                post_time += timedelta(days=1)
            
            # Add days to spread out content
            post_time += timedelta(days=(i // len(optimal_times)))

            schedule.append({
                'file_path': content['file_path'],
                'post_time': post_time,
                'total_score': content['total_score'],
                'caption': content['caption'],
                'hashtags': content['hashtags'],
                'engagement_tips': content.get('engagement_tips', ''),
                'key_strengths': content.get('key_strengths', ''),
                'improvement_suggestions': content.get('improvement_suggestions', '')
            })

        return schedule

    def post_to_social_media(self, content, platforms=None):
        """Post content to specified social media platforms."""
        if platforms is None:
            platforms = ['instagram', 'twitter', 'facebook', 'tiktok']

        results = {}
        for platform in platforms:
            success = False
            if platform == 'instagram':
                success = self.social_media.post_to_instagram(
                    content['file_path'],
                    content['caption'],
                    content['hashtags']
                )
            elif platform == 'twitter':
                success = self.social_media.post_to_twitter(
                    content['file_path'],
                    content['caption'],
                    content['hashtags']
                )
            elif platform == 'facebook':
                success = self.social_media.post_to_facebook(
                    content['file_path'],
                    content['caption'],
                    content['hashtags']
                )
            elif platform == 'tiktok' and content['media_type'] == 'video':
                success = self.social_media.post_to_tiktok(
                    content['file_path'],
                    content['caption'],
                    content['hashtags']
                )
            
            results[platform] = success
            # Record posting attempt in database
            if 'id' in content:
                self.record_post(content['id'], platform, 'success' if success else 'failed')

        return results

    def export_analysis(self, output_path='content_analysis.json'):
        """Export analysis results to JSON."""
        with open(output_path, 'w') as f:
            json.dump({
                'analyzed_content': self.analyzed_content,
                'generated_at': datetime.now(pytz.UTC).isoformat()
            }, f, indent=2, default=str)

    def __del__(self):
        """Close database connection when object is destroyed."""
        if hasattr(self, 'conn'):
            self.conn.close()

def main():
    analyzer = CatContentAnalyzer()
    
    print("🐱 Cat Content Analyzer for Instagram")
    print("=====================================")
    
    # Get media files from user
    media_dir = input("Enter the directory path containing your cat media files: ")
    media_files = [
        f for f in Path(media_dir).glob("*")
        if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.mp4', '.mov', '.avi']
    ]
    
    if not media_files:
        print("No supported media files found in the specified directory.")
        return
    
    print(f"\nFound {len(media_files)} media files. Starting analysis...")
    
    # Analyze each file
    for file_path in media_files:
        print(f"\nAnalyzing: {file_path.name}")
        try:
            analysis = analyzer.analyze_media(str(file_path))
            print(f"Total Score: {analysis['total_score']}/50")
        except Exception as e:
            print(f"Error analyzing {file_path.name}: {e}")
    
    # Generate and display posting schedule
    schedule = analyzer.generate_posting_schedule()
    
    print("\n📅 Recommended Posting Schedule")
    print("==============================")
    
    # Ask user about social media platforms
    print("\nAvailable platforms: instagram, twitter, facebook, tiktok")
    platforms = input("Enter platforms to post to (comma-separated, or 'all'): ").strip()
    platforms = ['instagram', 'twitter', 'facebook', 'tiktok'] if platforms.lower() == 'all' else [p.strip() for p in platforms.split(',')]
    
    for post in schedule:
        print(f"\nPost Time: {post['post_time'].strftime('%Y-%m-%d %I:%M %p ET')}")
        print(f"File: {Path(post['file_path']).name}")
        print(f"Score: {post['total_score']}/50")
        print(f"Caption: {post['caption']}")
        print(f"Hashtags: {post['hashtags']}")
        print("\nEngagement Tips:", post['engagement_tips'])
        print("Key Strengths:", post['key_strengths'])
        print("Improvement Suggestions:", post['improvement_suggestions'])
        
        # Ask for confirmation before posting
        should_post = input(f"\nPost this content now? (y/n): ").strip().lower()
        if should_post == 'y':
            results = analyzer.post_to_social_media(post, platforms)
            print("\nPosting Results:")
            for platform, success in results.items():
                print(f"{platform}: {'Success' if success else 'Failed'}")
    
    # Export analysis
    analyzer.export_analysis()
    print("\n✅ Analysis exported to content_analysis.json")

if __name__ == "__main__":
    main() 