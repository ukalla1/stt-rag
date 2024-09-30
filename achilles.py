import threading
import time
from stt_v2 import listen_and_recognize, stop_listening_event
from rag import RAG_pipeline

# Global flag to track the current chunk number
current_chunk_number = 0

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

# Main function to manage both STT and RAG processes sequentially
def main():
    global stop_listening_event

    while True:
        # Start the STT part
        stop_listening_event.clear()
        print("Listening for speech indefinitely... Press Enter at any time to stop and switch to LLM.")

        # Start a separate thread to listen for speech while waiting for Enter press
        stt_thread = threading.Thread(target=run_stt)
        stt_thread.start()

        # Wait for user to press Enter
        input("Press Enter to stop listening and save the transcription...\n")
        
        # Stop the STT thread
        stop_listening_event.set()
        stt_thread.join()

        # RAG part
        run_rag()

        # Ask the user whether to continue with STT or LLM
        next_step = input("Do you want to go back to STT, ask another LLM question, or exit? (stt/llm/exit): ").strip().lower()
        
        if next_step == 'exit':
            print("Exiting the system...")
            break
        elif next_step == 'llm':
            continue  # Continue with the LLM-RAG part
        elif next_step == 'stt':
            print("Going back to the STT process...")
            continue  # Go back to the STT process

if __name__ == "__main__":
    main()