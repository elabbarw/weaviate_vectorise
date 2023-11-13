import weaviate,os
from dotenv import load_dotenv
load_dotenv()
WEAVIATE_URL = os.getenv('WEAVIATE_URL')
WEAVIATE_KEY = os.getenv('WEAVIATE_KEY')
client = weaviate.Client(
    WEAVIATE_URL,
    auth_client_secret=weaviate.AuthApiKey(os.getenv('WEAVIATE_KEY')), # type: ignore
)


res = client.query.get(
    "kb_articles", ["text source"]
).with_near_text({
  "concepts":['request access to figma'],


  }).with_autocut(2).do()

print (res)
