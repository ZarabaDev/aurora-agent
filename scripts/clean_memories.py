
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_core.brain import AgentBrain

def clean_memories():
    print("Initializing Brain...")
    brain = AgentBrain()
    
    if not brain.vector_db:
        print("Vector DB disabled. Check API key.")
        return

    # Strings to cleanup
    target_phrases = ["secret verification code"]
    
    for phrase in target_phrases:
        print(f"Searching for memories containing: '{phrase}'")
        # Search to get the IDs
        results = brain.vector_db.similarity_search_with_score(phrase, k=10)
        
        ids_to_delete = []
        for doc, score in results:
            print(f"Found: {doc.page_content} (Score: {score})")
            # Heuristic: if the exact phrase is in the content, mark for deletion
            if phrase in doc.page_content:
                # Chroma docs don't always expose ID easily in LangChain wrapper unless we use the _collection
                # We need to access the underlying collection
                pass

        # LangChain Chroma wrapper doesn't expose delete by ID easily in the high level API
        # We need to access brain.vector_db._collection (chromadb native collection)
        
        # Proper way with LangChain Chroma:
        # It's actually hard to get IDs from similarity_search.
        # Let's use the underlying collection directly.
        
        collection = brain.vector_db._collection
        
        # Query using the text
        # Using "where_document" contains
        existing_docs = collection.get(where_document={"$contains": phrase})
        
        if existing_docs and existing_docs['ids']:
            ids = existing_docs['ids']
            documents = existing_docs['documents']
            print(f"Found {len(ids)} documents matching '{phrase}':")
            for i, doc in enumerate(documents):
                print(f" - {doc}")
            
            confirm = input("Delete these memories? (y/n): ")
            if confirm.lower() == 'y':
                collection.delete(ids=ids)
                print("Deleted.")
            else:
                print("Skipped.")
        else:
            print(f"No exact matches found for '{phrase}'.")

if __name__ == "__main__":
    clean_memories()
