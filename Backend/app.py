from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db, Base, engine
from models import User, Document, Query
from schemas import UserCreate, UserResponse, DocumentResponse, DocumentCreate, QueryResponse, QueryCreate
from s3_utils import upload_to_s3
from elasticsearch import Elasticsearch
from langchain_cohere import CohereEmbeddings, ChatCohere
from langchain_elasticsearch import ElasticsearchStore
# from langchain_community.vectorstores import FAISS
import boto3
import openai
import shutil
import os
from dotenv import load_dotenv
import pdf2image
import pytesseract
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain import hub

from jwtAuthenticate import get_password_hash, create_access_token, verify_password,get_current_user
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


from datetime import timedelta



Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "*", # for allowing all orgins for testing
    "http://doc-inside-engine.s3-website.ap-south-1.amazonaws.com/" # or allowing frontend origin from s3
    "http://localhost",
    "http://localhost:5173",  # Example for a frontend running on a different port
    "http://yourdomain.com",  # Example for a deployed frontend
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow specific origins
    allow_credentials=True,  # Allow cookies and authorization headers
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all HTTP headers
)

# Load environment variables
load_dotenv()

# Initialize S3 Client
s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

# Initialize Elasticsearch client
es_client = Elasticsearch(hosts=["http://localhost:9200"])

# Retrieve the API key from environment variables
cohere_api_key = os.getenv("COHERE_API_KEY")

# Initialize the CohereEmbeddings with the API key
embeddings = CohereEmbeddings(
    model="embed-english-v3.0",
    cohere_api_key=cohere_api_key
)
elastic_vector_search = ElasticsearchStore(
    es_url="http://localhost:9200",
    index_name="langchain_index",
    embedding=embeddings,
)

# Initialize Cohere LLM
llm = ChatCohere(model="command-r-plus")

# Create the Elasticsearch index for documents on startup
def create_document_index(index_name: str = "documents"):
    if not es_client.indices.exists(index=index_name):
        es_client.indices.create(index=index_name, body={
            "mappings": {
                "properties": {
                    "filename": {"type": "text"},
                    "content": {"type": "text"},
                    "metadata": {"type": "object"},
                    "timestamp": {"type": "date"}
                }
            }
        })


# OAuth2PasswordBearer is a dependency that retrieves the token from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# User signup
@app.post("/signup", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.email, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

# Token login for OAuth2
@app.post("/token", response_model=dict)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

# Fetch current authenticated user
@app.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user




# 1. File Upload Route
@app.post("/upload/", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    temp_dir = "temp_files"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    file_location = f"{temp_dir}/{file.filename}"
    try:
        with open(file_location, "wb+") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Step 2: Upload the file to AWS S3
        s3_url = upload_to_s3(open(file_location, 'rb'), "document-insight-engine-1-bucket", file.filename)
        if not s3_url:
            raise HTTPException(status_code=500, detail="Failed to upload to S3")
        # Step 3: Parse the file content using pytesseract
        parsed_content = ""
        if file.content_type == "application/pdf":
            images = pdf2image.convert_from_path(file_location)
            parsed_content = "\n".join([pytesseract.image_to_string(image) for image in images])
        
        # Step 4: Save document metadata to the database
        document_db = Document(
            filename=file.filename,
            file_type=file.content_type,
            s3_url=s3_url,
            parsed_content=parsed_content
        )
        db.add(document_db)
        db.commit()
        db.refresh(document_db)
        
        # Step 5: Index the parsed content in Elasticsearch
        document_data = {
            "filename": file.filename,
            "content": parsed_content,
            "metadata": {"author": "Unknown"},
            "timestamp": "2024-09-07T10:00:00"
        }
        index_document("documents", document_data)
        
        # Step 6: Index parsed content for NLP using LangChain
        index_document_for_nlp(document_data)
        
        return DocumentResponse(
            id=document_db.id,
            filename=document_db.filename,
            file_type=document_db.file_type,
            s3_url=document_db.s3_url,
            parsed_content=document_db.parsed_content
        )
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {str(e)}")
    finally:
        try:
            os.remove(file_location)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File Cleanup Error: {str(e)}")

# 2. Elasticsearch: Index Document
def index_document(index_name: str, document: dict):
    es_client.index(index=index_name, body=document)

# 3. LangChain: NLP Indexing and Querying
def index_document_for_nlp(document):
    content = document['content']
    elastic_vector_search.add_texts([content])

# Define the RAG retrieval and generation pipeline
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": elastic_vector_search.as_retriever(search_type="similarity", search_kwargs={"k": 10}) | format_docs, 
     "question": RunnablePassthrough()}
    | hub.pull("rlm/rag-prompt")
    | llm
    | StrOutputParser()
)


# RAG Response Generation Route
@app.get("/query")
async def query_document(query: str):
    # Use RAG pipeline to retrieve documents and generate response
    response=""
    for chunk in rag_chain.stream(query):
        response  += chunk
        if response == "I don't know.":
            response =""
            response += "Sorry unable to answer your question: "
            response += query
        print(chunk, end="", flush=True)

    
    return {"query": query, "response": response}

# Create the document index on startup
create_document_index()

# Home Route
@app.get("/")
async def homepage():
    return "Hello from Document Management System!"

# Elasticsearch Search Route
@app.post("/api/search")
async def search_documents(request: Request):
    data = await request.json()
    query = data.get("query")
    
    # Construct the Elasticsearch search query
    search_body = {
        "query": {
            "match": {
                "parsed_content": query
            }
        }
    }
    
    # Execute the search query
    response = es_client.search(index="documents", body=search_body)
    
    # Return the search results
    return response
