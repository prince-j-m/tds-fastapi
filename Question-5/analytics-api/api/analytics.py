from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

API_KEY = "ak_wnqazz84r601l5cero2cag7l"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/")
async def analytics(request: Request):
    api_key = request.headers.get("X-API-Key")

    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()
    events = data.get("events", [])

    total_events = len(events)
    unique_users = len(set(e["user"] for e in events))
    revenue = sum(e["amount"] for e in events if e["amount"] > 0)

    user_totals = {}
    for e in events:
        if e["amount"] > 0:
            user_totals[e["user"]] = user_totals.get(e["user"], 0) + e["amount"]

    top_user = max(user_totals, key=user_totals.get) if user_totals else None

    return {
        "email": "23f3001847@ds.study.iitm.ac.in",
        "total_events": total_events,
        "unique_users": unique_users,
        "revenue": revenue,
        "top_user": top_user
    }