import os
import random
import numpy as np
import streamlit as st
from gtts import gTTS
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import textwrap
import requests
from io import BytesIO

def create_text_image(text, background_image=None, width=1280, height=720):
    """
    Create an image with wrapped text on a background image.
    """
    if background_image:
        response = requests.get(background_image)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content)).resize((width, height))
        else:
            image = Image.new('RGB', (width, height), color='white')
    else:
        image = Image.new('RGB', (width, height), color='white')

    image = image.convert("RGBA")
    draw = ImageDraw.Draw(image)

    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ]

    font = None
    for font_path in font_paths:
        try:
            font = ImageFont.truetype(font_path, 32)
            break
        except IOError:
            continue

    if font is None:
        font = ImageFont.load_default()

    wrapped_text = textwrap.fill(text, width=30)
    text_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    position = ((width - text_width) / 2, (height - text_height) / 2)
    padding = 20
    text_bg_bbox = (
        position[0] - padding,
        position[1] - padding,
        position[0] + text_width + padding,
        position[1] + text_height + padding
    )
    draw.rectangle(text_bg_bbox, fill=(255, 255, 255, 180))
    draw.multiline_text(position, wrapped_text, font=font, fill=(255, 0, 0), align='center')

    return image

def create_video(text, output_file, background_images=None):
    """
    Create a video from text with dynamic text images and background images.
    """
    tts = gTTS(text=text, lang='en')
    audio_file = "temp_audio.mp3"
    tts.save(audio_file)

    audio_clip = AudioFileClip(audio_file)
    audio_duration = audio_clip.duration

    if not background_images:
        background_images = [None]

    words = text.split()
    segment_size = len(words) // max(int(audio_duration // 5), 1)

    image_clips = []
    for i in range(0, len(words), segment_size):
        bg_image = random.choice(background_images)
        segment = ' '.join(words[i:i+segment_size])
        img = create_text_image(segment, background_image=bg_image)
        img_clip = ImageClip(np.array(img)).set_duration(5)
        image_clips.append(img_clip)

    if image_clips:
        last_clip_duration = audio_duration - sum(clip.duration for clip in image_clips[:-1])
        image_clips[-1] = image_clips[-1].set_duration(last_clip_duration)

    video_clip = concatenate_videoclips(image_clips)
    video_clip = video_clip.set_audio(audio_clip)
    video_clip.write_videofile(output_file, codec='libx264', fps=24)

    os.remove(audio_file)
    return output_file

# Streamlit UI
st.title("Text-to-Video Generator with Background Images")

text_input = st.text_area("Enter your text")
background_urls = st.text_area("Enter background image URLs (comma-separated)")

if st.button("Generate Video") and text_input:
    bg_image_paths = [url.strip() for url in background_urls.split(',') if url.strip()]
    output_video = "generated_video.mp4"
    create_video(text_input, output_video, bg_image_paths)
    st.video(output_video)
