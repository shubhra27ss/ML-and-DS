import streamlit as st
from gtts import gTTS
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import tempfile
import os
import textwrap
import numpy as np

# Set page config
st.set_page_config(
    page_title="Text to Audio/Video Converter",
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
</style>
""", unsafe_allow_html=True)

def create_text_image(text, width=1280, height=720):
    """Create an image with wrapped text on white background"""
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except:
        font = ImageFont.load_default()
    
    wrapped_text = textwrap.fill(text, width=40)
    text_bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    position = ((width - text_width) / 2, (height - text_height) / 2)
    
    draw.multiline_text(position, wrapped_text, font=font, fill='black', align='center')
    return image

def generate_audio(text):
    """Generate audio from text"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
        tts = gTTS(text=text, lang='en')
        tts.save(fp.name)
        return fp.name

def generate_video(text):
    """Generate video from text"""
    # First generate audio
    audio_path = generate_audio(text)
    audio_clip = AudioFileClip(audio_path)
    
    # Create text image
    img = create_text_image(text)
    img_clip = ImageClip(np.array(img)).set_duration(audio_clip.duration)
    
    # Combine audio and image
    video_clip = img_clip.set_audio(audio_clip)
    
    # Save video
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as video_fp:
        video_clip.write_videofile(video_fp.name, codec='libx264', fps=24)
        return video_fp.name, audio_path

def main():
    st.title("📝 Text to Audio/Video Converter")
    st.markdown("Convert any text to downloadable audio (MP3) or video (MP4) files")
    
    # Text input
    text = st.text_area("Enter your text:", placeholder="Type or paste your text here...")
    
    # Output type selection
    output_type = st.radio("Select output format:", ("Audio (MP3)", "Video (MP4)"))
    
    # Generate button
    if st.button("Generate"):
        if not text.strip():
            st.warning("Please enter some text first.")
        else:
            with st.spinner(f"Generating {output_type}..."):
                try:
                    if output_type == "Audio (MP3)":
                        audio_path = generate_audio(text)
                        st.audio(audio_path)
                        
                        with open(audio_path, "rb") as f:
                            st.download_button(
                                label="Download Audio",
                                data=f,
                                file_name="output.mp3",
                                mime="audio/mpeg"
                            )
                        os.unlink(audio_path)
                    
                    else:  # Video
                        video_path, audio_path = generate_video(text)
                        st.video(video_path)
                        
                        with open(video_path, "rb") as f:
                            st.download_button(
                                label="Download Video",
                                data=f,
                                file_name="output.mp4",
                                mime="video/mp4"
                            )
                        # Clean up temporary files
                        os.unlink(video_path)
                        os.unlink(audio_path)
                    
                    st.success("Generation complete!")
                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
