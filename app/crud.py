from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from . import models, schemas

# --- 1. قوانين الانتقال بين الحالات ---
ALLOWED_TRANSITIONS = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["processing", "cancelled"],
    "processing": ["shipped", "cancelled"],
    "shipped": ["delivered"],
    "delivered": [],
    "cancelled": []
}

# ✅ إضافة ميزة التقييم (CRUD)
def create_review(db: Session, review_data: schemas.ReviewCreate, user_id: int):
    db_review = models.Review(
        product_id=review_data.product_id,
        user_id=user_id,
        rating=review_data.rating,
        comment=review_data.comment
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

# --- 2. إنشاء طلب جديد مع فحص آلي للمخزن ---
def create_order(db: Session, order_data: schemas.OrderCreate, user_id: int):
    total_price = 0
    items_list = order_data.dict().get('items', [])
    
    can_auto_confirm = True
    for item in items_list:
        product = db.query(models.Product).filter(models.Product.id == item['product_id']).first()
        if not product or product.stock_quantity < item['quantity']:
            can_auto_confirm = False
            break

    initial_status = "confirmed" if can_auto_confirm else "pending"
    db_order = models.Order(user_id=user_id, total_price=0, status=initial_status)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    current_total = 0
    for item in items_list:
        product = db.query(models.Product).filter(models.Product.id == item['product_id']).first()
        price_at_order = product.price
        current_total += price_at_order * item['quantity']
        
        db.add(models.OrderItem(
            order_id=db_order.id, 
            product_id=product.id, 
            quantity=item['quantity'], 
            price_at_purchase=price_at_order
        ))
        
        if can_auto_confirm:
            product.stock_quantity -= item['quantity']

    db_order.total_price = current_total
    note = "System: Order confirmed automatically" if can_auto_confirm else "System: Order pending"
    db.add(models.OrderStatusHistory(order_id=db_order.id, new_status=initial_status, changed_by=user_id, role="system", note=note))
    
    db.commit()
    db.refresh(db_order)
    return db_order

# --- 3. تحديث الحالة يدوياً ---
def update_order_status(db: Session, order_id: int, new_status: str, user: models.User, note: str = None):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order: return None
    
    current = db_order.status.lower()
    target = new_status.lower()

    if user.role.lower() != "admin":
        if target not in ALLOWED_TRANSITIONS.get(current, []):
            raise Exception(f"Cannot change status from {current} to {target}")

    db_order.status = target
    db.add(models.OrderStatusHistory(order_id=order_id, old_status=current, new_status=target, changed_by=user.id, role=user.role, note=note))
    db.commit()
    db.refresh(db_order)
    return db_order

# --- 4. إلغاء الطلب مع إرجاع المخزن ---
def cancel_order(db: Session, order_id: int, user: models.User):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order: return None
    if db_order.status.lower() in ["confirmed", "processing"]:
        for item in db_order.items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
            if product: product.stock_quantity += item.quantity
    return update_order_status(db, order_id, "cancelled", user, "Order cancelled")

# --- 5. جلب البيانات ---
def get_products(db: Session):
    # ✅ تعديل الدالة لترجع التقييمات بدون تغيير اسمها عشان ما يضرب الـ main.py
    products = db.query(models.Product).filter(models.Product.is_deleted == False).all()
    for product in products:
        avg = db.query(func.avg(models.Review.rating)).filter(models.Review.product_id == product.id).scalar()
        product.avg_rating = float(avg) if avg else 0.0
    return products

def get_orders_by_user(db: Session, user_id: int):
    return db.query(models.Order).options(
        joinedload(models.Order.items).joinedload(models.OrderItem.product).joinedload(models.Product.owner),
        joinedload(models.Order.history)
    ).filter(models.Order.user_id == user_id).all()

def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

# --- 6. إعادة فحص الطلبات العالقة عند زيادة الستوك ---
def recheck_pending_orders(db: Session, product_id: int):
    pending_orders = db.query(models.Order).join(models.OrderItem).filter(
        models.Order.status == "pending",
        models.OrderItem.product_id == product_id
    ).all()

    for order in pending_orders:
        can_confirm = True
        for item in order.items:
            if item.product.stock_quantity < item.quantity:
                can_confirm = False
                break
        
        if can_confirm:
            for item in order.items:
                item.product.stock_quantity -= item.quantity
            
            order.status = "confirmed"
            db.add(models.OrderStatusHistory(
                order_id=order.id, new_status="confirmed", 
                changed_by=0, role="system", note="System: Auto-confirmed"
            ))
    db.commit()