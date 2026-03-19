from fastapi import FastAPI
from src.gemini_api import generate_response
from dotenv import load_dotenv


app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI in Docker with uv!"}

@app.post("/message")
def create_message(message: str):
    llm_response = generate_response(message)
    print(llm_response)
    return {"message": f"{llm_response}"}

if __name__ == "__main__":
    import uvicorn
    load_dotenv('.env')
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)