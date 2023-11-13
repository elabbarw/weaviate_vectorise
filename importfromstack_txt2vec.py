import requests
import json
import os
import weaviate
from dotenv import load_dotenv
load_dotenv()

BASE_URL = "https://yourteam.stackenterprise.co/api/2.3"
HEADERS = {
    "X-API-Key": os.getenv('STACKOVERFLOW_KEY'),
    "Content-Type": "application/json"
}

def get_all_questions():
    """Retrieve all questions for a given team, accounting for pagination."""
    all_questions = []
    page = 1
    has_more = True

    while has_more:
        url = f"{BASE_URL}/questions?order=desc&sort=activity&filter=!nNPvSNP4(R"
        response = requests.get(url, headers=HEADERS, params={"page": page, "pagesize": 100})  # Fetching 100 questions per page
        if response.status_code == 200:
            data = response.json()
            all_questions.extend(data["items"])
            has_more = data.get("has_more", False)
            page += 1
        else:
            break

    return all_questions

def get_accepted_answer(question_id):
    """Retrieve the accepted answer for a given question."""
    url = f"{BASE_URL}/questions/{question_id}/answers?order=desc&sort=activity&filter=!nNPvSNe7Gv"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        answers = response.json()["items"]
        for answer in answers:
            if answer.get("is_accepted"):
                return answer
    return None

def retrieve_all_question_data():
    """Retrieve all questions and their accepted answers."""
    questions_data = []
    questions = get_all_questions()
    
    for question in questions:
        data = {
            "title": question["title"],
            "question": question["body_markdown"],
            "answer": None,
            "url": question['link'],
            "question_id" : question['question_id']
        }
        if question.get("accepted_answer_id"):
            accepted_answer = get_accepted_answer(question["question_id"])
            if accepted_answer:
                data["answer"] = accepted_answer["body_markdown"]
        
        questions_data.append(data)
    
    return questions_data

# Execution
WEAVIATE_URL = os.getenv('WEAVIATE_URL')
os.environ["WEAVIATE_API_KEY"] = os.getenv('WEAVIATE_KEY')
client = weaviate.Client(
    WEAVIATE_URL,
    auth_client_secret=weaviate.AuthApiKey(os.getenv('WEAVIATE_KEY')), # type: ignore
)

all_questions_info = retrieve_all_question_data()

### Send them to Weaviate
counter=0

with client.batch(500) as batch:        
    for document in all_questions_info:      
        # print update message every 100 objects        
        if (counter %100 == 0):
            print(f"(Import {counter} / {len(all_questions_info)} ", end="\r")

        properties = {
        "text": f"Question:{document['question']}\nAnswer:{document['answer']}",
        "source": document['url'],
        "pageid": f"SO{document['question_id']}", ## page id with prefix SO so we know it's stackoverflow
        "title": document['question']
        }

        batch.add_data_object(properties, "kb_articles", None)
        counter = counter+1
    print(f"Import {counter} / {len(all_questions_info)}")
    
print(f"Import complete")


