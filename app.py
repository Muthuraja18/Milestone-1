from flask import Flask, render_template, request, jsonify
import pyaudio
import wave
import json
from vosk import Model, KaldiRecognizer
from textblob import TextBlob
import gspread
from google.oauth2.service_account import Credentials
import datetime
import random

app = Flask(__name__)

# Google Sheets setup
json_key_path = r'C:\Users\Muthuraja\Downloads\modern-cycling-444916-g6-82c207d3eb47.json'
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(json_key_path, scopes=scopes)
client = gspread.authorize(creds)
sheet = client.open('Sales').sheet1

# Vosk Model setup
model = Model(r"C:\Users\Muthuraja\OneDrive\Attachments\Desktop\Ai intern\vosk-model-small-en-us-0.15")

# Function to record audio
def record_audio():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    RECORD_SECONDS = 5
    WAVE_OUTPUT_FILENAME = "output.wav"

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Recording...")
    frames = []

    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Recording complete.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    return WAVE_OUTPUT_FILENAME

# Function to transcribe audio to text
def transcribe_audio(file_path):
    wf = wave.open(file_path, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())

    transcript = ""
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            transcript += result.get("text", "")

    result = json.loads(rec.FinalResult())
    transcript += result.get("text", "")

    print("Transcript:", transcript)
    return transcript

# Function to analyze sentiment
def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment_polarity = blob.sentiment.polarity
    sentiment_description = "Positive" if sentiment_polarity > 0 else "Negative" if sentiment_polarity < 0 else "Neutral"
    return sentiment_polarity, sentiment_description

# Function to get a random emoji based on sentiment
def get_random_emoji(sentiment):
    positive_emojis = ["😊", "😃", "😄", "😁", "🙂"]
    negative_emojis = ["😞", "😠", "😢", "😟", "😡"]
    neutral_emojis = ["😐", "😶", "🤔", "😑", "😏"]

    if sentiment == "Positive":
        return random.choice(positive_emojis)
    elif sentiment == "Negative":
        return random.choice(negative_emojis)
    else:
        return random.choice(neutral_emojis)

# Function to update Google Sheet
def update_sheet(transcript, sentiment, score):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, transcript, sentiment, score])

# Flask route to handle audio recording and sentiment analysis
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/record', methods=['POST'])
def record_and_analyze():
    # Record audio
    audio_file = record_audio()

    # Transcribe the audio
    text = transcribe_audio(audio_file)
   
    # Analyze sentiment
    sentiment_score, sentiment = analyze_sentiment(text)
    emoji = get_random_emoji(sentiment)

    # Update Google Sheets with the results
    update_sheet(text, sentiment, sentiment_score)

    # Return results as JSON
    return jsonify({
        'transcript': text,
        'sentiment': sentiment,
        'sentiment_score': sentiment_score,
        'emoji': emoji
    })

if __name__ == "__main__":
    app.run(debug=True)
