import os
import asyncio
import re
import time
import subprocess
import requests
from telethon import TelegramClient, events
from dotenv import load_dotenv

# 🔹 טען משתנים מקובץ .env
load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")  # לא חובה אם משתמש ב־Userbot בלבד
YMOT_TOKEN = os.getenv("YMOT_TOKEN")
YMOT_PATH = os.getenv("YMOT_PATH", "ivr2:/97")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")  # @catava56u של הערוץ שלך

# 🔹 התחברות עם חשבון משתמש
client = TelegramClient("user_session", api_id, api_hash)

# 🔹 המרת טקסט לעברית בלבד (לקריינות)
def hebrew_only(text):
    # שמירה על תווים עבריים, פסיקים, נקודות, סימני שאלה וקריאה
    return re.sub(r'[^\u0590-\u05FF\s.,!?()\n]', '', text)

# 🔹 המרת קובץ ל־wav
def convert_to_wav(input_file, output_file='output.wav'):
    subprocess.run([
        'ffmpeg', '-i', input_file, '-ar', '8000', '-ac', '1', '-f', 'wav',
        output_file, '-y'
    ])

# 🔹 העלאה ל־Ymot
def upload_to_ymot(file_path):
    url = 'https://call2all.co.il/ym/api/UploadFile'
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, 'audio/wav')}
        data = {
            'token': YMOT_TOKEN,
            'path': YMOT_PATH,
            'convertAudio': '1',
            'autoNumbering': 'true'
        }
        response = requests.post(url, data=data, files=files)
    print("📞 תגובת ימות:", response.text)

# 🔹 טיפול בהודעות מהערוץ
@client.on(events.NewMessage(chats=CHANNEL_USERNAME))
async def handler(event):
    message = event.message
    text = message.text or message.caption
    media = message.media

    # אם יש קובץ (כולל >50MB)
    if media:
        file_path = "temp_file"
        await client.download_media(media, file_path)
        convert_to_wav(file_path, "temp.wav")
        upload_to_ymot("temp.wav")
        os.remove(file_path)
        os.remove("temp.wav")
        print("✅ קובץ הועלה בהצלחה")
    
    # אם יש טקסט
    if text:
        cleaned = hebrew_only(text)
        if cleaned.strip():
            # כתיבה זמנית ל־wav עם gTTS או TTS אחר
            from google.cloud import texttospeech
            tts_client = texttospeech.TextToSpeechClient()
            synthesis_input = texttospeech.SynthesisInput(text=cleaned)
            voice = texttospeech.VoiceSelectionParams(
                language_code="he-IL",
                name="he-IL-Wavenet-B",
                ssml_gender=texttospeech.SsmlVoiceGender.MALE
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.2
            )
            response = tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            with open("temp.mp3", "wb") as f:
                f.write(response.audio_content)
            convert_to_wav("temp.mp3", "temp.wav")
            upload_to_ymot("temp.wav")
            os.remove("temp.mp3")
            os.remove("temp.wav")
            print("✅ טקסט עברית הוקרא והועלה")

# 🔹 הפעלה
async def main():
    await client.start()
    print("🚀 Userbot מחובר ומאזין לערוץ")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
