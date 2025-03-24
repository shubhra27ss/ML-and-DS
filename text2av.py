import os
import random
import streamlit as st
import numpy as np
from gtts import gTTS
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import textwrap
from PIL.Image import Resampling  # Modern resampling method

def create_text_image(text, background_image=None, width=1280, height=720):
    """Create an image with text overlay on background"""
    if background_image and os.path.exists(background_image):
        image = Image.open(background_image).resize((width, height), Resampling.LANCZOS)
    else:
        image = Image.new('RGB', (width, height), color='white')

    image = image.convert("RGBA")
    draw = ImageDraw.Draw(image)

    # Try different fonts
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

    # Format text
    wrapped_text = textwrap.fill(text, width=30)
    text_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Position text
    position = ((width - text_width) / 2, (height - text_height) / 2)
    padding = 20
    text_bg_bbox = (
        position[0] - padding,
        position[1] - padding,
        position[0] + text_width + padding,
        position[1] + text_height + padding
    )
    
    # Add semi-transparent background for text
    draw.rectangle(text_bg_bbox, fill=(255, 255, 255, 180))
    draw.multiline_text(position, wrapped_text, font=font, fill=(255, 0, 0), align='center')

    return image

def create_video(text, output_file, background_images=None):
    """Create video with text and background images"""
    # Generate audio
    tts = gTTS(text=text, lang='en')
    audio_file = "temp_audio.mp3"
    tts.save(audio_file)
    audio_clip = AudioFileClip(audio_file)
    audio_duration = audio_clip.duration

    if not background_images:
        background_images = [None]

    # Calculate segment durations
    num_images = len(background_images)
    segment_duration = audio_duration / num_images

    # Create clips for each background
    image_clips = []
    for i, bg_image in enumerate(background_images):
        # Split text proportionally
        words = text.split()
        start_idx = int(i * len(words) / num_images)
        end_idx = int((i + 1) * len(words) / num_images)
        segment = ' '.join(words[start_idx:end_idx])
        
        # Create image with text
        img = create_text_image(segment, background_image=bg_image)
        img_array = np.array(img)
        
        # Create clip with simple fade effects
        img_clip = ImageClip(img_array).set_duration(segment_duration)
        img_clip = img_clip.fadein(0.5).fadeout(0.5)
        
        image_clips.append(img_clip)

    # Combine all clips
    video_clip = concatenate_videoclips(image_clips, method="compose")
    video_clip = video_clip.set_audio(audio_clip)
    
    # Write video file
    video_clip.write_videofile(output_file, codec='libx264', fps=24, threads=4)
    os.remove(audio_file)
    st.success(f"Video saved as {output_file}")

def create_audio(text, output_file):
    """Create audio only version"""
    tts = gTTS(text=text, lang='en')
    tts.save(output_file)
    st.success(f"Audio saved as {output_file}")
    st.audio(output_file)

# Streamlit UI
st.title("Text to Video/Audio Generator with Background Images")

# Input options
text_input = st.text_area("Enter text manually or upload a file and press Enter", height=200)
text_file = st.file_uploader("Or upload a text file", type=["txt"])
background_images = st.file_uploader("Upload background images", 
                                   type=["jpg", "jpeg", "png"], 
                                   accept_multiple_files=True)
option = st.radio("Select output type", ("Video", "Audio"))

def process_text_input():
    """Get text from either input or file"""
    if text_file:
        return text_file.read().decode("utf-8")
    return text_input if text_input else ""

if st.button("Generate Output"):
    text_content = process_text_input()
    
    if not text_content:
        st.error("Please provide text input or upload a file.")
    else:
        if option == "Video":
            # Save uploaded background images temporarily
            bg_image_paths = []
            for bg_img in background_images:
                bg_path = f"temp_{bg_img.name}"
                with open(bg_path, "wb") as f:
                    f.write(bg_img.getbuffer())
                bg_image_paths.append(bg_path)
            
            create_video(text_content, "output_video.mp4", bg_image_paths)
            
            # Display and cleanup
            st.video("output_video.mp4")
            for bg_path in bg_image_paths:
                if os.path.exists(bg_path):
                    os.remove(bg_path)
        else:
            create_audio(text_content, "output_audio.mp3")
