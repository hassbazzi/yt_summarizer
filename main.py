import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
import os
from prompts import SYSTEM_PROMPT, USER_PROMPT

# Function to get video details based on the URL provided by the user
def get_video_details(url):
    ydl_opts = {}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        video_title = info_dict.get('title', None)
        video_description = info_dict.get('description', None)
        video_duration = info_dict.get('duration', None)
        video_chapters = info_dict.get('chapters', None)
        return video_title, video_description, video_duration, video_chapters

# Function to get the video URL from the user and return details about the video
def get_video_url():
    url = input("Please enter the YouTube video URL: ") # This is a built-in Python function that lets us get input from the user.
    return url
    title, description, duration, chapters = get_video_details(video_url)
    print(f"Title: {title}")
    print(f"Description: {description}")
    print(f"Duration: {duration} seconds")
    print(f"Chapters: {chapters}")

# Function to get the transcript from the YouTube video by extracting the video ID
def get_transcript(video_url):
    try:
        if 'v=' in video_url:
            video_id = video_url.split('v=')[1].split('&')[0]
        else:
            video_id = video_url.split('/')[-1].split('?')[0]
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Function to split the transcript by chapters if available
def split_transcript_by_chapters(transcript, chapters):
    chapter_transcripts = []
    for chapter in chapters:
        start_time = chapter['start_time']
        end_time = chapter.get('end_time', float('inf'))
        chapter_text = []
        for entry in transcript:
            if start_time <= entry['start'] < end_time:
                chapter_text.append(entry['text'])
        chapter_transcripts.append(' '.join(chapter_text))
    return chapter_transcripts

# Function to count the tokens in the transcript
def summarize_text(text):
    try:
        client = OpenAI()
        
        # Format the user prompt with the transcript or chapter content
        user_prompt = USER_PROMPT.format(text=text)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.strip()},
                {"role": "user", "content": user_prompt.strip()}
            ],
            max_tokens=1000  # Adjust based on how much summary you want
        )
        summary = response.choices[0].message.content
        return summary.strip()
    except Exception as e:
        print(f"An error occurred while summarizing: {e}")
        return None

# Function to save the summary to a markdown file
def save_summary_to_markdown(title, summary):
    # Clean the title to create a safe filename
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"{safe_title}.md"
    
    # Write the summary to the markdown file
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(summary)
    
    print(f"Summary saved to {filename}")

# Main function to run the program
if __name__ == "__main__":
    video_url = get_video_url()
    title, description, duration, chapters = get_video_details(video_url)
    print(f"Title: {title}")
    print(f"Description: {description}")
    print(f"Duration: {duration} seconds")
    print(f"Chapters: {chapters}")

    transcript = get_transcript(video_url)
    if transcript:
        print("Transcript fetched successfully!")
        
        if chapters:
            print("Video has chapters. Summarizing each chapter separately.")
            chapter_transcripts = split_transcript_by_chapters(transcript, chapters)
            all_summaries = []
            for i, chapter_text in enumerate(chapter_transcripts):
                print(f"Summarizing Chapter {i+1}...")
                summary = summarize_text(chapter_text)
                if summary:
                    all_summaries.append(f"## Chapter {i+1}: {chapters[i]['title']}\n\n{summary}\n")
                    print(f"Summary for Chapter {i+1}:\n{summary}\n")
                else:
                    print(f"Failed to summarize Chapter {i+1}.")
            
            # Combine all chapter summaries into one markdown document
            full_summary = "\n".join(all_summaries)
            save_summary_to_markdown(title, full_summary)

        else:
            print("Video has no chapters. Summarizing entire transcript.")
            full_transcript = ' '.join([entry['text'] for entry in transcript])
            summary = summarize_text(full_transcript)
            if summary:
                save_summary_to_markdown(title, summary)
            else:
                print("Failed to summarize the full transcript.")
    else:
        print("No transcript available for this video.")
