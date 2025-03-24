import streamlit as st
from gtts import gTTS
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont, ImageOps
import tempfile
import os
import textwrap
import numpy as np
import random
from moviepy.video.fx import all as vfx

# Set page config
st.set_page_config(
    page_title="Enhanced Text to Video Converter",
    page_icon="🎬",
    layout="centered"
)

# Custom CSS for better appearance
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
    .stRadio div {
        flex-direction: row;
    }
    .stRadio label {
        margin-right: 20px;
    }
    .stSelectbox div {
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Background options (you'll need to provide these images)
BACKGROUND_OPTIONS = {
    "Nature": "nature.jpg",
    "City": "city.jpg",
    "Abstract": "abstract.jpg",
    "Technology": "tech.jpg",
    "Gradient": None  # For gradient background
}

def generate_audio(text):
    """Generate audio from text"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
        tts = gTTS(text=text, lang='en')
        tts.save(fp.name)
        return fp.name

def create_text_clip(text, duration, width=1280, height=720, bg_image=None, add_effects=True):
    """Create a text clip with optional background image and effects"""
    # Create background
    if bg_image and os.path.exists(bg_image):
        bg = Image.open(bg_image).resize((width, height))
    else:
        # Create gradient background if no image provided
        bg = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(bg)
        for y in range(height):
            color = (0, int(y/height*255), 255-int(y/height*255))
            draw.line([(0, y), (width, y)], fill=color)
    
    # Create text overlay
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = ImageFont.load_default()
    
    wrapped_text = textwrap.fill(text, width=30)
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
    
    # Add text with white color
    draw.multiline_text(
        position, 
        wrapped_text, 
        font=font, 
        fill=(255, 255, 255, 255), 
        align='center'
    )
    
    # Combine background and text
    bg = bg.convert("RGBA")
    final_img = Image.alpha_composite(bg, overlay)
    
    # Convert to numpy array for MoviePy
    img_array = np.array(final_img)
    clip = ImageClip(img_array).set_duration(duration)
    
    # Add effects if enabled
    if add_effects:
        # Zoom in effect
        clip = clip.fx(vfx.resize, lambda t: 1 + 0.01 * t)
        
        # Fade in effect
        clip = clip.fadein(0.5)
        
        # Subtle movement effect
        clip = clip.set_position(lambda t: ('center', 360 + 5*np.sin(t*2)))
    
    return clip

def generate_video(text, background_choice, add_effects=True):
    """Generate video with selected background and effects"""
    # First generate audio
    audio_path = generate_audio(text)
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration
    
    # Get background path
    bg_path = os.path.join("backgrounds", BACKGROUND_OPTIONS[background_choice]) if BACKGROUND_OPTIONS[background_choice] else None
    
    # Split text into chunks for multiple scenes
    words = text.split()
    chunk_size = max(len(words) // max(int(duration // 5), 1), 5)  # Ensure at least 5 words per chunk
    chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
    
    # Create clips for each text chunk
    clips = []
    for i, chunk in enumerate(chunks):
        clip_duration = duration/len(chunks)
        
        # Rotate through different backgrounds if using gradient
        if background_choice == "Gradient":
            current_bg = None  # This will trigger gradient generation
        else:
            current_bg = bg_path
            
        clip = create_text_clip(chunk, clip_duration, bg_image=current_bg, add_effects=add_effects)
        
        # Add crossfade transition between clips
        if i > 0:
            clip = clip.crossfadein(0.5)
        
        clips.append(clip)
    
    # Combine all clips
    video_clip = concatenate_videoclips(clips, method="compose")
    video_clip = video_clip.set_audio(audio_clip)
    
    # Add background music (optional)
    if os.path.exists("background_music.mp3"):
        music = AudioFileClip("background_music.mp3").volumex(0.1)
        music = music.set_duration(duration)
        video_clip.audio = CompositeAudioClip([video_clip.audio, music])
    
    return video_clip, audio_path

def main():
    st.title("🎬 Enhanced Text to Video Converter")
    st.markdown("Transform your text into engaging videos with beautiful backgrounds and animations")
    
    # Text input
    text = st.text_area("Enter your text:", placeholder="Type or paste your text here...", height=200)
    
    # Output type selection
    output_type = st.radio("Select output format:", ("Audio (MP3)", "Video (MP4)"))
    
    # Video options (only shown when video is selected)
    if output_type == "Video (MP4)":
        col1, col2 = st.columns(2)
        with col1:
            background_choice = st.selectbox(
                "Select background style:",
                list(BACKGROUND_OPTIONS.keys())
            )
        with col2:
            add_effects = st.checkbox("Add animations and effects", value=True)
    
    # Generate button
    if st.button("Generate Now", type="primary"):
        if not text.strip():
            st.warning("Please enter some text first.")
        else:
            with st.spinner(f"✨ Creating your {output_type}..."):
                try:
                    if output_type == "Audio (MP3)":
                        audio_path = generate_audio(text)
                        st.audio(audio_path)
                        
                        with open(audio_path, "rb") as f:
                            st.download_button(
                                label="Download Audio File",
                                data=f,
                                file_name="output.mp3",
                                mime="audio/mpeg",
                                key="audio_dl"
                            )
                        os.unlink(audio_path)
                    
                    else:  # Video
                        video_clip, audio_path = generate_video(text, background_choice, add_effects)
                        
                        # Save video to temp file
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as video_fp:
                            video_clip.write_videofile(video_fp.name, codec='libx264', fps=24, threads=4)
                            st.video(video_fp.name)
                            
                            with open(video_fp.name, "rb") as f:
                                st.download_button(
                                    label="Download Video File",
                                    data=f,
                                    file_name="output.mp4",
                                    mime="video/mp4",
                                    key="video_dl"
                                )
                        
                        # Clean up temporary files
                        os.unlink(video_fp.name)
                        os.unlink(audio_path)
                    
                    st.success("Generation complete! 🎉")
                    st.balloons()
                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    st.error("Please check that all required background images are available.")

if __name__ == "__main__":
    main()
