import threading
import time
from stt_v2 import listen_and_recognize, stop_listening_event
from rag import RAG_pipeline

# Global flag to track the current chunk number
current_chunk_number = 0
stop_key_event = threading.Event()

# Function to handle STT process (speech-to-text)
def run_stt():
    global current_chunk_number

    print("Starting the STT process... You can speak indefinitely. Press Enter to stop and switch to the LLM.")
    
    # Call the STT module with the current chunk number
    listen_and_recognize(current_chunk_number)
    
    # Increment chunk number for the next chunk
    current_chunk_number += 1

    print("STT transcription is complete.")

# Function to handle RAG process (retrieve and answer)
def run_rag():
    global current_chunk_number

    analyzer = RAG_pipeline()

    # Load the chunk PDF and process it in RAG
    pdf_filename = f"transcription_chunk_{current_chunk_number - 1}.pdf"
    print(f"Processing {pdf_filename} in RAG...")

    try:
        pdf_files = [pdf_filename]
        docs = analyzer.load_documents(pdf_files)
        
        # Split documents into smaller chunks
        splits = analyzer.split_documents(docs, chunk_size=2048)

        # Create vector database
        vectordb = analyzer.create_vector_db(splits, persist_directory='docs/chroma/')
        k = vectordb._collection.count()

        # Build the QA chain
        analyzer.build_qa_chain()

        # Ask user for the question
        user_question = input("Please enter your question: ")

        # Generate the answer for the user-provided question
        answer = analyzer.generate_answer(user_question, k=k)

        # Print the result
        print(f"Answer: {answer}")

    except Exception as e:
        print(f"Error processing chunk: {e}")

    print("RAG process is complete.")

# Thread to monitor Enter key press to stop STT
def monitor_enter_key():
    input("Press Enter to stop listening...\n")
    stop_listening_event.set()  # Signal to stop the STT process

# Main function to manage both STT and RAG processes sequentially
def main():
    global stop_listening_event

    while True:
        # Reset the stop signal
        stop_listening_event.clear()

        # Start the STT part
        print("Listening for speech... Press Enter at any time to stop and switch to LLM.")

        # Start a thread to monitor the Enter key press
        enter_key_thread = threading.Thread(target=monitor_enter_key)
        enter_key_thread.start()

        # Start the STT process in the main thread
        run_stt()

        # Wait for the Enter key press to stop STT
        enter_key_thread.join()

        # RAG part
        run_rag()

        # Ask the user whether to continue with STT or LLM
        next_step = input("Do you want to go back to STT, ask another LLM question, or exit? (stt/llm/exit): ").strip().lower()
        
        if next_step == 'exit':
            print("Exiting the system...")
            break
        elif next_step == 'llm':
            # continue  # Continue with the LLM-RAG part
            run_rag()
        elif next_step == 'stt':
            print("Going back to the STT process...")
            continue  # Go back to the STT process

if __name__ == "__main__":
    main()