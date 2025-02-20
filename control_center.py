import streamlit as st
import os
from pathlib import Path
import json
from datetime import datetime, timedelta, time
import pytz
from streamlit_option_menu import option_menu
import pandas as pd
from cat_content_analyzer import CatContentAnalyzer
from PIL import Image
import io
import sqlite3
from custom_components import (
    custom_menu_button,
    custom_scrollable_region,
    custom_header_button,
    add_accessibility_support,
    make_accessible
)

# Set page config with improved accessibility
st.set_page_config(
    page_title="Cat Content Control Center",
    page_icon="🐱",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/cat-content-analyzer',
        'Report a bug': "https://github.com/yourusername/cat-content-analyzer/issues",
        'About': """
        # Cat Content Control Center
        
        This app helps you analyze and manage your cat content for social media.
        Upload images or videos of cats, get AI-powered analysis, and schedule posts across platforms.
        """
    }
)

# Add global accessibility support
add_accessibility_support()

# Add skip link for keyboard navigation
st.markdown("""
    <a href="#main-content" class="skip-link">Skip to main content</a>
    <main id="main-content" role="main">
""", unsafe_allow_html=True)

# Custom CSS for modern design and better contrast
st.markdown("""
    <style>
    /* Main theme colors */
    :root {
        --primary-color: #2E3192;
        --secondary-color: #1E847F;
        --background-color: #E8F5E9;
        --text-color: #333333;
        --accent-color: #4CAF50;
        --success-color: #28A745;
        --warning-color: #FFC107;
        --error-color: #DC3545;
        --card-bg-color: #C8E6C9;
        --gradient-start: #2E7D32;
        --gradient-end: #43A047;
        --light-text: #F8FFF9;
    }

    /* Global styles */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: var(--primary-color);
        font-weight: 600;
        margin-bottom: 1rem;
        background: linear-gradient(120deg, var(--gradient-start), var(--gradient-end));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));
        color: var(--light-text);
        border-radius: 8px;
        padding: 0.75rem 1.25rem;
        font-weight: 600;
        font-size: 1rem;
        border: none;
        transition: all 0.3s ease;
        min-width: 120px;
        text-align: center;
        position: relative;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, var(--gradient-end), var(--gradient-start));
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }

    .stButton > button:focus {
        outline: 2px solid var(--primary-color);
        outline-offset: 2px;
    }

    .stButton > button:active {
        transform: translateY(1px);
    }

    /* Text inputs and text areas */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: var(--card-bg-color) !important;
        border: 2px solid var(--gradient-start);
        border-radius: 6px;
        padding: 0.5rem;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 1px var(--primary-color);
    }

    /* DataFrames */
    .stDataFrame {
        background: linear-gradient(135deg, var(--card-bg-color), #A5D6A7);
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(46, 125, 50, 0.2);
    }

    .dataframe {
        background-color: var(--card-bg-color) !important;
    }

    /* Metrics */
    .stMetric {
        background: linear-gradient(135deg, var(--card-bg-color), #A5D6A7);
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(46, 125, 50, 0.2);
    }

    .stMetric label {
        color: #1A1A1A !important;
    }

    .stMetric .metric-value {
        color: var(--gradient-start) !important;
        font-weight: 600;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));
        color: var(--light-text);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-weight: 500;
    }

    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, var(--card-bg-color), #A5D6A7);
        padding: 2rem 1rem;
        color: #1A1A1A;
    }

    /* Cards for content */
    .stCard, div[data-testid="stExpander"] {
        background: linear-gradient(135deg, var(--card-bg-color), #A5D6A7);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        border: 1px solid rgba(46, 125, 50, 0.2);
    }

    /* Success messages */
    .element-container .stAlert {
        background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));
        color: var(--light-text);
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }

    .element-container .stSuccess {
        background: linear-gradient(135deg, #28A745, #20C997);
        color: var(--light-text);
    }

    /* Warning messages */
    .element-container .stWarning {
        background: linear-gradient(135deg, #FFC107, #FF9800);
        color: #1A1A1A;
    }

    /* Error messages */
    .element-container .stError {
        background: linear-gradient(135deg, #DC3545, #C82333);
        color: var(--light-text);
    }

    /* Info messages */
    .element-container .stInfo {
        background: linear-gradient(135deg, #17A2B8, #138496);
        color: var(--light-text);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: var(--card-bg-color);
        gap: 2rem;
        border-bottom: 2px solid var(--gradient-start);
        padding: 0.5rem;
        border-radius: 8px 8px 0 0;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: var(--card-bg-color);
        padding: 1rem 2rem;
        color: var(--text-color);
        font-weight: 500;
        border-radius: 6px;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));
        color: var(--light-text) !important;
        border-radius: 6px;
    }

    /* Select boxes */
    .stSelectbox > div > div > select {
        background-color: var(--card-bg-color) !important;
        border: 2px solid var(--gradient-start);
        border-radius: 6px;
        padding: 0.5rem;
    }

    /* File uploader */
    .stFileUploader {
        background: linear-gradient(135deg, var(--card-bg-color), #A5D6A7);
        padding: 1rem;
        border-radius: 8px;
        border: 2px solid var(--gradient-start);
    }

    /* Progress bars */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--gradient-start), var(--gradient-end));
        color: var(--light-text);
    }

    /* Charts */
    .stChart {
        background: linear-gradient(135deg, var(--card-bg-color), #A5D6A7);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(46, 125, 50, 0.2);
    }

    /* Tables */
    .dataframe {
        background-color: var(--card-bg-color) !important;
    }

    /* Radio buttons and checkboxes */
    .stRadio > div,
    .stCheckbox > div {
        background-color: var(--card-bg-color);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid var(--gradient-start);
    }

    /* Links */
    a {
        color: var(--gradient-start);
        font-weight: 500;
    }
    a:hover {
        color: var(--gradient-end);
    }

    /* Text elements */
    .stMarkdown {
        color: #1A1A1A;
    }
    
    /* Sidebar text */
    .css-1d391kg {
        color: #1A1A1A;
    }

    /* Input labels */
    .stTextInput label, .stTextArea label, .stSelectbox label {
        color: #1A1A1A !important;
        font-weight: 500;
    }

    /* DataFrame text */
    .dataframe {
        color: #1A1A1A !important;
    }

    /* Main menu button */
    [data-testid="stMainMenu"] {
        background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));
        color: var(--light-text);
        padding: 0.5rem 1rem;
        border-radius: 8px;
        transition: all 0.3s ease;
        position: relative;
    }

    [data-testid="stMainMenu"]:hover {
        background: linear-gradient(135deg, var(--gradient-end), var(--gradient-start));
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    [data-testid="stMainMenu"] span {
        color: var(--light-text) !important;
        font-weight: 500;
    }

    /* Ensure proper ARIA support for menu button */
    [data-testid="stMainMenu"][aria-expanded="true"] {
        background: var(--gradient-end);
    }

    [data-testid="stMainMenu"][aria-haspopup="true"] {
        cursor: pointer;
    }

    /* Improve button visibility and contrast */
    .stButton > button {
        background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));
        color: var(--light-text);
        border-radius: 8px;
        padding: 0.75rem 1.25rem;
        font-weight: 600;
        font-size: 1rem;
        border: none;
        transition: all 0.3s ease;
        min-width: 120px;
        text-align: center;
        position: relative;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, var(--gradient-end), var(--gradient-start));
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }

    .stButton > button:focus {
        outline: 2px solid var(--primary-color);
        outline-offset: 2px;
    }

    .stButton > button:active {
        transform: translateY(1px);
    }

    /* Ensure proper contrast for running status */
    label.st-emotion-cache-klqnuk {
        color: #1A1A1A !important;
        font-weight: 500;
        background-color: #E8F5E9;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        border: 1px solid var(--gradient-start);
    }

    /* Fix main menu button accessibility */
    [data-testid="stMainMenu"] {
        visibility: hidden;
        position: absolute;
    }
    
    /* Custom accessible menu button */
    .custom-menu-button {
        position: fixed;
        top: 0.5rem;
        right: 0.5rem;
        z-index: 1000;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = CatContentAnalyzer()
if 'analyzed_content' not in st.session_state:
    st.session_state.analyzed_content = []
if 'pending_posts' not in st.session_state:
    st.session_state.pending_posts = []
if 'posted_content' not in st.session_state:
    st.session_state.posted_content = []

# Create temp directory if it doesn't exist
temp_dir = Path("temp")
if not temp_dir.exists():
    temp_dir.mkdir(parents=True, exist_ok=True)

def load_and_display_media(file_path):
    """Load and display media file."""
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            st.error(f"Media file not found: {file_path}")
            return
        
        if file_path.suffix.lower() in ['.mp4', '.mov', '.avi']:
            return st.video(str(file_path))
        else:
            # Open and verify the image
            try:
                # First try to open and validate the image
                with Image.open(file_path) as img:
                    # Verify the image
                    img.verify()
                
                # Reopen the image for processing (verify closes the file)
                img = Image.open(file_path)
                
                # Convert to RGB if necessary before any processing
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Get and validate image dimensions
                width, height = img.size
                if width <= 0 or height <= 0:
                    st.error(f"Invalid image dimensions: {width}x{height}")
                    return
                
                # Calculate new dimensions while preserving aspect ratio
                max_width = 800  # Maximum display width
                max_height = 1200  # Maximum display height
                
                # Calculate scale factors for both width and height
                width_scale = max_width / width if width > max_width else 1
                height_scale = max_height / height if height > max_height else 1
                
                # Use the smaller scale factor to ensure image fits within bounds
                scale = min(width_scale, height_scale)
                
                # Calculate new dimensions
                if scale < 1:  # Only resize if image is too large
                    new_width = max(1, int(width * scale))
                    new_height = max(1, int(height * scale))
                    
                    try:
                        # Resize image
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    except Exception as e:
                        st.warning(f"Error during resize, displaying original image: {str(e)}")
                
                # Display the image
                try:
                    return st.image(img, use_column_width=True)
                except Exception as e:
                    # If streamlit display fails, try converting to bytes
                    try:
                        import io
                        img_byte_arr = io.BytesIO()
                        img.save(img_byte_arr, format='JPEG')
                        img_byte_arr = img_byte_arr.getvalue()
                        return st.image(img_byte_arr, use_column_width=True)
                    except Exception as e2:
                        st.error(f"Failed to display image: {str(e2)}")
                        return
                        
            except Exception as e:
                st.error(f"Error processing image {file_path.name}: {str(e)}")
                # Try to display the original file as a last resort
                try:
                    return st.image(str(file_path), use_column_width=True)
                except:
                    st.error("Failed to display image in any format")
                    return
    except Exception as e:
        st.error(f"Error loading media: {str(e)}")
        return

def analyze_media(uploaded_files):
    """Analyze uploaded media files."""
    results = []
    
    # Connect to database
    conn = sqlite3.connect('cat_content.db')
    cursor = conn.cursor()
    
    for file in uploaded_files:
        # Save the file temporarily
        temp_path = Path("temp") / f"temp_{file.name}"
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Calculate file hash for duplicate checking
            file_content = file.getvalue()
            import hashlib
            file_hash = hashlib.md5(file_content).hexdigest()
            
            # Check if file was already analyzed using both filename and hash
            cursor.execute("""
                SELECT ca.*, cs.category, cs.score 
                FROM content_analysis ca
                LEFT JOIN category_scores cs ON ca.id = cs.analysis_id
                WHERE (ca.original_filename = ? OR ca.file_hash = ?)
                GROUP BY ca.id
            """, (file.name, file_hash))
            existing_analysis = cursor.fetchone()
            
            if existing_analysis:
                # Get the full analysis from database
                analysis_id = existing_analysis[0]
                cursor.execute("""
                    SELECT category, score 
                    FROM category_scores 
                    WHERE analysis_id = ?
                """, (analysis_id,))
                scores = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Reconstruct analysis dictionary
                analysis = {
                    'id': analysis_id,
                    'file_path': str(temp_path),
                    'original_filename': existing_analysis[2],
                    'media_type': existing_analysis[3],
                    'total_score': existing_analysis[4],
                    'caption': existing_analysis[5],
                    'hashtags': existing_analysis[6],
                    'engagement_tips': existing_analysis[7],
                    'key_strengths': existing_analysis[8],
                    'improvement_suggestions': existing_analysis[9],
                    'timestamp': existing_analysis[10],
                    'file_hash': existing_analysis[11] if len(existing_analysis) > 11 else file_hash,
                    'scores': scores
                }
                
                # Save the file for display
                with open(temp_path, "wb") as f:
                    f.write(file_content)
                
                st.info(f"Found existing analysis for {file.name} - Skipping reanalysis")
            else:
                # Save the file for new analysis
                with open(temp_path, "wb") as f:
                    f.write(file_content)
                
                # Analyze the file
                analysis = st.session_state.analyzer.analyze_media(str(temp_path))
                analysis['original_filename'] = file.name
                analysis['file_path'] = str(temp_path)
                analysis['file_hash'] = file_hash
                
                # Store the file hash in the database for future duplicate checking
                cursor.execute("""
                    UPDATE content_analysis 
                    SET file_hash = ? 
                    WHERE id = ?
                """, (file_hash, analysis.get('id')))
                conn.commit()
                
                st.success(f"New analysis completed for {file.name}")
            
            results.append(analysis)
            st.session_state.analyzed_content.append(analysis)
            
        except Exception as e:
            st.error(f"Error analyzing {file.name}: {e}")
            if temp_path.exists():
                temp_path.unlink()
    
    conn.close()
    return results

def display_analysis_results(analysis):
    """Display analysis results in a structured format with improved accessibility."""
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.markdown(f"### Media Info")
        load_and_display_media(analysis['file_path'])
        st.markdown(f"**File:** {analysis['original_filename']}")
        st.markdown(f"**Type:** {analysis['media_type']}")
    
    with col2:
        st.markdown("### Analysis Results")
        
        # Display scores in an accessible scrollable region
        scores_df = pd.DataFrame(
            analysis['scores'].items(),
            columns=['Category', 'Score']
        )
        st.markdown("**Category Scores:**")
        scores_html = scores_df.to_html(index=False, classes="styled-table")
        custom_scrollable_region(scores_html, max_height="200px", label="Category scores table", key=f"scores_{analysis['file_path']}")
        
        st.markdown(f"**Total Score:** {analysis['total_score']}/50")
        
        # Display generated content in accessible format
        st.markdown("**Generated Caption:**")
        caption = st.text_area("Caption", analysis['caption'], key=f"caption_{analysis['file_path']}", help="Generated caption for the media")
        
        st.markdown("**Hashtags:**")
        hashtags = st.text_area("Hashtags", analysis['hashtags'], key=f"hashtags_{analysis['file_path']}", help="Generated hashtags for the media")
        
        # Display tips in accessible expandable sections
        with st.expander("Engagement Tips"):
            custom_scrollable_region(analysis['engagement_tips'], max_height="150px", label="Engagement tips", key=f"tips_{analysis['file_path']}")
        
        with st.expander("Key Strengths"):
            custom_scrollable_region(analysis['key_strengths'], max_height="150px", label="Key strengths", key=f"strengths_{analysis['file_path']}")
        
        with st.expander("Improvement Suggestions"):
            custom_scrollable_region(analysis['improvement_suggestions'], max_height="150px", label="Improvement suggestions", key=f"improvements_{analysis['file_path']}")

def schedule_post(analysis):
    """Add post to pending schedule."""
    # Connect to database to check posting history
    conn = sqlite3.connect('cat_content.db')
    cursor = conn.cursor()
    
    # Check if this content was already posted
    if 'id' in analysis:
        cursor.execute("""
            SELECT platform, status, posted_at 
            FROM posting_history 
            WHERE analysis_id = ?
            ORDER BY posted_at DESC
        """, (analysis['id'],))
        posting_history = cursor.fetchall()
        
        if posting_history:
            st.info("Previous posting history:")
            history_df = pd.DataFrame(
                posting_history,
                columns=['Platform', 'Status', 'Posted At']
            )
            st.dataframe(history_df)
    
    platforms = st.multiselect(
        "Select platforms to post to:",
        ['instagram', 'twitter', 'facebook', 'tiktok'],
        key=f"platforms_{analysis['file_path']}"
    )
    
    # Split datetime input into date and time
    col1, col2 = st.columns(2)
    with col1:
        post_date = st.date_input(
            "Schedule date:",
            value=datetime.now(pytz.UTC).date(),
            key=f"date_{analysis['file_path']}"
        )
    with col2:
        post_time = st.time_input(
            "Schedule time:",
            value=datetime.now(pytz.UTC).time(),
            key=f"time_{analysis['file_path']}"
        )
    
    # Combine date and time into datetime
    post_datetime = datetime.combine(post_date, post_time)
    post_datetime = pytz.UTC.localize(post_datetime)
    
    if st.button("Schedule", key=f"schedule_{analysis['file_path']}"):
        scheduled_post = {
            'analysis': analysis,
            'platforms': platforms,
            'scheduled_time': post_datetime,
            'status': 'pending',
            'media_type': analysis['media_type']
        }
        st.session_state.pending_posts.append(scheduled_post)
        
        # Record scheduling in database
        if 'id' in analysis:
            for platform in platforms:
                cursor.execute("""
                    INSERT INTO posting_history 
                    (analysis_id, platform, status, posted_at) 
                    VALUES (?, ?, ?, ?)
                """, (analysis['id'], platform, 'scheduled', post_datetime))
            conn.commit()
        
        st.success("Content scheduled!")
    
    conn.close()

def manage_pending_posts():
    """Manage and approve pending posts."""
    if not st.session_state.pending_posts:
        st.info("No pending posts.")
        return
    
    # Connect to database
    conn = sqlite3.connect('cat_content.db')
    cursor = conn.cursor()
    
    st.subheader("Pending Posts")
    for i, post in enumerate(st.session_state.pending_posts):
        with st.expander(f"Content {i+1}: {post['analysis']['original_filename']}"):
            col1, col2 = st.columns([2, 3])
            
            with col1:
                load_and_display_media(post['analysis']['file_path'])
            
            with col2:
                st.write("Scheduled for:", post['scheduled_time'])
                platforms = post['platforms']
                st.write("Platforms:", ", ".join(platforms))
                st.write("Caption:", post['analysis']['caption'])
                st.write("Hashtags:", post['analysis']['hashtags'])
                
                # Show posting history if available
                if 'id' in post['analysis']:
                    cursor.execute("""
                        SELECT platform, status, posted_at 
                        FROM posting_history 
                        WHERE analysis_id = ?
                        ORDER BY posted_at DESC
                    """, (post['analysis']['id'],))
                    history = cursor.fetchall()
                    if history:
                        st.write("Posting History:")
                        history_df = pd.DataFrame(
                            history,
                            columns=['Platform', 'Status', 'Posted At']
                        )
                        st.dataframe(history_df)
                
                if 'tiktok' in platforms:
                    st.markdown("### TikTok Posting Instructions")
                    st.markdown("""
                    1. [Open TikTok Upload](https://www.tiktok.com/upload)
                    2. Upload your content
                    3. Copy-paste the caption below
                    """)
                    st.text_area(
                        "TikTok Caption & Hashtags",
                        f"{post['analysis']['caption']}\n\n{post['analysis']['hashtags']}",
                        key=f"tiktok_text_{i}"
                    )
                    platforms.remove('tiktok')
                
                if platforms:
                    if st.button("Share Now", key=f"share_now_{i}"):
                        try:
                            results = st.session_state.analyzer.post_to_social_media(
                                post['analysis'],
                                platforms
                            )
                            
                            success = all(results.values())
                            if success:
                                st.success("Content shared successfully!")
                                st.session_state.posted_content.append(post)
                                st.session_state.pending_posts.pop(i)
                            else:
                                failed_platforms = [p for p, r in results.items() if not r]
                                st.error(f"Share failed on: {', '.join(failed_platforms)}")
                        except Exception as e:
                            st.error(f"Error sharing: {e}")
                
                if 'tiktok' in post['platforms']:
                    if st.button("Mark TikTok as Posted", key=f"tiktok_done_{i}"):
                        st.success("TikTok post marked as completed!")
                        if not platforms:
                            st.session_state.posted_content.append(post)
                            st.session_state.pending_posts.pop(i)
                            
                            # Update database for TikTok
                            if 'id' in post['analysis']:
                                cursor.execute("""
                                    UPDATE posting_history 
                                    SET status = 'success', posted_at = ? 
                                    WHERE analysis_id = ? AND platform = 'tiktok'
                                """, (datetime.now(pytz.UTC), post['analysis']['id']))
                                conn.commit()
    
    conn.close()

def view_analytics():
    """View analytics and posting history."""
    if not st.session_state.posted_content:
        st.info("No posted content yet.")
        return
    
    st.markdown("### Posting History")
    
    # Create DataFrame for analytics
    posts_data = []
    for post in st.session_state.posted_content:
        posts_data.append({
            'Filename': post['analysis']['original_filename'],
            'Posted Time': post['scheduled_time'],
            'Platforms': ", ".join(post['platforms']),
            'Total Score': post['analysis']['total_score'],
            'Media Type': post['analysis']['media_type']
        })
    
    df = pd.DataFrame(posts_data)
    
    # Display metrics in an accessible format
    metrics_container = """
        <div role="region" aria-label="Analytics metrics" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: 1rem 0;">
    """
    
    metrics = [
        {'label': 'Total Posts', 'value': len(df)},
        {'label': 'Average Score', 'value': f"{df['Total Score'].mean():.1f}"},
        {'label': 'Images', 'value': len(df[df['Media Type'] == 'image'])},
        {'label': 'Videos', 'value': len(df[df['Media Type'] == 'video'])}
    ]
    
    for metric in metrics:
        metrics_container += f"""
            <div role="article" aria-label="{metric['label']} metric" style="
                background: linear-gradient(135deg, #C8E6C9, #A5D6A7);
                padding: 1rem;
                border-radius: 8px;
                text-align: center;
                border: 1px solid rgba(46, 125, 50, 0.2);
            ">
                <div style="font-size: 0.875rem; color: #1A1A1A; margin-bottom: 0.5rem;">{metric['label']}</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #2E7D32;">{metric['value']}</div>
            </div>
        """
    
    metrics_container += "</div>"
    st.markdown(metrics_container, unsafe_allow_html=True)
    
    # Display posting history in an accessible table
    st.markdown("### Recent Posts")
    table_html = df.to_html(
        index=False,
        classes=['styled-table'],
        table_id='posting-history'
    )
    custom_scrollable_region(
        f"""
        <div role="region" aria-label="Posting history table">
            {table_html}
        </div>
        """,
        max_height="400px",
        label="Posting history",
        key="posting_history"
    )
    
    # Platform distribution with accessible chart
    st.markdown("### Platform Distribution")
    platform_counts = df['Platforms'].str.split(", ").explode().value_counts()
    
    # Create accessible bar chart
    chart_container = """
        <div role="region" aria-label="Platform distribution chart" style="margin: 1rem 0;">
            <table class="styled-table" style="width: 100%;">
                <caption style="font-weight: bold; margin-bottom: 0.5rem;">Posts by Platform</caption>
                <thead>
                    <tr>
                        <th scope="col">Platform</th>
                        <th scope="col">Number of Posts</th>
                        <th scope="col">Visual Representation</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    max_count = platform_counts.max()
    for platform, count in platform_counts.items():
        percentage = (count / max_count) * 100
        chart_container += f"""
            <tr>
                <th scope="row">{platform}</th>
                <td>{count}</td>
                <td>
                    <div style="
                        width: {percentage}%;
                        height: 24px;
                        background: linear-gradient(135deg, #2E7D32, #43A047);
                        border-radius: 4px;
                        position: relative;
                    " role="img" aria-label="{platform}: {count} posts">
                        <span style="
                            position: absolute;
                            left: 8px;
                            top: 50%;
                            transform: translateY(-50%);
                            color: white;
                            font-weight: bold;
                        ">{count}</span>
                    </div>
                </td>
            </tr>
        """
    
    chart_container += """
                </tbody>
            </table>
        </div>
    """
    
    st.markdown(chart_container, unsafe_allow_html=True)
    
    # Database Analytics with improved accessibility
    st.markdown("### Database Analytics")
    
    # Get posting history from database
    posting_history = st.session_state.analyzer.get_posting_history()
    if posting_history:
        history_df = pd.DataFrame(
            posting_history,
            columns=['Filename', 'Platform', 'Status', 'Posted At']
        )
        
        # Display success rate by platform
        st.markdown("#### Success Rate by Platform")
        success_rate = history_df.groupby('Platform')['Status'].apply(
            lambda x: (x == 'success').mean() * 100
        ).round(1)
        
        success_table = """
            <div role="region" aria-label="Success rate by platform">
                <table class="styled-table" style="width: 100%;">
                    <caption style="font-weight: bold; margin-bottom: 0.5rem;">Platform Success Rates</caption>
                    <thead>
                        <tr>
                            <th scope="col">Platform</th>
                            <th scope="col">Success Rate</th>
                            <th scope="col">Visual Indicator</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for platform, rate in success_rate.items():
            success_table += f"""
                <tr>
                    <th scope="row">{platform}</th>
                    <td>{rate}%</td>
                    <td>
                        <div style="
                            width: {rate}%;
                            height: 24px;
                            background: linear-gradient(135deg, #2E7D32, #43A047);
                            border-radius: 4px;
                            position: relative;
                        " role="img" aria-label="{platform} success rate: {rate}%">
                            <span style="
                                position: absolute;
                                left: 8px;
                                top: 50%;
                                transform: translateY(-50%);
                                color: white;
                                font-weight: bold;
                            ">{rate}%</span>
                        </div>
                    </td>
                </tr>
            """
        
        success_table += """
                    </tbody>
                </table>
            </div>
        """
        
        st.markdown(success_table, unsafe_allow_html=True)
        
        # Display recent posting activity
        st.markdown("#### Recent Posting Activity")
        recent_posts = history_df.sort_values('Posted At', ascending=False).head(10)
        recent_posts_html = recent_posts.to_html(
            index=False,
            classes=['styled-table'],
            table_id='recent-posts'
        )
        custom_scrollable_region(
            f"""
            <div role="region" aria-label="Recent posting activity">
                {recent_posts_html}
            </div>
            """,
            max_height="400px",
            label="Recent posts",
            key="recent_posts"
        )
        
        # Show posting activity over time with accessible timeline
        st.markdown("#### Posting Activity Over Time")
        history_df['Posted At'] = pd.to_datetime(history_df['Posted At'])
        daily_posts = history_df.resample('D', on='Posted At').size()
        
        timeline_html = """
            <div role="region" aria-label="Posting activity timeline" style="margin: 1rem 0;">
                <table class="styled-table" style="width: 100%;">
                    <caption style="font-weight: bold; margin-bottom: 0.5rem;">Daily Posting Activity</caption>
                    <thead>
                        <tr>
                            <th scope="col">Date</th>
                            <th scope="col">Posts</th>
                            <th scope="col">Activity Level</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        max_posts = daily_posts.max()
        for date, count in daily_posts.items():
            percentage = (count / max_posts) * 100 if max_posts > 0 else 0
            timeline_html += f"""
                <tr>
                    <th scope="row">{date.strftime('%Y-%m-%d')}</th>
                    <td>{count}</td>
                    <td>
                        <div style="
                            width: {percentage}%;
                            height: 24px;
                            background: linear-gradient(135deg, #2E7D32, #43A047);
                            border-radius: 4px;
                            position: relative;
                        " role="img" aria-label="Posts on {date.strftime('%Y-%m-%d')}: {count}">
                            <span style="
                                position: absolute;
                                left: 8px;
                                top: 50%;
                                transform: translateY(-50%);
                                color: white;
                                font-weight: bold;
                            ">{count}</span>
                        </div>
                    </td>
                </tr>
            """
        
        timeline_html += """
                    </tbody>
                </table>
            </div>
        """
        
        custom_scrollable_region(
            timeline_html,
            max_height="400px",
            label="Posting timeline",
            key="posting_timeline"
        )

def view_database():
    """View and manage the SQLite database."""
    st.header("Database Management")
    
    # Connect to database
    conn = sqlite3.connect('cat_content.db')
    
    # Sidebar for table selection
    tables = ['content_analysis', 'category_scores', 'posting_history']
    selected_table = st.selectbox("Select Table to View", tables)
    
    # Query builder
    st.subheader(f"View {selected_table}")
    
    # Get table schema
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({selected_table})")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Create query options
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Filter options
        filter_column = st.selectbox("Filter by column", ["None"] + columns)
        if filter_column != "None":
            filter_value = st.text_input("Filter value")
    
    with col2:
        # Sort options
        sort_column = st.selectbox("Sort by", ["None"] + columns)
        if sort_column != "None":
            sort_order = st.radio("Sort order", ["ASC", "DESC"])
    
    # Build and execute query
    query = f"SELECT * FROM {selected_table}"
    params = []
    
    if filter_column != "None" and filter_value:
        query += f" WHERE {filter_column} LIKE ?"
        params.append(f"%{filter_value}%")
    
    if sort_column != "None":
        query += f" ORDER BY {sort_column} {sort_order}"
    
    # Execute query and display results
    try:
        df = pd.read_sql_query(query, conn, params=params)
        st.dataframe(df, use_container_width=True)
        
        # Export options
        if not df.empty:
            csv = df.to_csv(index=False)
            st.download_button(
                "Download as CSV",
                csv,
                f"{selected_table}.csv",
                "text/csv",
                key=f'download_{selected_table}'
            )
    except Exception as e:
        st.error(f"Error querying database: {e}")
    
    # Database statistics
    st.subheader("Database Statistics")
    stats_col1, stats_col2, stats_col3 = st.columns(3)
    
    with stats_col1:
        cursor.execute(f"SELECT COUNT(*) FROM {selected_table}")
        total_rows = cursor.fetchone()[0]
        st.metric("Total Rows", total_rows)
    
    with stats_col2:
        if selected_table == 'content_analysis':
            cursor.execute("SELECT AVG(total_score) FROM content_analysis")
            avg_score = cursor.fetchone()[0]
            st.metric("Average Score", f"{avg_score:.1f}" if avg_score else "N/A")
    
    with stats_col3:
        if selected_table == 'posting_history':
            cursor.execute("SELECT COUNT(DISTINCT platform) FROM posting_history")
            platform_count = cursor.fetchone()[0]
            st.metric("Active Platforms", platform_count)
    
    # Database maintenance
    st.subheader("Database Maintenance")
    maintenance_col1, maintenance_col2 = st.columns(2)
    
    with maintenance_col1:
        if st.button("Vacuum Database"):
            try:
                cursor.execute("VACUUM")
                st.success("Database optimized successfully")
            except Exception as e:
                st.error(f"Error optimizing database: {e}")
    
    with maintenance_col2:
        if st.button("Export Full Database"):
            try:
                # Export all tables
                tables_data = {}
                for table in tables:
                    tables_data[table] = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                
                # Create JSON string
                json_data = {
                    table: df.to_dict(orient='records') 
                    for table, df in tables_data.items()
                }
                
                st.download_button(
                    "Download Full Database",
                    json.dumps(json_data, indent=2),
                    "database_export.json",
                    "application/json",
                    key='download_full_db'
                )
            except Exception as e:
                st.error(f"Error exporting database: {e}")
    
    # Close connection
    conn.close()

def create_post():
    """Create and schedule posts for different platforms."""
    st.header("Create Post")
    
    # Create temp directory if it doesn't exist
    temp_dir = Path("temp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Add tabs for new content vs existing content
    tab1, tab2 = st.tabs(["Upload New Content", "Use Existing Content"])
    
    with tab1:
        # Platform selection
        platforms = st.multiselect(
            "Select platforms to post to:",
            ['Instagram', 'Twitter', 'Facebook', 'TikTok'],
            default=['Instagram']
        )
        
        if not platforms:
            st.warning("Please select at least one platform.")
            return
        
        # Media upload
        uploaded_files = st.file_uploader(
            "Upload media (images/videos)",
            accept_multiple_files=True,
            type=['png', 'jpg', 'jpeg', 'mp4', 'mov', 'avi']
        )
        
        if uploaded_files:
            for file in uploaded_files:
                st.write(f"Processing: {file.name}")
                
                # Save file temporarily
                temp_path = Path("temp") / f"temp_{file.name}"
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(temp_path, "wb") as f:
                    f.write(file.getbuffer())
                
                # Display media preview
                if file.type.startswith('video'):
                    st.video(temp_path)
                else:
                    st.image(temp_path)
                
                # Post customization
                with st.expander("Post Details", expanded=True):
                    _handle_post_details(file.name, temp_path, platforms)
    
    with tab2:
        # Connect to database
        conn = sqlite3.connect('cat_content.db')
        cursor = conn.cursor()
        
        try:
            # Get all analyzed content
            cursor.execute("""
                SELECT ca.id, ca.original_filename, ca.media_type, ca.total_score, 
                       ca.caption, ca.hashtags, ca.file_path, ca.created_at,
                       GROUP_CONCAT(DISTINCT ph.platform) as posted_platforms
                FROM content_analysis ca
                LEFT JOIN posting_history ph ON ca.id = ph.analysis_id
                GROUP BY ca.id
                ORDER BY ca.created_at DESC
            """)
            content_list = cursor.fetchall()
            
            if not content_list:
                st.info("No existing content found in the database.")
                return
            
            # Create a DataFrame for better display
            df = pd.DataFrame(content_list, columns=[
                'id', 'filename', 'media_type', 'score', 'caption', 
                'hashtags', 'file_path', 'created_at', 'posted_platforms'
            ])
            
            # Add filters
            col1, col2, col3 = st.columns(3)
            with col1:
                media_type_filter = st.multiselect(
                    "Filter by media type",
                    df['media_type'].unique(),
                    default=df['media_type'].unique()
                )
            with col2:
                min_score = st.number_input("Minimum score", 0, 50, 0)
            with col3:
                search_term = st.text_input("Search in filename")
            
            # Apply filters
            mask = (
                df['media_type'].isin(media_type_filter) &
                (df['score'] >= min_score)
            )
            if search_term:
                mask &= df['filename'].str.contains(search_term, case=False)
            
            filtered_df = df[mask]
            
            # Display filtered content
            for _, row in filtered_df.iterrows():
                with st.expander(f"{row['filename']} (Score: {row['score']}/50)"):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        try:
                            # Load and display media
                            original_path = Path(row['file_path'])
                            temp_path = temp_dir / f"reuse_{row['id']}_{row['filename']}"
                            
                            # Check if the original file exists
                            if original_path.exists():
                                # Copy file to temp directory if it doesn't exist or is outdated
                                if not temp_path.exists() or temp_path.stat().st_mtime < original_path.stat().st_mtime:
                                    import shutil
                                    shutil.copy2(original_path, temp_path)
                                
                                # Display media
                                if row['media_type'] == 'video':
                                    st.video(str(temp_path))
                                else:
                                    st.image(str(temp_path))
                            else:
                                st.error(f"Original file not found: {original_path}")
                                continue
                        except Exception as e:
                            st.error(f"Error loading media: {e}")
                            continue
                    
                    with col2:
                        # Show posting history
                        if row['posted_platforms']:
                            st.write("Previously posted to:", row['posted_platforms'])
                        
                        # Platform selection for reposting
                        platforms = st.multiselect(
                            "Select platforms to post to:",
                            ['Instagram', 'Twitter', 'Facebook', 'TikTok'],
                            key=f"platforms_reuse_{row['id']}"
                        )
                        
                        if platforms:
                            # Get existing caption and hashtags
                            caption = st.text_area(
                                "Caption",
                                value=row['caption'],
                                key=f"caption_reuse_{row['id']}"
                            )
                            
                            hashtags = st.text_area(
                                "Hashtags",
                                value=row['hashtags'],
                                key=f"hashtags_reuse_{row['id']}"
                            )
                            
                            # Platform-specific options
                            if 'Instagram' in platforms:
                                st.checkbox("Also share to Instagram Story", key=f"insta_story_reuse_{row['id']}")
                            if 'Facebook' in platforms:
                                st.checkbox("Share to Facebook Story", key=f"fb_story_reuse_{row['id']}")
                            if 'TikTok' in platforms:
                                st.slider("Video Duration (seconds)", 0, 60, 30, key=f"tiktok_duration_reuse_{row['id']}")
                            
                            # Scheduling options
                            col1, col2 = st.columns(2)
                            with col1:
                                post_date = st.date_input(
                                    "Schedule date",
                                    value=datetime.now(pytz.UTC).date(),
                                    key=f"schedule_date_reuse_{row['id']}"
                                )
                            with col2:
                                post_time = st.time_input(
                                    "Schedule time",
                                    value=datetime.now(pytz.UTC).time(),
                                    key=f"schedule_time_reuse_{row['id']}"
                                )
                            
                            schedule_datetime = datetime.combine(post_date, post_time)
                            schedule_datetime = pytz.UTC.localize(schedule_datetime)
                            
                            # Best time suggestions
                            st.info("""
                            💡 Recommended posting times (ET):
                            - Instagram: 11 AM - 2 PM, 7 PM - 9 PM
                            - Twitter: 9 AM - 11 AM, 5 PM - 7 PM
                            - Facebook: 1 PM - 4 PM
                            - TikTok: 6 PM - 9 PM
                            """)
                            
                            # Post now or schedule
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Post Now", key=f"post_now_reuse_{row['id']}"):
                                    try:
                                        post_data = {
                                            'id': row['id'],
                                            'file_path': str(temp_path),
                                            'caption': caption,
                                            'hashtags': hashtags,
                                            'platforms': platforms,
                                            'scheduled_time': datetime.now(pytz.UTC),
                                            'media_type': row['media_type']
                                        }
                                        
                                        results = st.session_state.analyzer.post_to_social_media(
                                            post_data,
                                            [p.lower() for p in platforms]
                                        )
                                        
                                        for platform, success in results.items():
                                            if success:
                                                st.success(f"Posted to {platform}")
                                            else:
                                                st.error(f"Failed to post to {platform}")
                                    except Exception as e:
                                        st.error(f"Error posting: {e}")
                            
                            with col2:
                                if st.button("Schedule Post", key=f"schedule_reuse_{row['id']}"):
                                    try:
                                        scheduled_post = {
                                            'id': row['id'],
                                            'file_path': str(temp_path),
                                            'caption': caption,
                                            'hashtags': hashtags,
                                            'platforms': platforms,
                                            'scheduled_time': schedule_datetime,
                                            'status': 'pending',
                                            'media_type': row['media_type']
                                        }
                                        
                                        st.session_state.pending_posts.append(scheduled_post)
                                        st.success(f"Post scheduled for {schedule_datetime.strftime('%Y-%m-%d %I:%M %p %Z')}")
                                    except Exception as e:
                                        st.error(f"Error scheduling post: {e}")
        except Exception as e:
            st.error(f"Error accessing database: {e}")
        finally:
            conn.close()

def _handle_post_details(filename, temp_path, platforms):
    """Helper function to handle post details form."""
    # Caption with character count
    caption = st.text_area(
        "Caption",
        help="Write your post caption here. Instagram captions work best under 125 characters.",
        key=f"caption_{filename}"
    )
    st.write(f"Character count: {len(caption)}/2200")
    
    # Hashtag suggestions based on platforms
    suggested_hashtags = []
    if 'Instagram' in platforms:
        suggested_hashtags.extend(['#catsofinstagram', '#catstagram', '#cats'])
    if 'Twitter' in platforms:
        suggested_hashtags.extend(['#CatsOfTwitter', '#cats'])
    if 'TikTok' in platforms:
        suggested_hashtags.extend(['#catsoftiktok', '#cattok'])
    
    hashtags = st.multiselect(
        "Select hashtags",
        suggested_hashtags,
        default=suggested_hashtags[:5],
        key=f"hashtags_{filename}"
    )
    custom_hashtags = st.text_input(
        "Add custom hashtags (comma-separated)",
        key=f"custom_hashtags_{filename}"
    )
    
    if custom_hashtags:
        hashtags.extend([tag.strip() for tag in custom_hashtags.split(',')])
    
    # Platform-specific options
    if 'Instagram' in platforms:
        st.checkbox("Also share to Instagram Story", key=f"insta_story_{filename}")
    if 'Facebook' in platforms:
        st.checkbox("Share to Facebook Story", key=f"fb_story_{filename}")
    if 'TikTok' in platforms:
        st.slider("Video Duration (seconds)", 0, 60, 30, key=f"tiktok_duration_{filename}")
    
    # Scheduling options
    col1, col2 = st.columns(2)
    with col1:
        post_date = st.date_input(
            "Schedule date",
            value=datetime.now(pytz.UTC).date(),
            key=f"schedule_date_{filename}"
        )
    with col2:
        post_time = st.time_input(
            "Schedule time",
            value=datetime.now(pytz.UTC).time(),
            key=f"schedule_time_{filename}"
        )
    
    schedule_datetime = datetime.combine(post_date, post_time)
    schedule_datetime = pytz.UTC.localize(schedule_datetime)
    
    # Best time suggestions
    st.info("""
    💡 Recommended posting times (ET):
    - Instagram: 11 AM - 2 PM, 7 PM - 9 PM
    - Twitter: 9 AM - 11 AM, 5 PM - 7 PM
    - Facebook: 1 PM - 4 PM
    - TikTok: 6 PM - 9 PM
    """)
    
    # Schedule or post now
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Post Now", key=f"post_now_{filename}"):
            try:
                post_data = {
                    'file_path': str(temp_path),
                    'caption': caption,
                    'hashtags': ' '.join(hashtags),
                    'platforms': platforms,
                    'scheduled_time': datetime.now(pytz.UTC),
                    'media_type': row['media_type']
                }
                
                results = st.session_state.analyzer.post_to_social_media(
                    post_data,
                    [p.lower() for p in platforms]
                )
                
                for platform, success in results.items():
                    if success:
                        st.success(f"Content shared to {platform}")
                    else:
                        st.error(f"Share failed on {platform}")
            except Exception as e:
                st.error(f"Error sharing: {e}")
    
    with col2:
        if st.button("Schedule Post", key=f"schedule_{filename}"):
            try:
                scheduled_post = {
                    'file_path': str(temp_path),
                    'caption': caption,
                    'hashtags': ' '.join(hashtags),
                    'platforms': platforms,
                    'scheduled_time': schedule_datetime,
                    'status': 'pending',
                    'media_type': row['media_type']
                }
                
                st.session_state.pending_posts.append(scheduled_post)
                st.success(f"Post scheduled for {schedule_datetime.strftime('%Y-%m-%d %I:%M %p %Z')}")
            except Exception as e:
                st.error(f"Error scheduling post: {e}")

def auto_schedule_posts():
    """Automatically schedule posts with timeline view."""
    st.header("Auto Post Scheduler")
    
    # Create two columns for the layout
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.subheader("Content Selection")
        
        # Connect to database
        conn = sqlite3.connect('cat_content.db')
        cursor = conn.cursor()
        
        try:
            # Get all analyzed content that hasn't been posted yet or was posted more than 30 days ago
            cursor.execute("""
                SELECT 
                    ca.id, 
                    ca.original_filename, 
                    ca.media_type, 
                    ca.total_score,
                    ca.caption, 
                    ca.hashtags, 
                    ca.file_path,
                    ca.engagement_tips,
                    ca.key_strengths,
                    ca.improvement_suggestions,
                    GROUP_CONCAT(DISTINCT ph.platform) as posted_platforms,
                    MAX(ph.posted_at) as last_posted
                FROM content_analysis ca
                LEFT JOIN posting_history ph ON ca.id = ph.analysis_id
                GROUP BY ca.id
                HAVING last_posted IS NULL 
                    OR datetime(last_posted) < datetime('now', '-30 days')
                ORDER BY ca.total_score DESC
            """)
            available_content = cursor.fetchall()
            
            if not available_content:
                st.warning("No content available for scheduling. Please analyze some content first.")
                return
            
            # Create DataFrame for content selection
            df = pd.DataFrame(available_content, columns=[
                'id', 'filename', 'media_type', 'score', 'caption', 
                'hashtags', 'file_path', 'engagement_tips', 'key_strengths',
                'improvement_suggestions', 'posted_platforms', 'last_posted'
            ])
            
            # Content filters
            st.write("Filter Content")
            col_filter1, col_filter2 = st.columns(2)
            
            with col_filter1:
                media_types = st.multiselect(
                    "Media Type",
                    df['media_type'].unique(),
                    default=df['media_type'].unique()
                )
            
            with col_filter2:
                min_score = st.slider("Minimum Score", 0, 50, 30)
            
            # Apply filters
            mask = (df['media_type'].isin(media_types)) & (df['score'] >= min_score)
            
            filtered_df = df[mask].copy()
            
            # Content selection
            selected_content = st.multiselect(
                "Select content to schedule",
                filtered_df['filename'].tolist(),
                default=filtered_df['filename'].head(5).tolist(),
                help="Choose the content you want to schedule. Selected content will be scheduled based on quality score."
            )
            
            if not selected_content:
                st.warning("Please select at least one piece of content to schedule.")
                return
            
            # Get selected content data
            selected_df = filtered_df[filtered_df['filename'].isin(selected_content)]
            
            # Platform selection (limited to Instagram and Twitter)
            platforms = st.multiselect(
                "Select platforms for auto-posting",
                ['Instagram', 'Twitter'],
                default=['Instagram', 'Twitter']
            )
            
            # Time range selection
            st.subheader("Posting Schedule")
            col_time1, col_time2 = st.columns(2)
            with col_time1:
                start_time = st.time_input("Start posting from", value=datetime.strptime("09:00", "%H:%M").time())
            with col_time2:
                end_time = st.time_input("End posting at", value=datetime.strptime("21:00", "%H:%M").time())
            
            # Days selection
            days = st.multiselect(
                "Select posting days",
                ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                default=['Monday', 'Wednesday', 'Friday']
            )
            
            # Posts per day
            posts_per_day = st.slider("Posts per day", 1, 5, 2)
            
            # Minimum gap between posts
            min_gap_hours = st.slider("Minimum hours between posts", 2, 8, 4)
            
            # Generate schedule button
            generate_schedule = st.button("Generate Schedule", type="primary")
            
        except Exception as e:
            st.error(f"Error accessing database: {e}")
            return
        finally:
            conn.close()
    
    with col2:
        if generate_schedule and selected_content:
            st.subheader("Generated Schedule")
            
            # Sort selected content by score
            selected_df = selected_df.sort_values('score', ascending=False)
            
            # Generate posting schedule
            schedule = []
            current_date = datetime.now(pytz.UTC).date()
            content_index = 0
            
            # Create schedule for next 7 days
            for _ in range(7):
                if current_date.strftime('%A') in days:
                    # Calculate posting times for the day
                    day_start = datetime.combine(current_date, start_time)
                    day_end = datetime.combine(current_date, end_time)
                    
                    # Divide time range into equal intervals
                    time_range = (day_end - day_start).seconds / 3600
                    interval = max(time_range / posts_per_day, min_gap_hours)
                    
                    for i in range(posts_per_day):
                        if content_index < len(selected_df):
                            post_time = day_start + timedelta(hours=i * interval)
                            content = selected_df.iloc[content_index]
                            
                            schedule.append({
                                'datetime': post_time,
                                'content': {
                                    'id': content['id'],
                                    'original_filename': content['filename'],
                                    'file_path': content['file_path'],
                                    'media_type': content['media_type'],
                                    'total_score': content['score'],
                                    'caption': content['caption'],
                                    'hashtags': content['hashtags'],
                                    'engagement_tips': content['engagement_tips'],
                                    'key_strengths': content['key_strengths'],
                                    'improvement_suggestions': content['improvement_suggestions']
                                },
                                'platforms': platforms
                            })
                            
                            content_index = (content_index + 1) % len(selected_df)
                
                current_date += timedelta(days=1)
            
            # Display timeline
            for post in schedule:
                post_expander = st.expander(
                    f"📅 {post['datetime'].strftime('%A, %B %d, %I:%M %p')} - {post['content']['original_filename']}", 
                    expanded=True
                )
                
                with post_expander:
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        # Display media preview
                        try:
                            if post['content']['media_type'] == 'video':
                                st.video(post['content']['file_path'])
                            else:
                                st.image(post['content']['file_path'])
                        except Exception as e:
                            st.error(f"Error loading media: {e}")
                    
                    with col2:
                        # Display and allow editing of post details
                        platforms_str = " & ".join(post['platforms'])
                        st.write(f"🎯 Posting to: {platforms_str}")
                        st.write(f"📊 Content Score: {post['content']['total_score']}/50")
                        
                        # Editable caption and hashtags
                        edited_caption = st.text_area(
                            "Edit Caption",
                            post['content']['caption'],
                            key=f"caption_{post['datetime']}_{post['content']['id']}"
                        )
                        edited_hashtags = st.text_area(
                            "Edit Hashtags",
                            post['content']['hashtags'],
                            key=f"hashtags_{post['datetime']}_{post['content']['id']}"
                        )
                        
                        # Update post data with edits
                        post['content']['caption'] = edited_caption
                        post['content']['hashtags'] = edited_hashtags
                        
                        # Show content insights
                        st.write("💡 Engagement Tips:", post['content']['engagement_tips'])
                        st.write("💪 Key Strengths:", post['content']['key_strengths'])
                        st.write("📈 Improvement Suggestions:", post['content']['improvement_suggestions'])
                        
                        # Approval button
                        if st.button("✅ Approve Post", key=f"approve_{post['datetime']}_{post['content']['id']}"):
                            try:
                                # Add to pending posts
                                scheduled_post = {
                                    'analysis': post['content'],
                                    'platforms': [p.lower() for p in post['platforms']],
                                    'scheduled_time': post['datetime'].replace(tzinfo=pytz.UTC),
                                    'status': 'pending'
                                }
                                st.session_state.pending_posts.append(scheduled_post)
                                st.success("Post approved and scheduled!")
                            except Exception as e:
                                st.error(f"Error scheduling post: {e}")
            
            # Add download schedule button
            schedule_df = pd.DataFrame([
                {
                    'Date': post['datetime'].strftime('%Y-%m-%d'),
                    'Time': post['datetime'].strftime('%I:%M %p'),
                    'File': post['content']['original_filename'],
                    'Platforms': ' & '.join(post['platforms']),
                    'Caption': post['content']['caption'],
                    'Hashtags': post['content']['hashtags'],
                    'Score': post['content']['total_score']
                }
                for post in schedule
            ])
            
            csv = schedule_df.to_csv(index=False)
            st.download_button(
                "📥 Download Schedule as CSV",
                csv,
                "posting_schedule.csv",
                "text/csv",
                key='download_schedule'
            )

def view_posted_content():
    """Display all posted content with details and metrics."""
    st.header("Posted Content History")
    
    # Connect to database
    conn = sqlite3.connect('cat_content.db')
    cursor = conn.cursor()
    
    try:
        # Get all successfully posted content
        cursor.execute("""
            SELECT 
                ca.id,
                ca.original_filename,
                ca.media_type,
                ca.total_score,
                ca.caption,
                ca.hashtags,
                ca.file_path,
                ph.platform,
                ph.posted_at,
                ph.status,
                ph.id as post_history_id
            FROM content_analysis ca
            JOIN posting_history ph ON ca.id = ph.analysis_id
            WHERE ph.status = 'success'
            ORDER BY ph.posted_at DESC
        """)
        posts = cursor.fetchall()
        
        if not posts:
            st.info("No posted content found in the history.")
            return
        
        # Group posts by date
        from itertools import groupby
        from datetime import datetime
        
        # Convert posts to list of dicts for easier handling
        posts_data = []
        for p in posts:
            try:
                # Handle different datetime string formats
                posted_at_str = p[8]
                try:
                    # Try parsing with timezone
                    posted_at = datetime.strptime(posted_at_str.split('+')[0], '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    try:
                        # Try parsing without microseconds
                        posted_at = datetime.strptime(posted_at_str.split('+')[0], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        # If all else fails, try basic format
                        posted_at = datetime.strptime(posted_at_str, '%Y-%m-%d %H:%M:%S')
                
                posts_data.append({
                    'id': p[0],
                    'filename': p[1],
                    'media_type': p[2],
                    'score': p[3],
                    'caption': p[4],
                    'hashtags': p[5],
                    'file_path': p[6],
                    'platform': p[7],
                    'posted_at': posted_at,
                    'status': p[9],
                    'post_history_id': p[10]  # Add unique post history ID
                })
            except Exception as e:
                st.warning(f"Skipping post due to date parsing error: {e}")
                continue
        
        # Sort posts by date
        posts_data.sort(key=lambda x: x['posted_at'], reverse=True)
        
        # Group by date
        current_date = None
        for post in posts_data:
            post_date = post['posted_at'].date()
            
            # Create new date section if date changes
            if post_date != current_date:
                if current_date is not None:
                    st.divider()
                current_date = post_date
                
                # Create date header with post count
                same_day_posts = [p for p in posts_data if p['posted_at'].date() == post_date]
                st.subheader(f"📅 {post_date.strftime('%B %d, %Y')} ({len(same_day_posts)} posts)")
                
                # Create columns for filters
                col1, col2, col3 = st.columns(3)
                with col1:
                    platform_filter = st.multiselect(
                        "Filter by platform",
                        list(set(p['platform'] for p in same_day_posts)),
                        key=f"platform_filter_{post_date}"
                    )
                with col2:
                    media_filter = st.multiselect(
                        "Filter by media type",
                        list(set(p['media_type'] for p in same_day_posts)),
                        key=f"media_filter_{post_date}"
                    )
                with col3:
                    min_score = st.slider(
                        "Minimum score",
                        0, 50, 0,
                        key=f"score_filter_{post_date}"
                    )
                
                # Apply filters
                filtered_posts = [
                    p for p in same_day_posts
                    if (not platform_filter or p['platform'] in platform_filter)
                    and (not media_filter or p['media_type'] in media_filter)
                    and p['score'] >= min_score
                ]
                
                # Display posts in a grid
                cols = st.columns(3)
                for i, post in enumerate(filtered_posts):
                    with cols[i % 3]:
                        st.markdown(f"### 🎯 {post['platform'].title()} - {post['posted_at'].strftime('%I:%M %p')}")
                        try:
                            # Check if media file exists
                            file_path = Path(post['file_path'])
                            if file_path.exists():
                                if post['media_type'] == 'video':
                                    st.video(str(file_path))
                                else:
                                    st.image(str(file_path))
                            else:
                                # Try to find the file in temp directory
                                temp_file = Path("temp") / f"reuse_{post['id']}_{post['filename']}"
                                if temp_file.exists():
                                    if post['media_type'] == 'video':
                                        st.video(str(temp_file))
                                    else:
                                        st.image(str(temp_file))
                                else:
                                    st.warning(f"Media file not found: {post['filename']}")
                                    # Update the file path in the database to point to temp directory
                                    cursor.execute("""
                                        UPDATE content_analysis
                                        SET file_path = ?
                                        WHERE id = ?
                                    """, (str(temp_file), post['id']))
                                    conn.commit()
                            
                            # Post details
                            st.write(f"**File:** {post['filename']}")
                            st.write(f"**Score:** {post['score']}/50")
                            
                            # Engagement metrics
                            cursor.execute("""
                                SELECT likes, comments, shares, views
                                FROM engagement_metrics
                                WHERE post_id = ? AND platform = ?
                            """, (post['id'], post['platform']))
                            metrics = cursor.fetchone()
                            
                            if metrics:
                                metric_cols = st.columns(4)
                                with metric_cols[0]:
                                    st.metric("Likes", metrics[0] or 0)
                                with metric_cols[1]:
                                    st.metric("Comments", metrics[1] or 0)
                                with metric_cols[2]:
                                    st.metric("Shares", metrics[2] or 0)
                                with metric_cols[3]:
                                    st.metric("Views", metrics[3] or 0)
                            
                            # Post content
                            st.markdown("##### 📝 Post Content")
                            st.markdown("**Caption:**")
                            st.markdown(f"```\n{post['caption']}\n```")
                            st.markdown("**Hashtags:**")
                            st.markdown(f"```\n{post['hashtags']}\n```")
                            
                            # Repost button with unique key using post_history_id
                            if st.button("🔄 Repost", key=f"repost_{post['post_history_id']}"):
                                # Add to pending posts for reposting
                                st.session_state.pending_posts.append({
                                    'analysis': {
                                        'id': post['id'],
                                        'file_path': str(file_path) if file_path.exists() else str(temp_file),
                                        'caption': post['caption'],
                                        'hashtags': post['hashtags'],
                                        'media_type': post['media_type'],
                                        'total_score': post['score']
                                    },
                                    'platforms': [post['platform']],
                                    'scheduled_time': datetime.now(pytz.UTC),
                                    'status': 'pending'
                                })
                                st.success("Added to pending posts! Go to Post Manager to schedule.")
                            
                            # Add a divider between posts in the same column
                            st.divider()
                            
                        except Exception as e:
                            st.error(f"Error displaying post: {e}")
    
    except Exception as e:
        st.error(f"Error accessing database: {e}")
    finally:
        conn.close()

@make_accessible
def main():
    # Update main header with accessible components
    st.markdown("""
        <h1 style="font-size: 2.5rem; font-weight: bold; background: linear-gradient(135deg, #2E7D32, #43A047); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            🐱 Cat Content Manager
        </h1>
        <p style="color: #666666; font-size: 1.1rem;">
            Analyze, Schedule, and Share Your Cat Content
        </p>
    """, unsafe_allow_html=True)
    
    # Add accessible header buttons with proper ARIA labels and roles
    col1, col2 = st.columns([6, 1])
    with col2:
        st.markdown("""
            <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
                <button
                    class="header-button"
                    role="button"
                    aria-label="Open Settings"
                    title="Open Settings"
                    onclick="window.parent.postMessage({type: 'streamlit:message', action: 'headerButtonClicked', key: 'settings_button'}, '*')"
                    style="
                        min-height: 44px;
                        padding: 8px 16px;
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        gap: 8px;
                        font-weight: 600;
                        border-radius: 8px;
                        cursor: pointer;
                        background: linear-gradient(135deg, #2E7D32, #43A047);
                        color: #FFFFFF;
                        border: none;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    "
                >
                    <span aria-hidden="true" style="font-size: 1.2rem;">⚙️</span>
                    <span style="font-size: 1rem;">Settings</span>
                </button>
                <button
                    class="header-button"
                    role="button"
                    aria-label="Get Help"
                    title="Get Help"
                    onclick="window.parent.postMessage({type: 'streamlit:message', action: 'headerButtonClicked', key: 'help_button'}, '*')"
                    style="
                        min-height: 44px;
                        padding: 8px 16px;
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        gap: 8px;
                        font-weight: 600;
                        border-radius: 8px;
                        cursor: pointer;
                        background: linear-gradient(135deg, #2E7D32, #43A047);
                        color: #FFFFFF;
                        border: none;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    "
                >
                    <span aria-hidden="true" style="font-size: 1.2rem;">❓</span>
                    <span style="font-size: 1rem;">Help</span>
                </button>
            </div>
        """, unsafe_allow_html=True)
    
    # Override Streamlit's main menu button styles and ARIA attributes
    st.markdown("""
        <style>
            /* Fix main menu button accessibility */
            [data-testid="stMainMenu"] {
                visibility: hidden;
                position: absolute;
            }
            
            /* Custom accessible menu button */
            .custom-menu-button {
                position: fixed;
                top: 0.5rem;
                right: 0.5rem;
                z-index: 1000;
            }
        </style>
        
        <div class="custom-menu-button">
            <button
                role="button"
                aria-label="Main menu"
                title="Main menu"
                onclick="document.querySelector('[data-testid=stMainMenu]').click()"
                style="
                    min-height: 44px;
                    padding: 8px 16px;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    font-weight: 600;
                    border-radius: 8px;
                    cursor: pointer;
                    background: linear-gradient(135deg, #2E7D32, #43A047);
                    color: #FFFFFF;
                    border: none;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                "
            >
                <span aria-hidden="true" style="font-size: 1.2rem;">≡</span>
                <span style="font-size: 1rem;">Menu</span>
            </button>
        </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation with improved accessibility
    with st.sidebar:
        st.markdown("""
            <nav role="navigation" aria-label="Main navigation">
                <div style='text-align: center; margin-bottom: 2rem; background: linear-gradient(135deg, #2E7D32, #43A047); padding: 2rem; border-radius: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);'>
                    <img src='https://placekitten.com/150/150' alt='Decorative cat image' style='border-radius: 50%; margin-bottom: 1rem; border: 4px solid #FFFFFF; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);'>
                    <h2 style='color: #FFFFFF; margin: 0; font-size: 1.5rem; font-weight: 600;'>Control Center</h2>
                </div>
            </nav>
        """, unsafe_allow_html=True)
        
        selected = option_menu(
            "Navigation",
            ["Content Analysis", "Create Posts", "Auto Schedule", "Post Manager", "Posted Content", "Analytics", "Database Manager"],
            icons=['camera-fill', 'plus-circle-fill', 'calendar-plus-fill', 'calendar-check-fill', 'collection-play-fill', 'graph-up-arrow', 'database-fill'],
            menu_icon="house-door-fill",
            default_index=0,
            styles={
                "container": {
                    "padding": "1.5rem",
                    "background-color": "#C8E6C9",
                    "border-radius": "15px",
                    "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.05)",
                    "border": "1px solid rgba(46, 125, 50, 0.2)"
                },
                "icon": {
                    "color": "#2E7D32",
                    "font-size": "22px",
                    "margin-right": "10px"
                },
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "0.8rem 0",
                    "padding": "0.8rem 1.2rem",
                    "border-radius": "10px",
                    "font-weight": "500",
                    "color": "#1A1A1A",
                    "background-color": "#E8F5E9",
                    "border": "1px solid rgba(46, 125, 50, 0.1)",
                    "transition": "all 0.3s ease",
                },
                "nav-link-selected": {
                    "background": "linear-gradient(135deg, #2E7D32, #43A047)",
                    "color": "#FFFFFF",
                    "font-weight": "600",
                    "box-shadow": "0 2px 4px rgba(0, 0, 0, 0.1)"
                }
            }
        )
    
    if selected == "Content Analysis":
        st.markdown("### Content Analysis")
        
        uploaded_files = st.file_uploader(
            "Upload cat media files",
            accept_multiple_files=True,
            type=['png', 'jpg', 'jpeg', 'mp4', 'mov', 'avi'],
            help="Select image or video files of cats to analyze"
        )
        
        if uploaded_files:
            if st.button("Analyze Content", help="Click to analyze uploaded content"):
                with st.spinner("Analyzing content..."):
                    results = analyze_media(uploaded_files)
                    
                for analysis in results:
                    st.divider()
                    display_analysis_results(analysis)
                    schedule_post(analysis)
    
    elif selected == "Create Posts":
        create_post()
    
    elif selected == "Auto Schedule":
        auto_schedule_posts()
    
    elif selected == "Post Manager":
        st.markdown("### Content Manager")
        manage_pending_posts()
    
    elif selected == "Posted Content":
        view_posted_content()
    
    elif selected == "Analytics":
        st.markdown("### Analytics")
        view_analytics()
    
    elif selected == "Database Manager":
        view_database()

    # Add keyboard instructions
    st.markdown("""
        <div role="complementary" aria-label="Keyboard navigation instructions">
            <h3>Keyboard Navigation</h3>
            <ul>
                <li>Use Tab to move between interactive elements</li>
                <li>Use Enter or Space to activate buttons</li>
                <li>Use Arrow keys to navigate within scrollable regions</li>
                <li>Use Page Up/Down for faster scrolling</li>
                <li>Use Home/End to jump to start/end of scrollable content</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

    # Close main landmark
    st.markdown('</main>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 