import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class EcommerceChunkManager:
    def __init__(self, window_size=10, step=2):
        """
        Initialize the manager with sliding window parameters.
        
        Args:
            window_size (int): Number of words per chunk.
            step (int): Overlap step between chunks.
        """
        self.window_size = window_size
        self.step = step

    def chunk(self, text):
        """
        Splits text into overlapping chunks using a sliding window approach.
        If the text is shorter than the window size, returns the full text as one chunk.
        """
        words = text.split()
        if len(words) < self.window_size:
            # Return the entire text as a single chunk if it's too short
            return [text]
        
        chunks = []
        for i in range(0, len(words) - self.window_size + 1, self.step):
            chunk = ' '.join(words[i:i+self.window_size])
            chunks.append(chunk)
            return chunks


    def find_relevant_chunks(self, text, query):
        """
        Uses cosine similarity to rank chunks by relevance to the query.
        """
        chunks = self.chunk(text)
        
        # Check if any chunks were generated
        if not chunks:
            print("No chunks were generated. Check the text length and window size.")
            return []
        
        vectorizer = TfidfVectorizer()
        # Combine the query and chunks for vectorization
        vectors = vectorizer.fit_transform([query] + chunks)
        
        # Ensure we have at least one chunk vector
        if vectors.shape[0] < 2:
            print("Not enough data for similarity computation.")
            return []
        
        query_vector = vectors[0]
        chunk_vectors = vectors[1:]
        
        # Compute cosine similarity between the query and each chunk
        similarities = cosine_similarity(query_vector, chunk_vectors).flatten()
        relevant_chunks = list(zip(chunks, similarities))
        # Sort chunks by similarity in descending order
        relevant_chunks.sort(key=lambda x: x[1], reverse=True)
        return relevant_chunks


# Example usage:
if __name__ == '__main__':
    # This text simulates a product description from an e-commerce site.
    text = (
        "Introducing the new SuperWidget! Enjoy features such as high resolution display, "
        "a sleek design, and an unbeatable price of $49.99. Check out the product image at "
        "https://amazon.com/superwidget.jpg. This SuperWidget is perfect for tech enthusiasts. "
        "Now available with a special discount!"
    )
    # Tailor the query to capture product details
    query = "price product image name discount"

    manager = EcommerceChunkManager(window_size=100, step=50)
    chunks = manager.chunk(text)
    relevant_chunks = manager.find_relevant_chunks(text, query)

    print("Relevant Chunks (sorted by relevance):")
    for chunk, score in relevant_chunks:
        print(f"Score: {score:.3f}, Chunk: {chunk[:100]}...")
