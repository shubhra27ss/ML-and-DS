import os
import random
import streamlit as st
import numpy as np
from gtts import gTTS
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import textwrap

def create_text_image(text, background_image=None, width=1280, height=720):
    if background_image and os.path.exists(background_image):
        image = Image.open(background_image).resize((width, height))
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
    tts = gTTS(text=text, lang='en')
    audio_file = "temp_audio.mp3"
    tts.save(audio_file)

    audio_clip = AudioFileClip(audio_file)
    audio_duration = audio_clip.duration

    if not background_images:
        background_images = [None]

    words = text.split()
    segment_size = max(1, len(words) // max(int(audio_duration // 5), 1))

    image_clips = []
    num_images = len(background_images)
    for i in range(0, len(words), segment_size):
        bg_image = background_images[i % num_images]
        segment = ' '.join(words[i:i+segment_size])
        img = create_text_image(segment, background_image=bg_image)
        img_clip = ImageClip(np.array(img)).set_duration(5).fadein(1).fadeout(1)
        image_clips.append(img_clip)

    if image_clips:
        last_clip_duration = audio_duration - sum(clip.duration for clip in image_clips[:-1])
        image_clips[-1] = image_clips[-1].set_duration(last_clip_duration)

    video_clip = concatenate_videoclips(image_clips, method="compose")
    video_clip = video_clip.set_audio(audio_clip)
    video_clip.write_videofile(output_file, codec='libx264', fps=24)
    os.remove(audio_file)
    st.success(f"Video saved as {output_file}")

def create_audio(text, output_file):
    tts = gTTS(text=text, lang='en')
    tts.save(output_file)
    st.success(f"Audio saved as {output_file}")
    st.audio(output_file)

st.title("Text to Video/Audio Generator with Background Images")
text_input = st.text_area("Enter text manually or upload a file")
text_file = st.file_uploader("Or upload a text file", type=["txt"])
background_images = st.file_uploader("Upload background images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
option = st.radio("Select output type", ("Video", "Audio"))

if st.button("Generate Output"):
    text_content = ""
    if text_file:
        text_content = text_file.read().decode("utf-8")
    elif text_input:
        text_content = text_input
    
    if text_content:
        if option == "Video":
            bg_image_paths = []
            for bg_img in background_images:
                bg_path = f"temp_{bg_img.name}"
                with open(bg_path, "wb") as f:
                    f.write(bg_img.read())
                bg_image_paths.append(bg_path)
            create_video(text_content, "output_video.mp4", bg_image_paths)
            st.video("output_video.mp4")
        else:
            create_audio(text_content, "output_audio.mp3")
    else:
        st.error("Please provide text input or upload a file.")
