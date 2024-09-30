# stt_v2.py (modified to support indefinite listening)
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
        
        # Keep listening until the user presses 'Enter'
        while not stop_listening_event.is_set():
            try:
                print("Listening for speech (press Enter to stop and switch to LLM)...")
                audio_text = r.listen(source)  # Removed phrase_time_limit for continuous listening
                print("Processing speech...")

                # Recognize the speech using Google Web Speech API
                text = r.recognize_google(audio_text)
                print(f"Google thinks you said: {text}")

                # Wrap the recognized text
                wrapped_text = wrapper.fill(text)

                # Add wrapped text to the PDF
                pdf.multi_cell(0, 10, wrapped_text)
                pdf.ln()  # Add an empty line between segments

            except sr.WaitTimeoutError:
                print("No speech detected, waiting for input...")
            except sr.UnknownValueError:
                print("Sorry, I did not get that.")
            except sr.RequestError as e:
                print(f"Could not request results; {e}")

    # Save the transcription to a PDF once Enter is pressed
    pdf.output(pdf_filename)
    print(f"Transcription saved to {pdf_filename}\n")