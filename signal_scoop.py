# Quietly install necessary packages
!pip install -q gradio google-api-python-client pandas

import gradio as gr
import pandas as pd
from googleapiclient.discovery import build
import urllib.parse as urlparse
import io

def get_video_id(url):
    """Extracts the video ID from various YouTube URL formats."""
    parsed_url = urlparse.urlparse(url)
    if parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            return urlparse.parse_qs(parsed_url.query)['v'][0]
        if parsed_url.path[:7] == '/embed/':
            return parsed_url.path.split('/')[2]
        if parsed_url.path[:3] == '/v/':
            return parsed_url.path.split('/')[2]
    return None

def fetch_all_comments(api_key, video_url):
    if not api_key or not video_url:
        return "Please provide both an API Key and a Video URL.", None

    video_id = get_video_id(video_url)
    if not video_id:
        return "Invalid YouTube URL format.", None

    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        comments_data = []
        next_page_token = None

        while True:
            # Request comment threads
            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                pageToken=next_page_token,
                textFormat="plainText"
            )
            response = request.execute()

            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments_data.append({
                    "Author": comment.get("authorDisplayName"),
                    "Comment": comment.get("textDisplay"),
                    "Likes": comment.get("likeCount"),
                    "Published At": comment.get("publishedAt"),
                    "Updated At": comment.get("updatedAt"),
                    "Author Channel URL": comment.get("authorChannelUrl")
                })

            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break

        df = pd.DataFrame(comments_data)

        # Save to temporary CSV for download
        csv_file = "youtube_comments.csv"
        df.to_csv(csv_file, index=False)

        return df, csv_file

    except Exception as e:
        return f"Error: {str(e)}", None

# --- Gradio Interface ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎥 YouTube Comment Extractor")
    gr.Markdown("Enter your YouTube Data API v3 Key and a Video URL to fetch all comments into a DataFrame.")

    with gr.Row():
        api_input = gr.Textbox(label="YouTube API Key", placeholder="Paste your API key here...", type="password")
        url_input = gr.Textbox(label="Video URL", placeholder="https://www.youtube.com/watch?v=...")

    fetch_btn = gr.Button("Fetch All Comments", variant="primary")

    output_df = gr.DataFrame(label="Extracted Comments")
    download_file = gr.File(label="Download CSV")

    fetch_btn.click(
        fn=fetch_all_comments,
        inputs=[api_input, url_input],
        outputs=[output_df, download_file]
    )

demo.launch(debug=True)
