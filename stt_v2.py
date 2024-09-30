# stt_v2.py (modified to support indefinite listening with Enter key)
import speech_recognition as sr
import threading
import textwrap
from fpdf import FPDF

# Initialize recognizer class (for recognizing the speech)
r = sr.Recognizer()

# Word wrapping setup (wrap at 80 characters per line)
wrapper = textwrap.TextWrapper(width=80)

# Event to stop the recording
stop_listening_event = threading.Event()

# Function to listen and recognize speech, continuously transcribing
def listen_and_recognize(current_chunk_number):
    pdf_filename = f"transcription_chunk_{current_chunk_number}.pdf"
    
    # Initialize the PDF document
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=1)  # Adjusts based on background noise
        
        # Buffer to store ongoing transcriptions
        full_transcription = ""

        print("Listening for speech (press Enter to stop and save)...")
        
        while not stop_listening_event.is_set():
            try:
                # Listen to a chunk of speech
                audio_text = r.listen(source, phrase_time_limit=None, timeout=None)
                # audio_text = r.record(source)
                # print("Processing speech...")

                # Recognize the speech using Google Web Speech API
                text = r.recognize_google(audio_text)
                # print(f"Google thinks you said: {text}")

                # Store the transcription in a buffer
                full_transcription += text + " "

            except sr.UnknownValueError:
                # print("Sorry, I did not get that.")
            except sr.RequestError as e:
                # print(f"Could not request results; {e}")

        # Wrap the entire transcribed conversation and write to PDF
        wrapped_text = wrapper.fill(full_transcription)
        pdf.multi_cell(0, 10, wrapped_text)
        pdf.ln()  # Add an empty line between segments

    # Save the transcription to a PDF once Enter is pressed
    pdf.output(pdf_filename)
    print(f"Transcription saved to {pdf_filename}\n")
