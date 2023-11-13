import weaviate,os
from dotenv import load_dotenv
load_dotenv()
WEAVIATE_URL = os.getenv('WEAVIATE_URL')
WEAVIATE_KEY = os.getenv('WEAVIATE_KEY')
client = weaviate.Client(
    WEAVIATE_URL,
    auth_client_secret=weaviate.AuthApiKey(os.getenv('WEAVIATE_KEY')), # type: ignore
)
client.schema.delete_class("kb_articles") #- uncomment to delete schema AND ALL DATA

kb_obj = {
    "class": "kb_articles",
    "description": "KB Articles",  # description of the class
    "properties": [
        {
            "dataType": ["text"],
            "description": "text",
            "name": "content",
        },
        {
            "dataType": ["text"],
            "description": "source",
            "name": "source",
        },
        {
            "dataType": ["text"],
            "description": "pageid",
            "name": "pageid",
        },
                {
            "dataType": ["text"],
            "description": "title",
            "name": "title",
        }
    ],
    "vectorizer": "text2vec-transformers",
}

# add the schema
client.schema.create_class(kb_obj)

