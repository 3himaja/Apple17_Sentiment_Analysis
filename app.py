# 1. INSTALL DEPENDENCIES
!pip install gradio supabase vaderSentiment pandas matplotlib

import gradio as gr
import pandas as pd
import matplotlib.pyplot as plt
from supabase import create_client
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# 2. SUPABASE CONFIGURATION
# Copy these from your Supabase Settings > API
SUPABASE_URL = "https://hdzfnimpvqmjjzaacezp.supabase.co"
SUPABASE_KEY = "sb_secret_Uyw-K1x-VXykoo2ETrZifA_LRKj39bm"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

analyzer = SentimentIntensityAnalyzer()

def get_analysis():
    try:
        # Fetching data exactly as per your SQL schema
        response = supabase.table("comments").select("*").execute()
        df = pd.DataFrame(response.data)

        if df.empty:
            return None, "No data found in Supabase. Please check your upload.", None

        # --- SENTIMENT ANALYSIS ---
        # Using 'comment' column as per your SQL 'CREATE TABLE'
        df['sentiment_score'] = df['comment'].apply(lambda x: analyzer.polarity_scores(str(x))['compound'])
        
        # --- VISUALIZATION: SENTIMENT OVER TIME ---
        # Using 'published_at' column as per your SQL schema
        df['published_at'] = pd.to_datetime(df['published_at'])
        df_sorted = df.sort_values('published_at')
        
        plt.figure(figsize=(10, 5))
        # Rolling average to visualize the "Vibe" trend
        plt.plot(df_sorted['published_at'], df_sorted['sentiment_score'].rolling(window=15, min_periods=1).mean(), 
                 color='#1DA1F2', linewidth=2.5, label="Sentiment Trend")
        plt.axhline(0, color='red', linestyle='--', alpha=0.3)
        plt.title("iPhone 17 Market Sentiment Pulse", fontsize=14)
        plt.xlabel("Timeline of Reviews")
        plt.ylabel("Sentiment Score (Positive 1 to -1 Negative)")
        plt.legend()
        plt.grid(True, alpha=0.2)
        plt.tight_layout()
        plt.savefig("pulse_chart.png")
        plt.close()

        # --- DRILL-DOWN: TOP 2 POSITIVE & NEGATIVE ---
        # Selecting Author, Comment, and Score for the report
        top_pos = df.nlargest(2, 'sentiment_score')[['author', 'comment', 'sentiment_score']]
        top_neg = df.nsmallest(2, 'sentiment_score')[['author', 'comment', 'sentiment_score']]
        
        return "pulse_chart.png", top_pos, top_neg

    except Exception as e:
        return None, f"Error: {str(e)}", None

# 3. GRADIO UI DESIGN
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📱 iPhone 17 Signal-to-Strategy Portal")
    gr.Markdown("Analyzing live YouTube signals directly from your Supabase Database.")
    
    with gr.Row():
        btn = gr.Button("🚀 Run Sentiment Analysis", variant="primary")
    
    with gr.Tab("Market Pulse"):
        plot_out = gr.Image(label="Sentiment Timeline")
        
    with gr.Tab("Strategic Drill-Down"):
        gr.Markdown("### 🌟 Top 2 Most Positive Signals")
        pos_out = gr.DataFrame(headers=["Author", "Comment", "Score"])
        gr.Markdown("### 📉 Top 2 Most Negative Signals")
        neg_out = gr.DataFrame(headers=["Author", "Comment", "Score"])

    btn.click(get_analysis, outputs=[plot_out, pos_out, neg_out])

# 4. LAUNCH
demo.launch(share=True, debug=True)
