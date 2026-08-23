import os
from google import genai
from PIL import Image

from dotenv import load_dotenv
load_dotenv(override=True)


class GeminiEmbedder:
    def __init__(self, model_name="gemini-embedding-001"):
        """
        Initializes the Google GenAI client and sets the model.
        The user specified "gemini-embedding-001".
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def embed_image(self, image: Image.Image) -> list[float]:
        """
        Embeds a single PIL Image.
        """
        print(f"Embedding image using model: {self.model_name}...")
        try:
            result = self.client.models.embed_content(
                model=self.model_name,
                contents=image
            )
            return result.embeddings[0].values
        except Exception as e:
            print(f"Error embedding image: {e}")
            raise e

    def embed_text(self, text: str) -> list[float]:
        """
        Embeds a text query.
        """
        print(f"Embedding text using model: {self.model_name}...")
        try:
            result = self.client.models.embed_content(
                model=self.model_name,
                contents=text
            )
            return result.embeddings[0].values
        except Exception as e:
            print(f"Error embedding text: {e}")
            raise e

documents = [
    "Virat Kohli is an Indian cricketer known for his aggressive batting and leadership.",
    "MS Dhoni is a former Indian captain famous for his calm demeanor and finishing skills.",
    "Sachin Tendulkar, also known as the 'God of Cricket', holds many batting records.",
    "Rohit Sharma is known for his elegant batting and record-breaking double centuries.",
    "Jasprit Bumrah is an Indian fast bowler known for his unorthodox action and yorkers."
]

embedding_model = GeminiEmbedder(model_name="gemini-embedding-001")
doc_embeddings = [embedding_model.embed_text(doc) for doc in documents]

query= "tell me about bowler of indian cricket team"

query_embedding = embedding_model.embed_text(query)

from sklearn.metrics.pairwise import cosine_similarity
scores = cosine_similarity([query_embedding], doc_embeddings)[0]

index, score = sorted(list(enumerate(scores)),key=lambda x:x[1])[-1]

print(query)
print(documents[index])
print("similarity score is:", score)
