from fastapi import FastAPI
from .database import engine, Base, SessionLocal  # Added SessionLocal here
from .routes import router
from .models import Property  # Added this import
from fastapi.middleware.cors import CORSMiddleware

# Add CORS middleware
app = FastAPI()
app.include_router(router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# 1. Create the database tables
Base.metadata.create_all(bind=engine)

# 2. Add the "Seed Data" logic right here
db = SessionLocal()
if not db.query(Property).first():
    property = Property(
        name="Bangalore Commercial Property",
        total_value=10000000,
        total_units=1000,
        available_units=1000
    )
    db.add(property)
    db.commit()
db.close()

# 3. Initialize the FastAPI app
app = FastAPI()

app.include_router(router)

@app.get("/")
def root():
    return {"message": "Real Estate Blockchain MVP Running"}