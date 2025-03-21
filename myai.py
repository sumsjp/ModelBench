from openai import OpenAI
import google.generativeai as genai
from dotenv import load_dotenv
import os
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")


load_dotenv()

prompt = '''
您是個專業的研究員，可幫忙整理學術文獻的重要內容。
1. 請你務必**用中文回答**，除人名與專有名詞外，不要使用英文。
2. 整理學術文獻，會使用正式的學術用語。
3. 提供清晰、客觀的文獻總結時，會使用正式的學術用語。
4. 歸納文獻的主要重點，包括主題、觀念、原因、解決方案、結論和建議。
5. 提供清楚的、目標性的、正確的重點總結。
6. 避免個人意見和推浮，是一個可信賴的工具，用于整理各個領域的複雜學術內容，非常適於研究人員、學生和學術人士。
'''

template = '''
===== 文章開始 =====

{text}

===== 文章結束 =====

請整理此文章重點，使用正式的學術用語，並以小節作歸納。
將原文章用中文重寫，用中文列出詳細重點，作清楚客觀的整理。
'''

# MODEL = 'deepseek-r1:14b'
MODEL = 'gemma3:27b'


def transcribe_it(video_id):
    transcript_path = os.path.join("transcript", f"{video_id}.txt")
    result_dir = "result"
    
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
        
    if os.path.exists(transcript_path):
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript_text = f.read()
                
            for model in ["A", "B"]:
                for ptype in [1]:
                    import time
                    start_time = time.time()
                    
                    if model == "A":
                        summary = chat_with_gemini(transcript_text)
                    else:
                        summary = chat_with_openai(transcript_text)
                        
                    elapsed_time = time.time() - start_time
                    logger.info(f"Model {model} took {elapsed_time:.2f} seconds")

                    # Save the summary
                    output_path = os.path.join(result_dir, f"{video_id}_{ptype}{model}.txt")
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(f"Model = {model}\n---\n\n")
                        f.write(f"elapsed_time = {elapsed_time:.2f}\n---\n\n")
                        f.write(f"prompt = {prompt}\n---\n\n")
                        f.write(f"template = {template}\n---\n\n")
                        f.write(summary)
                    logger.info(f"Summary saved to {output_path}")
                    
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
    else:
        logger.error(f"Transcript file not found: {transcript_path}")

def chat_with_gemini(message):
    try:
        # Configure the model
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        
        # Create the model instance
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        content = template.format(text=message)
        
        # Create a chat instance
        chat = model.start_chat(history=[])
        
        # Add system prompt
        chat.send_message(prompt)
        
        # Send the content and get response
        response = chat.send_message(content)
        
        summary = response.text.strip()
        
        # Handle </think> tag if present
        if '</think>' in summary:
            last_think_pos = summary.rindex('</think>')
            summary = summary[last_think_pos + 8:].lstrip()
            
        return summary
        
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def chat_with_openai(message):
    client = OpenAI(
        api_key='ollama',
        base_url='http://solarsuna.com:34567/v1'
    )
    
    try:
        content = template.format(text=message)
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": content
                }
            ],
            max_tokens=15000,
            temperature=0.7
        )
        
        summary = response.choices[0].message.content.strip()
        
        # Handle </think> tag if present
        if '</think>' in summary:
            last_think_pos = summary.rindex('</think>')
            summary = summary[last_think_pos + 8:].lstrip()
            
        return summary
        
    except Exception as e:
        return f"Error generating summary: {str(e)}"
