import streamlit as st
from gtts import gTTS
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont, ImageOps
from PIL.Image import Resampling  # Add this import
import tempfile
import os
import textwrap
import numpy as np
import random
from moviepy.video.fx import all as vfx
import requests
from io import BytesIO

# Set page config
st.set_page_config(
    page_title="Text-to-Video Generator",
    page_icon="🎬",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    .stTextArea textarea {
        min-height: 200px;
    }
    .stButton button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
    }
    .stDownloadButton button {
        width: 100%;
        background-color: #2196F3;
        color: white;
    }
    .stSelectbox div {
        margin-bottom: 15px;
    }
    .css-1v0mbdj {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

def get_random_image(query, width=1280, height=720):
    """Get random image from Unsplash without API key"""
    try:
        url = f"https://source.unsplash.com/random/{width}x{height}/?{query}"
        response = requests.get(url, timeout=10)
        img = Image.open(BytesIO(response.content))
        return img
    except:
        return None

def create_gradient_background(width=1280, height=720):
    """Create colorful gradient background"""
    bg = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(bg)
    for y in range(height):
        color = (
            int(y/height*255),
            random.randint(0, 255),
            255-int(y/height*255)
        )
        draw.line([(0, y), (width, y)], fill=color)
    return bg

def generate_audio(text):
    """Generate audio from text"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
        tts = gTTS(text=text, lang='en')
        tts.save(fp.name)
        return fp.name

def create_text_clip(text, duration, width=1280, height=720, bg_image=None, add_effects=True):
    """Create a text clip with background"""
    # Create background
    if bg_image:
        img = bg_image.resize((width, height), Resampling.LANCZOS)  # Updated resampling method
    else:
        img = create_gradient_background(width, height)
    
    # Create text overlay
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    try:
        # Try to load a nice font (fallback to default if not available)
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = ImageFont.load_default()
    
    wrapped_text = textwrap.fill(text, width=40)
    text_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    position = ((width - text_width) / 2, (height - text_height) / 2)
    
    # Add semi-transparent background for text
    padding = 20
    draw.rectangle(
        [position[0]-padding, position[1]-padding,
         position[0]+text_width+padding, position[1]+text_height+padding],
        fill=(0, 0, 0, 180)
    )
    
    # Add text
    draw.multiline_text(
        position, 
        wrapped_text, 
        font=font, 
        fill=(255, 255, 255), 
        align='center'
    )
    
    # Combine background and text
    img = img.convert("RGBA")
    final_img = Image.alpha_composite(img, overlay)
    
    # Convert to numpy array for MoviePy
    img_array = np.array(final_img)
    clip = ImageClip(img_array).set_duration(duration)
    
    # Add effects
    if add_effects:
        clip = clip.fx(vfx.resize, lambda t: 1 + 0.01 * t)  # Zoom effect
        clip = clip.fadein(0.5)  # Fade in
        clip = clip.set_position(lambda t: ('center', 360 + 5*np.sin(t*2)))  # Subtle movement
    
    return clip

def generate_video(text, background_style, add_effects=True):
    """Generate video with smart background selection"""
    audio_path = generate_audio(text)
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration
    
    # Split text into meaningful chunks
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    if not sentences:
        sentences = [text]
    
    clips = []
    for i, sentence in enumerate(sentences):
        # Get relevant image
        bg_image = None
        if background_style != "Gradient":
            if background_style == "Contextual":
                bg_image = get_random_image(sentence.split()[0])  # Use first word as query
            else:
                bg_image = get_random_image(background_style.lower())
        
        # Calculate duration for this segment
        clip_duration = min(len(sentence.split()) * 0.5, 10)  # Max 10s per clip
        if i == len(sentences)-1:
            clip_duration = duration - sum(clip.duration for clip in clips[:-1])
        
        # Create clip
        clip = create_text_clip(
            sentence, 
            clip_duration, 
            bg_image=bg_image,
            add_effects=add_effects
        )
        
        # Add transition
        if i > 0:
            clip = clip.crossfadein(0.5)
        
        clips.append(clip)
    
    # Combine clips
    video_clip = concatenate_videoclips(clips, method="compose")
    video_clip = video_clip.set_audio(audio_clip)
    return video_clip, audio_path

def main():
    st.title("🎥 Text-to-Video Generator")
    st.markdown("Create videos from text with beautiful backgrounds")
    
    # Text input
    text = st.text_area("Enter your text:", placeholder="Type or paste your text here...", height=250)
    
    # Video options
    background_style = st.selectbox(
        "Background style:",
        ["Contextual", "Nature", "City", "Technology", "Abstract", "Gradient"],
        help="'Contextual' tries to match your text content"
    )
    
    add_effects = st.checkbox("Enable animations", value=True)
    
    if st.button("Generate Video", type="primary"):
        if not text.strip():
            st.warning("Please enter some text first.")
        else:
            with st.spinner("Creating your video..."):
                try:
                    # Generate and display video
                    video_clip, audio_path = generate_video(text, background_style, add_effects)
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as video_fp:
                        video_clip.write_videofile(
                            video_fp.name, 
                            codec='libx264', 
                            fps=24,
                            threads=4,
                            preset='ultrafast'
                        )
                        
                        # Display video
                        st.video(video_fp.name)
                        
                        # Download button
                        with open(video_fp.name, "rb") as f:
                            st.download_button(
                                "Download Video",
                                f,
                                file_name="output.mp4",
                                mime="video/mp4"
                            )
                    
                    # Clean up
                    os.unlink(video_fp.name)
                    os.unlink(audio_path)
                    
                    st.success("Video created successfully! 🎉")
                
                except Exception as e:
                    st.error(f"Error generating video: {str(e)}")

if __name__ == "__main__":
    main()
