from yt_dlp import YoutubeDL
import os
import re
import sys
import requests
import logging
from myai import transcribe_it
            
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("main")

def extract_video_id(url_or_id):
    """Extract video ID from URL or return the ID if it's already just an ID."""
    patterns = [
        r'(?:v=|/)([\w-]{11})(?:\?|&|/|$)',  # Regular YouTube URLs
        r'^([\w-]{11})$'  # Direct video ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return None

def download_subtitle(video_id, preferred_langs=['en']):
    info_opts = {
        'quiet': True,
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,  # 若無手動字幕則下載自動字幕
        'subtitleslangs': preferred_langs,  # 指定字幕語言（可調整）
        'subtitlesformat': 'json3',  # 使用json3 (srv3) 格式
    }
            
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    with YoutubeDL(info_opts) as ydl:
        video_info = ydl.extract_info(video_url, download=False)
        
    title = video_info.get('title')
    upload_date = video_info.get('upload_date')
    formatted_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}" if upload_date else '未知日期'

    logger.info(f"影片標題：{title}")
    logger.info(f"上傳日期：{formatted_date}")

    selected_lang = 'en'
    subtitles = video_info.get('subtitles', {}) or video_info.get('automatic_captions', {})
    if not subtitles or selected_lang not in subtitles:
        logger.warning(f"無可用字幕：{video_id}")
        return "", ""
        
    sub_url = subtitles[selected_lang][0]['url']
    subtitle_json = requests.get(sub_url).json()

    # 從JSON中抽取完整句子且避免重複
    subtitle_text = ''
    last_text = ''
    for event in subtitle_json['events']:
        if 'segs' in event:
            line_text = ''.join(seg.get('utf8', '') for seg in event['segs']).strip()
            
            # 避免重複
            if line_text and line_text != last_text:
                line_text = re.sub(r'\s+', ' ', line_text).strip() 
                subtitle_text += line_text + '\n'
                last_text = line_text

    return subtitle_text, formatted_date


def download_youtube(video_id):
    """Download first available YouTube transcript if it doesn't exist."""
    transcript_dir = "transcript"
    transcript_path = os.path.join(transcript_dir, f"{video_id}.txt")
    
    # Create transcript directory if it doesn't exist
    if not os.path.exists(transcript_dir):
        os.makedirs(transcript_dir)
    
    # Check if transcript already exists
    if os.path.exists(transcript_path):
        logger.info(f"Transcript already exists for video {video_id}")
        return

    try:
        subtitle_text, formatted_date = download_subtitle(video_id)
        if subtitle_text:
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(subtitle_text)
            logger.info(f"Successfully downloaded transcript for {video_id}")
        else:
            logger.warning(f"No subtitle content available for {video_id}")
    except Exception as e:
        logger.error(f"Error downloading transcript: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python run.py <video_id>")
        sys.exit(1)
    
    url_or_id = sys.argv[1]
    video_id = extract_video_id(url_or_id)
    
    if not video_id:
        logger.error("Invalid YouTube URL or video ID")
        sys.exit(1)
    
    download_youtube(video_id)
    transcribe_it(video_id)

if __name__ == "__main__":
    main()
