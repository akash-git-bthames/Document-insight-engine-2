















from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from database import get_db, engine
from models import Base, Document
from schemas import DocumentUpload, DocumentResponse
from s3_utils import upload_to_s3
from unstructured.partition.pdf import partition_pdf, PDFDocument
from elasticsearch import Elasticsearch
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import ElasticVectorSearch
from crewai import AutoGen



import shutil

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/upload/", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Save the uploaded file temporarily
    file_location = f"temp_files/{file.filename}"
    with open(file_location, "wb+") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Upload the file to S3
    s3_url = upload_to_s3(open(file_location, 'rb'), "your-bucket-name", file.filename)
    if not s3_url:
        raise HTTPException(status_code=500, detail="Failed to upload to S3")

    # Parse the file using unstructured.io
    parsed_content = ""
    if file.content_type == "application/pdf":
        document = partition_pdf(file_location)
        parsed_content = document.text

    # Save document metadata to the database
    document_db = Document(filename=file.filename, file_type=file.content_type, s3_url=s3_url, parsed_content=parsed_content)
    db.add(document_db)
    db.commit()
    db.refresh(document_db)

    return DocumentResponse(id=document_db.id, filename=document_db.filename, file_type=document_db.file_type, s3_url=document_db.s3_url, parsed_content=document_db.parsed_content)

# More routes for user registration and query handling can be added here.






# Initialize Elasticsearch client
es_client = Elasticsearch(hosts=["http://localhost:9200"])

# Create an index in Elasticsearch for documents
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

# Function to index documents in Elasticsearch
def index_document(index_name: str, document: dict):
    es_client.index(index=index_name, body=document)

# Example usage of creating index
create_document_index()








@app.post("/upload")
async def upload_document(file: UploadFile):
    # Parse the document
    if file.filename.endswith(".pdf"):
        pdf_doc = PDFDocument.from_file(file.file)
        content = pdf_doc.get_text()
    
    # Index parsed content in Elasticsearch
    document = {
        "filename": file.filename,
        "content": content,
        "metadata": {"author": "Unknown"},  # Add additional metadata if necessary
        "timestamp": "2024-09-04T10:00:00"  # Add proper timestamp
    }
    index_document("documents", document)
    
    return {"message": "Document uploaded and indexed successfully"}








# Initialize the LangChain embedding model and ElasticSearch vector store
embedding_model = OpenAIEmbeddings()
vector_store = ElasticVectorSearch(
    embedding_model.embed,
    es_client,
    index_name="document_vectors"
)

# Function to index document content into LangChain for fast querying
def index_document_for_nlp(document: dict):
    content = document['content']
    vector_store.add_texts([content])

# Example usage: index a parsed document
document_content = {
    "filename": "example.pdf",
    "content": "This is the parsed content of the document.",
    "metadata": {"author": "Author Name"},
}
index_document_for_nlp(document_content)











# Initialize CrewAI RAG model
rag_model = AutoGen(api_key="YOUR_CREWAI_API_KEY")

# Function to handle query and response generation
def get_rag_response(query: str):
    # Search for relevant content from indexed documents
    response = vector_store.search(query)

    # Retrieve the most relevant document
    most_relevant_content = response['hits'][0]['_source']['content']
    
    # Generate an answer using the RAG model
    generated_response = rag_model.generate(query, context=most_relevant_content)
    
    return generated_response

# FastAPI route to handle queries
@app.get("/query")
async def query_document(query: str):
    # Get the RAG response
    response = get_rag_response(query)
    return {"query": query, "response": response}

