import weaviate,os
from dotenv import load_dotenv
import os
import json
from langchain.document_loaders import ConfluenceLoader
from langchain.text_splitter import TokenTextSplitter, CharacterTextSplitter
from langchain.schema   import Document
import requests
import tiktoken

load_dotenv()


def get_spaces():
    """
    Get all global spaces from confluence
    """

    url = f"{os.getenv('CONFURL')}/rest/api/space"


    headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer: {os.getenv('CONFKEY')}"
    }
    
    params = {
        "limit" : 250,
        "type" : "global",
        "keys": "name,key"
    }

    response = requests.request(
    "GET",
    url,
    headers=headers,
    params=params
    )

    spaces = response.json()['results']
    
    listoutput = [{"name":space['name'], "key":space['key']} for space in spaces]
    
    
    return listoutput


def confluence_load():
    """
    Load pages from space
    """
    loader = ConfluenceLoader(
        url = os.getenv('CONFURL'), # type: ignore
        token = os.getenv('CONFKEY')
    )
    
    documents = loader.load(
        keep_markdown_format=True,
        cql='type = page AND lastmodified >= now("-2y") AND lastmodified <= now() AND space.key = "ITPortal"') ### CQL for pages that have been modified in the last two years and not IT archive
    return documents



WEAVIATE_URL = os.getenv('WEAVIATE_URL')
os.environ["WEAVIATE_API_KEY"] = os.getenv('WEAVIATE_KEY')
client = weaviate.Client(
    WEAVIATE_URL,
    auth_client_secret=weaviate.AuthApiKey(os.getenv('WEAVIATE_KEY')), # type: ignore
)

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


conf = confluence_load() 

### THE LANGCHAIN DOCUMENT LOADER ADDS ID WHICH CONFLICTS WITH WEAVIATE AND CAUSES ERRORS. THIS changes ids to pageid
new_documents = []
for doc in conf:
    if doc.page_content: ### The page actually has content and is not empty
        metadata = doc.metadata.copy()  # copy the metadata dict to avoid changing the original
        metadata['pageid'] = metadata.pop('id')  # rename 'id' to 'pageid'
        new_doc = Document(page_content=doc.page_content, metadata=metadata)  # create a new namedtuple
        new_documents.append(new_doc)  # append the new namedtuple to the new list
        

### Next we take the documents from the confluence space and split them into small manageable snippets.

### Split according to markdown headers, etc...
text_splitter = CharacterTextSplitter(chunk_size=512, chunk_overlap=51)
texts = text_splitter.split_documents(new_documents)
text_splitter = TokenTextSplitter(chunk_size=1000, chunk_overlap=10, encoding_name="cl100k_base")  # This the encoding for text-embedding-ada-002
texts = text_splitter.split_documents(texts)



### Send them to Weaviate
counter=0

with client.batch(500) as batch:        
    for document in texts:      
        # print update message every 100 objects        
        if (counter %100 == 0):
            print(f"(Import {counter} / {len(texts)} ", end="\r")

        properties = {
        "text": document.page_content,
        "source": document.metadata['source'],
        "pageid": document.metadata['pageid'],
        "title": document.metadata['title']
        }

        batch.add_data_object(properties, "interactiveit_kb", None)
        counter = counter+1
    print(f"Import {counter} / {len(texts)}")
    
print(f"Import complete")

