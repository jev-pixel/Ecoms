# E-Commerce Service with FastAPI and SQLite
# Install required packages: pip install fastapi uvicorn sqlalchemy

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uvicorn

# Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./ecommerce.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    category = Column(String)
    
    order_items = relationship("OrderItem", back_populates="item")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=False)
    total_amount = Column(Float, default=0.0)
    status = Column(String, default="pending")  # pending, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    
    order = relationship("Order", back_populates="order_items")
    item = relationship("Item", back_populates="order_items")

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Schemas
class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    category: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemResponse(ItemBase):
    id: int
    
    class Config:
        from_attributes = True

class OrderItemCreate(BaseModel):
    item_id: int
    quantity: int = Field(gt=0)

class OrderItemResponse(BaseModel):
    id: int
    item_id: int
    item_name: str
    quantity: int
    unit_price: float
    subtotal: float
    
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    customer_name: str
    customer_email: str
    items: List[OrderItemCreate]

class OrderUpdate(BaseModel):
    quantity: Optional[int] = Field(None, gt=0)
    status: Optional[str] = None

class OrderResponse(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    total_amount: float
    status: str
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]
    
    class Config:
        from_attributes = True

class SalesTransaction(BaseModel):
    order_id: int
    customer_name: str
    customer_email: str
    total_amount: float
    status: str
    item_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize FastAPI
app = FastAPI(title="E-Commerce API", version="1.0.0")

# Helper function to seed database with sample items
def seed_database():
    db = SessionLocal()
    if db.query(Item).count() == 0:
        sample_items = [
            Item(name="fuck", description="High-performance laptop", price=999.99, stock=50, category="Electronics"),
            Item(name="bwesit Mouse", description="Ergonomic wireless mouse", price=29.99, stock=200, category="Electronics"),
            Item(name="Keyboard", description="Mechanical gaming keyboard", price=79.99, stock=150, category="Electronics"),
            Item(name="Monitor", description="27-inch 4K monitor", price=349.99, stock=75, category="Electronics"),
            Item(name="USB Cable", description="USB-C charging cable", price=12.99, stock=500, category="Accessories"),
            Item(name="kingina", description="USB-C charging cable", price=12.99, stock=500, category="Accessories"),
        ]
        db.add_all(sample_items)
        db.commit()
    db.close()

# Seed database on startup
@app.on_event("startup")
def startup_event():
    seed_database()

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "E-Commerce API",
        "version": "1.0.0",
        "endpoints": {
            "items": "/api/items",
            "orders": "/api/orders",
            "transactions": "/api/transactions"
        }
    }

# ==================== GET APIs ====================

@app.get("/api/items", response_model=List[ItemResponse])
def get_all_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all items in the inventory"""
    items = db.query(Item).offset(skip).limit(limit).all()
    return items

@app.get("/api/items/{item_id}", response_model=ItemResponse)
def get_item_by_id(item_id: int, db: Session = Depends(get_db)):
    """Get a specific item by ID"""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item with id {item_id} not found")
    return item

@app.get("/api/transactions", response_model=List[SalesTransaction])
def get_all_sales_transactions(
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all sales transactions (orders)"""
    query = db.query(Order)
    
    if status:
        query = query.filter(Order.status == status)
    
    orders = query.offset(skip).limit(limit).all()
    
    transactions = []
    for order in orders:
        transactions.append(SalesTransaction(
            order_id=order.id,
            customer_name=order.customer_name,
            customer_email=order.customer_email,
            total_amount=order.total_amount,
            status=order.status,
            item_count=len(order.order_items),
            created_at=order.created_at
        ))
    
    return transactions

@app.get("/api/orders/{order_id}", response_model=OrderResponse)
def get_order_by_id(order_id: int, db: Session = Depends(get_db)):
    """Get a specific order by ID"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order with id {order_id} not found")
    
    # Format order items
    items = []
    for order_item in order.order_items:
        items.append(OrderItemResponse(
            id=order_item.id,
            item_id=order_item.item_id,
            item_name=order_item.item.name,
            quantity=order_item.quantity,
            unit_price=order_item.unit_price,
            subtotal=order_item.subtotal
        ))
    
    return OrderResponse(
        id=order.id,
        customer_name=order.customer_name,
        customer_email=order.customer_email,
        total_amount=order.total_amount,
        status=order.status,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=items
    )

# ==================== POST API ====================

@app.post("/api/orders", response_model=OrderResponse, status_code=201)
def add_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    """Add a new order (purchase)"""
    
    # Validate items and check stock
    total_amount = 0.0
    order_items_data = []
    
    for item_data in order_data.items:
        item = db.query(Item).filter(Item.id == item_data.item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail=f"Item with id {item_data.item_id} not found")
        
        if item.stock < item_data.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock for {item.name}. Available: {item.stock}, Requested: {item_data.quantity}"
            )
        
        subtotal = item.price * item_data.quantity
        total_amount += subtotal
        
        order_items_data.append({
            "item": item,
            "quantity": item_data.quantity,
            "unit_price": item.price,
            "subtotal": subtotal
        })
    
    # Create order
    new_order = Order(
        customer_name=order_data.customer_name,
        customer_email=order_data.customer_email,
        total_amount=total_amount,
        status="pending"
    )
    db.add(new_order)
    db.flush()  # Get the order ID
    
    # Create order items and update stock
    for item_data in order_items_data:
        order_item = OrderItem(
            order_id=new_order.id,
            item_id=item_data["item"].id,
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            subtotal=item_data["subtotal"]
        )
        db.add(order_item)
        
        # Update item stock
        item_data["item"].stock -= item_data["quantity"]
    
    db.commit()
    db.refresh(new_order)
    
    return get_order_by_id(new_order.id, db)

# ==================== PUT API ====================

@app.put("/api/orders/{order_id}", response_model=OrderResponse)
def update_order(order_id: int, update_data: OrderUpdate, db: Session = Depends(get_db)):
    """Update an order (quantity or status)"""
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order with id {order_id} not found")
    
    # Update status
    if update_data.status:
        valid_statuses = ["pending", "completed", "cancelled"]
        if update_data.status not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        order.status = update_data.status
    
    # Update quantity (for the first item in order as example)
    if update_data.quantity:
        if not order.order_items:
            raise HTTPException(status_code=400, detail="Order has no items to update")
        
        order_item = order.order_items[0]
        item = order_item.item
        
        # Calculate stock difference
        quantity_diff = update_data.quantity - order_item.quantity
        
        if quantity_diff > 0 and item.stock < quantity_diff:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Available: {item.stock}"
            )
        
        # Update stock
        item.stock -= quantity_diff
        
        # Update order item
        order_item.quantity = update_data.quantity
        order_item.subtotal = order_item.unit_price * update_data.quantity
        
        # Recalculate total
        order.total_amount = sum(oi.subtotal for oi in order.order_items)
    
    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    
    return get_order_by_id(order_id, db)

# ==================== DELETE API ====================

@app.delete("/api/orders/{order_id}", status_code=200)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    """Delete an order and restore stock"""
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order with id {order_id} not found")
    
    # Restore stock for all items in the order
    for order_item in order.order_items:
        item = order_item.item
        item.stock += order_item.quantity
    
    # Delete order (cascade will delete order_items)
    db.delete(order)
    db.commit()
    
    return {
        "message": f"Order {order_id} deleted successfully",
        "order_id": order_id
    }

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)