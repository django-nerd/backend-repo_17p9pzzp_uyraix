import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Order, OrderItem, User

app = FastAPI(title="Protein Store API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Protein Store Backend is running"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
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

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# ---------------------- Products ----------------------

@app.post("/api/products", response_model=dict)
def create_product(product: Product):
    try:
        product_id = create_document("product", product)
        return {"id": product_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ProductQuery(BaseModel):
    category: Optional[str] = None
    q: Optional[str] = None
    limit: Optional[int] = 50

@app.get("/api/products")
def list_products(category: Optional[str] = None, q: Optional[str] = None, limit: int = 50):
    try:
        filter_dict = {}
        if category:
            filter_dict["category"] = category
        if q:
            filter_dict["$or"] = [
                {"title": {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}},
                {"tags": {"$regex": q, "$options": "i"}},
            ]
        docs = get_documents("product", filter_dict, limit)
        # Convert ObjectId
        for d in docs:
            if d.get("_id"):
                d["id"] = str(d.pop("_id"))
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    try:
        docs = get_documents("product", {"_id": ObjectId(product_id)}, 1)
        if not docs:
            raise HTTPException(status_code=404, detail="Product not found")
        d = docs[0]
        d["id"] = str(d.pop("_id"))
        return d
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------- Seed sample products ----------------------

@app.post("/api/seed")
def seed_products():
    try:
        existing = get_documents("product", {}, 1)
        if existing:
            return {"message": "Products already seeded"}
        sample_products = [
            Product(
                title="Protein Pizza (100g Protein)",
                description="Stone-baked high-protein pizza with 100g protein per pie. Crispy crust, low-carb.",
                price=14.99,
                category="food",
                in_stock=True,
                image="https://images.unsplash.com/photo-1542281286-9e0a16bb7366",
                protein_grams=100,
                calories=980,
                tags=["pizza","high-protein","meal"]
            ),
            Product(
                title="Whey Protein Powder (2lb)",
                description="Ultra-filtered whey with 24g protein per scoop. Mixes instantly.",
                price=29.99,
                category="powder",
                in_stock=True,
                image="https://images.unsplash.com/photo-1517673400267-0251440c45dc",
                protein_grams=24,
                calories=120,
                tags=["powder","whey","shake"]
            ),
            Product(
                title="Vegan Protein Blend (2lb)",
                description="Pea + rice protein for a complete amino acid profile.",
                price=32.99,
                category="powder",
                in_stock=True,
                image="https://images.unsplash.com/photo-1517957754645-708b06a1bbb2",
                protein_grams=22,
                calories=110,
                tags=["vegan","powder"]
            ),
            Product(
                title="Protein Cookies (12-pack)",
                description="Soft-baked cookies with 16g protein per cookie.",
                price=19.99,
                category="snack",
                in_stock=True,
                image="https://images.unsplash.com/photo-1547414362-527f27b7b797",
                protein_grams=16,
                calories=220,
                tags=["snack","cookie"]
            )
        ]
        for p in sample_products:
            create_document("product", p)
        return {"message": "Seeded sample products"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------- Orders ----------------------

@app.post("/api/orders")
def create_order(order: Order):
    try:
        order_id = create_document("order", order)
        return {"id": order_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
