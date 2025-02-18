import streamlit as st
import os
from pathlib import Path
import json
from datetime import datetime, timedelta
import pytz
from streamlit_option_menu import option_menu
import pandas as pd
from cat_content_analyzer import CatContentAnalyzer
from PIL import Image
import io
import sqlite3

# Set page config
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

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
    }
    .stTextArea>div>div>textarea {
        font-size: 14px;
    }
    .stDataFrame {
        font-size: 14px;
    }
    .css-1d391kg {
        padding-top: 1rem;
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
    file_path = Path(file_path)
    if not file_path.exists():
        st.error(f"Media file not found: {file_path}")
        return
    
    if file_path.suffix.lower() in ['.mp4', '.mov', '.avi']:
        return st.video(str(file_path))
    else:
        return st.image(str(file_path))

def analyze_media(uploaded_files):
    """Analyze uploaded media files."""
    results = []
    for file in uploaded_files:
        # Save the file temporarily
        temp_path = Path("temp") / f"temp_{file.name}"
        temp_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure temp directory exists
        
        try:
            # Save the file
            with open(temp_path, "wb") as f:
                f.write(file.getbuffer())
            
            # Analyze the file
            analysis = st.session_state.analyzer.analyze_media(str(temp_path))
            analysis['original_filename'] = file.name
            analysis['file_path'] = str(temp_path)  # Store the full path
            results.append(analysis)
            st.session_state.analyzed_content.append(analysis)
        except Exception as e:
            st.error(f"Error analyzing {file.name}: {e}")
            if temp_path.exists():
                temp_path.unlink()  # Clean up on error
    
    return results

def display_analysis_results(analysis):
    """Display analysis results in a structured format."""
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.subheader("Media Info")
        load_and_display_media(analysis['file_path'])
        st.write(f"File: {analysis['original_filename']}")
        st.write(f"Type: {analysis['media_type']}")
    
    with col2:
        st.subheader("Analysis Results")
        
        # Display scores
        scores_df = pd.DataFrame(
            analysis['scores'].items(),
            columns=['Category', 'Score']
        )
        st.write("Category Scores:")
        st.dataframe(scores_df, use_container_width=True)
        
        st.write(f"Total Score: {analysis['total_score']}/50")
        
        # Display generated content
        st.write("Generated Caption:")
        st.text_area("Caption", analysis['caption'], key=f"caption_{analysis['file_path']}")
        
        st.write("Hashtags:")
        st.text_area("Hashtags", analysis['hashtags'], key=f"hashtags_{analysis['file_path']}")
        
        # Display platform-specific tips
        with st.expander("Engagement Tips"):
            st.write(analysis['engagement_tips'])
        
        with st.expander("Key Strengths"):
            st.write(analysis['key_strengths'])
        
        with st.expander("Improvement Suggestions"):
            st.write(analysis['improvement_suggestions'])

def schedule_post(analysis):
    """Add post to pending schedule."""
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
    
    if st.button("Schedule Post", key=f"schedule_{analysis['file_path']}"):
        scheduled_post = {
            'analysis': analysis,
            'platforms': platforms,
            'scheduled_time': post_datetime,
            'status': 'pending'
        }
        st.session_state.pending_posts.append(scheduled_post)
        st.success("Post scheduled successfully!")

def manage_pending_posts():
    """Manage and approve pending posts."""
    if not st.session_state.pending_posts:
        st.info("No pending posts.")
        return
    
    st.subheader("Pending Posts")
    for i, post in enumerate(st.session_state.pending_posts):
        with st.expander(f"Post {i+1}: {post['analysis']['original_filename']}"):
            col1, col2 = st.columns([2, 3])
            
            with col1:
                load_and_display_media(post['analysis']['file_path'])
            
            with col2:
                st.write("Scheduled for:", post['scheduled_time'])
                platforms = post['platforms']
                st.write("Platforms:", ", ".join(platforms))
                st.write("Caption:", post['analysis']['caption'])
                st.write("Hashtags:", post['analysis']['hashtags'])
                
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
                    platforms.remove('tiktok')  # Remove TikTok from automated posting
                
                if platforms:  # If there are other platforms to post to
                    if st.button("Post to Other Platforms", key=f"post_now_{i}"):
                        try:
                            results = st.session_state.analyzer.post_to_social_media(
                                post['analysis'],
                                platforms
                            )
                            
                            success = all(results.values())
                            if success:
                                st.success("Posted successfully to other platforms!")
                                st.session_state.posted_content.append(post)
                                st.session_state.pending_posts.pop(i)
                            else:
                                failed_platforms = [p for p, r in results.items() if not r]
                                st.error(f"Failed to post to: {', '.join(failed_platforms)}")
                        except Exception as e:
                            st.error(f"Error posting: {e}")
                            
                if 'tiktok' in post['platforms']:
                    if st.button("Mark TikTok as Posted", key=f"tiktok_done_{i}"):
                        st.success("TikTok post marked as completed!")
                        if not platforms:  # If no other platforms were pending
                            st.session_state.posted_content.append(post)
                            st.session_state.pending_posts.pop(i)

def view_analytics():
    """View analytics and posting history."""
    if not st.session_state.posted_content:
        st.info("No posted content yet.")
        return
    
    st.subheader("Posting History")
    
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
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Posts", len(df))
    with col2:
        st.metric("Average Score", f"{df['Total Score'].mean():.1f}")
    with col3:
        st.metric("Images", len(df[df['Media Type'] == 'image']))
    with col4:
        st.metric("Videos", len(df[df['Media Type'] == 'video']))
    
    # Display posting history
    st.subheader("Recent Posts")
    st.dataframe(df, use_container_width=True)
    
    # Platform distribution
    st.subheader("Platform Distribution")
    platform_counts = df['Platforms'].str.split(", ").explode().value_counts()
    st.bar_chart(platform_counts)
    
    # Database Analytics
    st.subheader("Database Analytics")
    
    # Get posting history from database
    posting_history = st.session_state.analyzer.get_posting_history()
    if posting_history:
        history_df = pd.DataFrame(
            posting_history,
            columns=['Filename', 'Platform', 'Status', 'Posted At']
        )
        
        # Display success rate by platform
        st.write("Success Rate by Platform")
        success_rate = history_df.groupby('Platform')['Status'].apply(
            lambda x: (x == 'success').mean() * 100
        ).round(1)
        success_df = pd.DataFrame({
            'Platform': success_rate.index,
            'Success Rate (%)': success_rate.values
        })
        st.dataframe(success_df, use_container_width=True)
        
        # Display recent posting activity
        st.write("Recent Posting Activity")
        st.dataframe(
            history_df.sort_values('Posted At', ascending=False).head(10),
            use_container_width=True
        )
        
        # Show posting activity over time
        st.write("Posting Activity Over Time")
        history_df['Posted At'] = pd.to_datetime(history_df['Posted At'])
        daily_posts = history_df.resample('D', on='Posted At').size()
        st.line_chart(daily_posts)

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

def main():
    st.title("🐱 Cat Content Control Center")
    
    # Cleanup old temp files
    def cleanup_old_temp_files():
        """Clean up temporary files older than 24 hours."""
        temp_dir = Path("temp")
        if temp_dir.exists():
            current_time = datetime.now()
            for temp_file in temp_dir.glob("temp_*"):
                file_age = current_time - datetime.fromtimestamp(temp_file.stat().st_mtime)
                # Only delete files older than 24 hours and not in current session
                if file_age > timedelta(hours=24) and str(temp_file) not in [
                    analysis.get('file_path') for analysis in st.session_state.analyzed_content
                ]:
                    try:
                        temp_file.unlink()
                    except Exception as e:
                        print(f"Error cleaning up {temp_file}: {e}")
    
    # Run cleanup at startup
    cleanup_old_temp_files()
    
    # Sidebar navigation
    with st.sidebar:
        selected = option_menu(
            "Navigation",
            ["Content Analysis", "Post Management", "Analytics", "Database Management"],
            icons=['camera-fill', 'calendar-check-fill', 'graph-up-arrow', 'database-fill'],
            menu_icon="house-door-fill",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "black", "font-size": "20px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#eee",
                },
                "nav-link-selected": {"background-color": "#0083B8"},
            }
        )
    
    if selected == "Content Analysis":
        st.header("Content Analysis")
        
        uploaded_files = st.file_uploader(
            "Upload cat media files",
            accept_multiple_files=True,
            type=['png', 'jpg', 'jpeg', 'mp4', 'mov', 'avi']
        )
        
        if uploaded_files:
            if st.button("Analyze Content"):
                with st.spinner("Analyzing content..."):
                    results = analyze_media(uploaded_files)
                    
                for analysis in results:
                    st.divider()
                    display_analysis_results(analysis)
                    schedule_post(analysis)
    
    elif selected == "Post Management":
        st.header("Post Management")
        manage_pending_posts()
    
    elif selected == "Analytics":
        st.header("Analytics")
        view_analytics()
    
    elif selected == "Database Management":
        view_database()

if __name__ == "__main__":
    main() 