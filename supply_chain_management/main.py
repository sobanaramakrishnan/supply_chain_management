from fastapi import FastAPI, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

# Initialize FastAPI and templates
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
# Create tables
models.Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Home Page
@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Manage Products
@app.get("/products/")
def get_products(request: Request, db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    return templates.TemplateResponse("products.html", {"request": request, "products": products})

@app.post("/products/")
def create_product(name: str = Form(...), price: float = Form(...), description: str = Form(...), db: Session = Depends(get_db)):
    product = models.Product(name=name, price=price, description=description)
    db.add(product)
    db.commit()
    return RedirectResponse(url="/products/", status_code=303)

# Manage Inventory
@app.get("/inventory/")
def get_inventory(request: Request, db: Session = Depends(get_db)):
    inventory = db.query(models.Inventory).all()
    products = db.query(models.Product).all()  # Fetch products
    return templates.TemplateResponse("inventory.html", {"request": request, "inventory": inventory, "products": products})


@app.post("/inventory/")
def update_inventory(product_id: int = Form(...), quantity: int = Form(...), db: Session = Depends(get_db)):
    inventory = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
    if not inventory:
        inventory = models.Inventory(product_id=product_id, quantity=quantity)
    else:
        inventory.quantity += quantity
    db.add(inventory)
    db.commit()
    return RedirectResponse(url="/inventory/", status_code=303)
@app.get("/orders/")
def get_orders(request: Request, db: Session = Depends(get_db)):
    orders = db.query(models.Order).all()  # Fetch all orders from the database
    products = db.query(models.Product).all()  # Fetch all products to show in the form
    return templates.TemplateResponse("orders.html", {"request": request, "orders": orders, "products": products})
@app.post("/orders/")
def create_order(product_id: int = Form(...), quantity: int = Form(...), db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        return RedirectResponse(url="/orders/", status_code=303)

    inventory = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
    if not inventory or inventory.quantity < quantity:
        return RedirectResponse(url="/orders/", status_code=303)

    total_price = product.price * quantity
    inventory.quantity -= quantity
    order = models.Order(product_id=product_id, quantity=quantity, total_price=total_price)
    db.add(order)
    db.commit()

    return RedirectResponse(url="/orders/", status_code=303)
