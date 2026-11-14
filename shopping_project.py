from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from auth import (
    create_access_token,
    get_current_user,
    hash_password,
    require_admin,
    verify_password,
)
from database import (
    OrderError,
    add_product,
    add_user,
    create_order,
    delete_product,
    get_all_products,
    get_product,
    get_user,
    update_product,
)

app = FastAPI(title="Online Store API")


class UserCreate(BaseModel):
    username: str
    password: str


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    stock: int = Field(default=0, ge=0)


class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    items: list[OrderItemIn] = Field(min_length=1)


def product_to_dict(row):
    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "price": float(row[3]),
        "stock": row[4],
    }


@app.get("/")
def home():
    return {"message": "Online Store API is running"}


@app.post("/register")
def register(user: UserCreate):
    if get_user(user.username) is not None:
        raise HTTPException(status_code=400, detail="Username already exists")
    add_user(user.username, hash_password(user.password))
    return {"message": f"User '{user.username}' registered"}


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    row = get_user(form_data.username)
    if row is None or not verify_password(form_data.password, row[2]):
        raise HTTPException(
            status_code=401, detail="Invalid username or password")
    return {"access_token": create_access_token(row[1]), "token_type": "bearer"}


@app.get("/me")
def read_me(current_user: dict = Depends(get_current_user)):
    return current_user


@app.get("/products")
def list_products():
    return [product_to_dict(row) for row in get_all_products()]


@app.get("/products/{product_id}")
def read_product(product_id: int):
    row = get_product(product_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product_to_dict(row)


@app.post("/products", status_code=201)
def create_product(product: ProductCreate, admin: dict = Depends(require_admin)):
    product_id = add_product(
        product.name, product.description, product.price, product.stock
    )
    return {"id": product_id, "message": "Product created"}


@app.put("/products/{product_id}")
def edit_product(
    product_id: int,
    product: ProductCreate,
    admin: dict = Depends(require_admin),
):
    updated = update_product(
        product_id, product.name, product.description, product.price, product.stock
    )
    if updated == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product updated"}


@app.delete("/products/{product_id}")
def remove_product(product_id: int, admin: dict = Depends(require_admin)):
    deleted = delete_product(product_id)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}


@app.post("/orders", status_code=201)
def place_order(order: OrderCreate, current_user: dict = Depends(get_current_user)):
    items = [item.model_dump() for item in order.items]
    try:
        order_id = create_order(current_user["id"], items)
    except OrderError as error:
        raise HTTPException(status_code=400, detail=str(error))
    return {"order_id": order_id, "message": "Order created"}
