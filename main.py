import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI(title="GenZyFits API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility to validate ObjectId strings

def oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


@app.get("/")
def read_root():
    return {"message": "GenZyFits API running"}


# Schemas are defined in schemas.py; expose them for the database viewer
@app.get("/schema")
def get_schema_overview():
    try:
        import schemas
        keys = [k for k in dir(schemas) if k[0].isupper()]
        return {"schemas": keys}
    except Exception as e:
        return {"error": str(e)}


# Seed sample products if collection empty
@app.post("/seed")
def seed_products():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    count = db["product"].count_documents({})
    if count > 0:
        return {"seeded": False, "message": "Products already exist"}

    sample = [
        {
            "title": "Neon Flux Hoodie",
            "slug": "neon-flux-hoodie",
            "description": "Oversized hoodie with neon gradient print",
            "price": 89.0,
            "category": "Streetwear",
            "images": [
                "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?q=80&w=1400&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1520975922284-7b683db0352b?q=80&w=1400&auto=format&fit=crop"
            ],
            "sizes": ["S","M","L","XL"],
            "tags": ["best","seasonal"],
            "rating": 4.7,
            "rating_count": 243,
            "in_stock": True
        },
        {
            "title": "Ripple Tee",
            "slug": "ripple-tee",
            "description": "Boxy fit tee with wave puff print",
            "price": 39.0,
            "category": "Casual",
            "images": [
                "https://images.unsplash.com/photo-1520975693416-35a6a199d470?q=80&w=1400&auto=format&fit=crop"
            ],
            "sizes": ["XS","S","M","L"],
            "tags": ["new"],
            "rating": 4.4,
            "rating_count": 91,
            "in_stock": True
        },
        {
            "title": "Core Knit Crew",
            "slug": "core-knit-crew",
            "description": "Premium heavyweight knit crewneck",
            "price": 69.0,
            "category": "Essentials",
            "images": [
                "https://images.unsplash.com/photo-1521577352947-9bb58764b69a?q=80&w=1400&auto=format&fit=crop"
            ],
            "sizes": ["S","M","L","XL"],
            "tags": ["best"],
            "rating": 4.8,
            "rating_count": 512,
            "in_stock": True
        }
    ]

    for p in sample:
        create_document("product", p)

    return {"seeded": True, "count": len(sample)}


# Public catalog endpoints
@app.get("/products")
def list_products(tag: Optional[str] = None, category: Optional[str] = None):
    if db is None:
        return []
    filt = {}
    if tag:
        filt["tags"] = tag
    if category:
        filt["category"] = category
    prods = get_documents("product", filt)
    # Serialize ObjectId
    for p in prods:
        p["_id"] = str(p.get("_id"))
    return prods


@app.get("/products/{product_id}")
def get_product(product_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    doc = db["product"].find_one({"_id": oid(product_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    doc["_id"] = str(doc["_id"])
    return doc


# Reviews
class ReviewIn(BaseModel):
    product_id: str
    user_name: str
    rating: int
    comment: Optional[str] = None


@app.get("/reviews/{product_id}")
def get_reviews(product_id: str):
    if db is None:
        return []
    items = get_documents("review", {"product_id": product_id})
    for r in items:
        r["_id"] = str(r.get("_id"))
    return items


@app.post("/reviews")
def create_review(payload: ReviewIn):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    # simple validation
    if not db["product"].find_one({"_id": oid(payload.product_id)}):
        raise HTTPException(status_code=400, detail="Invalid product")
    review_id = create_document("review", payload.model_dump())
    return {"_id": review_id}


# Fast checkout (mock intent creation)
class CheckoutItem(BaseModel):
    product_id: str
    size: Optional[str] = None
    quantity: int = 1

class CheckoutRequest(BaseModel):
    email: str
    items: List[CheckoutItem]

@app.post("/checkout")
def fast_checkout(req: CheckoutRequest):
    # Calculate total from products
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    total = 0.0
    line_items = []
    for item in req.items:
        prod = db["product"].find_one({"_id": oid(item.product_id)})
        if not prod:
            raise HTTPException(status_code=400, detail=f"Invalid product: {item.product_id}")
        price = float(prod.get("price", 0))
        line_total = price * int(item.quantity)
        total += line_total
        line_items.append({
            "title": prod.get("title"),
            "size": item.size,
            "quantity": item.quantity,
            "unit_price": price,
            "line_total": line_total
        })

    order_doc = {
        "email": req.email,
        "items": line_items,
        "total": round(total, 2),
        "status": "created"
    }
    order_id = create_document("order", order_doc)
    return {"order_id": order_id, "total": round(total, 2)}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available" if db is None else "✅ Connected",
    }
    if db is not None:
        try:
            response["collections"] = db.list_collection_names()
        except Exception as e:
            response["collections_error"] = str(e)
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
