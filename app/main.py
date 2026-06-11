from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
from typing import List
import httpx 
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from . import crud, models, schemas, auth, database

# Database Initialization
models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="Marco System - Order Management")

# CORS Configuration
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

def get_db():
    db = database.SessionLocal()
    try: yield db
    finally: db.close()

# 📧 إعدادات الإيميل المحدثة بالاسم المستعار (Marco System Support)
conf = ConnectionConfig(
    MAIL_USERNAME = "hayajnehbona@gmail.com", 
    MAIL_PASSWORD = "mdwb doyiv xsy amxl", 
    MAIL_FROM = "hayajnehbona@gmail.com",
    MAIL_FROM_NAME = "Marco System Support", 
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

# ✅ مسار جلب أسعار الصرف (Multi-Currency Integration)
@app.get("/api/currency-rates")
async def get_all_rates():
    api_key = "3fb698a3bf9ce51ae176b090"
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/USD"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            data = response.json()
            if data.get("result") == "success":
                return data['conversion_rates']
            return {"JOD": 0.709, "SAR": 3.75, "TRY": 32.20, "USD": 1}
        except Exception:
            return {"JOD": 0.709, "SAR": 3.75, "TRY": 32.20, "USD": 1}

# 📧 مسار إرسال إيميل ترحيبي احترافي
@app.post("/api/send-welcome-email")
async def send_welcome(payload: schemas.UserEmailSchema):
    html = f"""
    <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; background-color: #f1f5f9; padding: 20px;">
            <div style="background-color: white; padding: 40px; border-radius: 24px; border: 1px solid #e2e8f0; max-width: 500px; margin: auto;">
                <h1 style="color: #10b981; font-size: 28px;">MARCO SYSTEM</h1>
                <h2 style="color: #1e293b;">Welcome to the Family! 🚀</h2>
                <p style="color: #475569; font-size: 16px;">Hello <b>{payload.username}</b>,</p>
                <p style="color: #64748b;">Your account is ready. You can now explore our marketplace and shop effortlessly.</p>
                <br>
                <div style="background: #10b981; color: white; padding: 12px 25px; border-radius: 12px; display: inline-block; font-weight: bold; text-decoration: none;">Account Verified ✅</div>
                <p style="color: #94a3b8; font-size: 11px; margin-top: 30px;">© 2026 Marco System - YU Graduation Project</p>
            </div>
        </body>
    </html>
    """
    message = MessageSchema(
        subject="Welcome to Marco System! ✨",
        recipients=[payload.email],
        body=html,
        subtype=MessageType.html
    )
    fm = FastMail(conf)
    await fm.send_message(message)
    return {"message": "Success: Welcome email sent!"}

# --- 1. User & Authentication ---

@app.post("/users/", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_pwd = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username, 
        email=user.email, 
        hashed_password=hashed_pwd, 
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user: raise HTTPException(status_code=401, detail="Wrong credentials")
    return {
        "access_token": auth.create_access_token(data={"sub": user.username}), 
        "token_type": "bearer", "role": user.role, "id": user.id, "username": user.username
    }

@app.get("/users", response_model=List[schemas.UserResponse])
def get_all_users(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role.lower() != "admin": raise HTTPException(status_code=403, detail="Admin only")
    return db.query(models.User).all()

# --- 2. Product Management ---
@app.get("/products/", response_model=List[schemas.ProductResponse])
def read_products(db: Session = Depends(get_db)):
    # تم تعديلها لتنادي الدالة التي تحسب avg_rating من الـ crud
    return crud.get_products(db)

@app.get("/admin/vendors/{vendor_id}/products", response_model=List[schemas.ProductResponse])
def get_vendor_products_admin(vendor_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role.lower() != "admin": raise HTTPException(status_code=403, detail="Admin only")
    return db.query(models.Product).filter(models.Product.vendor_id == vendor_id).all()

@app.post("/products/", response_model=schemas.ProductResponse)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role.lower() != "admin": raise HTTPException(status_code=403, detail="Admin only")
    return crud.create_product(db, product)

@app.put("/products/{product_id}", response_model=schemas.ProductResponse)
async def update_product(product_id: int, updated_product: schemas.ProductCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product: raise HTTPException(status_code=404, detail="Product not found")
    db_product.name, db_product.description, db_product.price, db_product.stock_quantity = updated_product.name, updated_product.description, updated_product.price, updated_product.stock_quantity
    db.commit()
    db.refresh(db_product)
    crud.recheck_pending_orders(db, product_id)
    return db_product

# --- 3. Admin Reports & Control ---
@app.get("/admin/vendors-report")
def get_vendors_report(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role.lower() != "admin": raise HTTPException(status_code=403, detail="Admin only")
    vendors = db.query(models.User).filter(models.User.role == "vendor").all()
    report = []
    for v in vendors:
        p_count = db.query(models.Product).filter(models.Product.vendor_id == v.id).count()
        items = db.query(models.OrderItem).join(models.Product).filter(models.Product.vendor_id == v.id).all()
        total_units = sum(item.quantity for item in items)
        total_rev = sum(item.quantity * item.price_at_purchase for item in items)
        report.append({"id": v.id, "username": v.username, "products_count": p_count, "units_sold": total_units, "revenue": total_rev})
    return report

# --- 4. Order Management ---
@app.get("/orders", response_model=List[schemas.OrderResponse])
def read_all_orders(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role.lower() != "admin": raise HTTPException(status_code=403)
    return db.query(models.Order).options(joinedload(models.Order.items).joinedload(models.OrderItem.product).joinedload(models.Product.owner), joinedload(models.Order.history)).all()

@app.get("/vendor/orders", response_model=List[schemas.OrderResponse])
async def get_vendor_orders(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    if current_user.role.lower() != "vendor": raise HTTPException(status_code=403)
    orders = db.query(models.Order).options(joinedload(models.Order.items).joinedload(models.OrderItem.product), joinedload(models.Order.history)).join(models.OrderItem).join(models.Product).filter(models.Product.vendor_id == current_user.id).distinct().all()
    filtered_results = []
    for order in orders:
        vendor_items = [i for i in order.items if i.product.vendor_id == current_user.id]
        vendor_total = sum(item.quantity * item.price_at_purchase for item in vendor_items)
        filtered_results.append({"id": order.id, "status": order.status, "total_price": vendor_total, "created_at": order.created_at, "updated_at": order.updated_at, "items": vendor_items, "history": order.history})
    return filtered_results

@app.patch("/orders/{order_id}/status", response_model=schemas.OrderResponse)
def update_status(order_id: int, data: schemas.OrderStatusUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    try: return crud.update_order_status(db, order_id, data.status, current_user, f"[{current_user.username}]: {data.note}")
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))

@app.get("/orders/my", response_model=List[schemas.OrderResponse])
def read_my_orders(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return crud.get_orders_by_user(db, current_user.id)

@app.post("/orders/", response_model=schemas.OrderResponse)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return crud.create_order(db, order, current_user.id)

@app.post("/orders/{order_id}/cancel", response_model=schemas.OrderResponse)
def cancel_order_api(order_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    try: return crud.cancel_order(db, order_id, current_user)
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))

# ✅ --- 5. Review Management (جديد) ---
@app.post("/reviews/", response_model=schemas.ReviewResponse)
def create_product_review(
    review: schemas.ReviewCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    return crud.create_review(db=db, review_data=review, user_id=current_user.id)

# --- 6. Manual Recheck ---
@app.post("/admin/recheck-all-orders")
def recheck_all_orders_manually(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.role.lower() != "admin": raise HTTPException(status_code=403)
    for p in db.query(models.Product).filter(models.Product.stock_quantity > 0).all(): crud.recheck_pending_orders(db, p.id)
    return {"message": "Success!"}