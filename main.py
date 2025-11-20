import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone

from database import create_document, get_documents, db
from bson import ObjectId

app = FastAPI(title="Vibe Station API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Pricing(BaseModel):
    type: str = Field(..., description="one-time | subscription | negotiation")
    amount: Optional[float] = Field(None, ge=0)
    currency: str = Field("USD")

class Links(BaseModel):
    external_url: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None
    embed_url: Optional[HttpUrl] = None
    zip_url: Optional[HttpUrl] = None

class AIInsights(BaseModel):
    summary: Optional[str] = None
    pitch: Optional[str] = None
    landing_copy: Optional[str] = None
    deck_outline: Optional[List[str]] = None
    tags: List[str] = []
    readiness_score: Optional[float] = Field(None, ge=0, le=100)
    market_fit_score: Optional[float] = Field(None, ge=0, le=100)
    suggestions: Optional[List[str]] = None

class ProjectIn(BaseModel):
    name: str
    description: Optional[str] = None
    tech_stack: List[str] = []
    category: Optional[str] = None
    pricing: Optional[Pricing] = None
    status: str = Field("MVP", description="MVP | prototype | commercial-ready")
    links: Optional[Links] = None
    thumbnails: List[str] = []

class Project(ProjectIn):
    id: str
    created_at: datetime
    updated_at: datetime
    ai: AIInsights = AIInsights()
    views: int = 0
    saves: int = 0
    watchers: int = 0


def _serialize(doc: Dict[str, Any]) -> Dict[str, Any]:
    d = dict(doc)
    if d.get("_id"):
        d["id"] = str(d.pop("_id"))
    # Convert datetime to isoformat
    for k in ["created_at", "updated_at"]:
        if isinstance(d.get(k), datetime):
            d[k] = d[k].isoformat()
    return d


@app.get("/")
def read_root():
    return {"message": "Vibe Station API ready"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# Projects Endpoints
@app.post("/api/projects", response_model=Project)
def create_project(payload: ProjectIn):
    base: Dict[str, Any] = payload.model_dump()
    now = datetime.now(timezone.utc)
    base.update({
        "ai": AIInsights().model_dump(),
        "views": 0,
        "saves": 0,
        "watchers": 0,
        "created_at": now,
        "updated_at": now,
    })
    new_id = create_document("project", base)
    created = db["project"].find_one({"_id": ObjectId(new_id)})
    return Project(**_serialize(created))


@app.get("/api/projects", response_model=List[Project])
def list_projects(category: Optional[str] = None, tech: Optional[str] = None):
    filt: Dict[str, Any] = {}
    if category:
        filt["category"] = category
    if tech:
        filt["tech_stack"] = {"$in": [tech]}
    docs = get_documents("project", filt)
    return [Project(**_serialize(d)) for d in docs]


@app.get("/api/projects/{project_id}", response_model=Project)
def get_project(project_id: str):
    try:
        doc = db["project"].find_one({"_id": ObjectId(project_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid project id")
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    return Project(**_serialize(doc))


# Simple AI bootstrap endpoint (stubbed content generation)
@app.post("/api/projects/{project_id}/bootstrap-ai")
def bootstrap_ai(project_id: str):
    doc = db["project"].find_one({"_id": ObjectId(project_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")

    name = doc.get("name", "Your MVP")
    description = doc.get("description") or "An innovative micro-app that solves a focused problem."
    techs = ", ".join(doc.get("tech_stack", [])) or "modern web stack"

    ai_block = {
        "summary": f"{name} — {description}",
        "pitch": f"{name} helps teams move faster by automating key workflows using {techs}.",
        "landing_copy": f"Ship faster with {name}. Built with {techs}.", 
        "deck_outline": [
            "Problem",
            "Solution",
            "Product Demo",
            "Market",
            "Business Model",
            "Roadmap"
        ],
        "tags": [t.lower() for t in doc.get("category", "").split()] + doc.get("tech_stack", []),
        "readiness_score": 60.0,
        "market_fit_score": 55.0,
        "suggestions": [
            "Add a quick demo video",
            "Publish a public roadmap",
            "Collect early user feedback"
        ]
    }

    db["project"].update_one(
        {"_id": ObjectId(project_id)},
        {"$set": {"ai": ai_block, "updated_at": datetime.now(timezone.utc)}}
    )

    updated = db["project"].find_one({"_id": ObjectId(project_id)})
    return _serialize(updated)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
