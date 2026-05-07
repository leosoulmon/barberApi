from fastapi import FastAPI

app = FastAPI(title="Barber API", version="0.1.0")


@app.get("/")
def root():
    return {"message": "Barber API is running"}
