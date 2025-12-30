import os
from pydub import AudioSegment
import speech_recognition as sr
import subprocess
from controller.models import SessionLocal, Song  # Adjust import based on your project

DB_SESSION = SessionLocal()

def convert_to_wav(input_file):
    """Convert audio file to WAV format."""
    filename, ext = os.path.splitext(input_file)
    if ext.lower() != ".wav":
        wav_file = f"{filename}.wav"
        audio = AudioSegment.from_file(input_file)
        audio.export(wav_file, format="wav")
        return wav_file
    return input_file

def transcribe_audio(audio_path):
    """Convert audio to raw text using speech recognition."""
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio_data)  # you can integrate offline Whisper if needed
        return text
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return ""

def generate_lyrics_from_text(raw_text):
    """Use Ollama Mistral to convert raw text to lyrical style."""
    if not raw_text.strip():
        return "Lyrics could not be generated."
    
    prompt = f"Convert the following spoken text into song lyrics:\n{raw_text}"
    command = ["ollama", "run", "mistral:latest", "--prompt", prompt]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        return "Lyrics generation failed."
    return result.stdout.strip()

def update_song_lyrics(song_id, audio_path):
    """Main function to process audio and update lyrics."""
    wav_path = convert_to_wav(audio_path)
    raw_text = transcribe_audio(wav_path)
    lyrics = generate_lyrics_from_text(raw_text)

    song = DB_SESSION.query(Song).filter_by(id=song_id).first()
    if song:
        song.lyrics = lyrics
        DB_SESSION.commit()
        print(f"Lyrics updated for song: {song.title}")
    else:
        print("Song not found.")
