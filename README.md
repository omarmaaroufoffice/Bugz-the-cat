# Cat Content Analyzer for Instagram 🐱

This application uses Google's Gemini Flash 2.0 AI to analyze your cat photos and videos for Instagram virality potential. It provides detailed scoring, generates captions, suggests hashtags, and creates an optimal posting schedule.

## Features

- Analyzes both images and videos of cats
- Scores content in 5 categories:
  1. Cuteness Factor
  2. Action/Entertainment Value
  3. Uniqueness
  4. Image/Video Quality
  5. Trend Alignment
- Generates engaging captions and relevant hashtags
- Creates an optimal posting schedule
- Exports analysis results to JSON

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root with your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

   To get a Gemini API key:
   1. Go to https://makersuite.google.com/app/apikey
   2. Create or select a project
   3. Click "Create API Key"

## Usage

1. Organize your cat media files (images and videos) in a directory
   - Supported image formats: .jpg, .jpeg, .png
   - Supported video formats: .mp4, .mov, .avi

2. Run the analyzer:
   ```bash
   python cat_content_analyzer.py
   ```

3. Enter the path to your media directory when prompted

4. The program will:
   - Analyze each media file
   - Generate scores and recommendations
   - Create a posting schedule
   - Export results to `content_analysis.json`

## Output

The analyzer provides:
- Individual scores for each category (1-10)
- Total virality score (out of 50)
- AI-generated captions
- Relevant hashtags
- Optimal posting times
- Detailed analysis export in JSON format

## Best Practices

1. Use high-quality images and videos
2. Include a variety of cat content (action shots, cute poses, unique moments)
3. Follow the recommended posting schedule for optimal engagement
4. Review and personalize the AI-generated captions before posting
5. Mix and match suggested hashtags based on your account's strategy

## Notes

- The posting schedule is generated in Eastern Time (ET)
- Videos are analyzed at 1 frame per second
- Analysis results are saved in `content_analysis.json` for future reference 