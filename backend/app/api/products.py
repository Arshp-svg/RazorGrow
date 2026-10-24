from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.auth_dependencies import get_current_merchant_context, require_merchant_roles
from app.auth.roles import MerchantRole
from app.db.database import SessionLocal
from app.models.models import Product
from app.schemas.product import ProductResponse, ProductCreate


router = APIRouter(prefix="/products", tags=["products"])


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def parse_list(value: str) -> list[str]:
    if not value:
        return []

    return [item.strip() for item in value.split(",") if item.strip()]


def parse_int_list(value: str) -> list[int]:
    if not value:
        return []

    return [
        int(item.strip())
        for item in value.split(",")
        if item.strip()
    ]


def product_to_response(product: Product) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        name=product.name,
        price=product.price,
        category=product.category,
        tags=parse_list(product.tags),
        use_cases=parse_list(product.use_cases),
        compatible_products=parse_int_list(product.compatible_products),
        upsell_products=parse_int_list(product.upsell_products),
        inventory=product.inventory,
    )


@router.get("", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db),
                 merchant_context=Depends(get_current_merchant_context),):
    products = (
    db.query(Product)
    .filter(Product.merchant_id == merchant_context[0].id)
    .all()
)

    return [product_to_response(product) for product in products]


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db),
                merchant_context=Depends(get_current_merchant_context),
                ):
    product = (
    db.query(Product)
    .filter(
        Product.id == product_id,
        Product.merchant_id == merchant_context[0].id,
    )
    .first()
)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product_to_response(product)


@router.get("/{product_id}/agent", response_model=ProductResponse)
def get_product_for_agent(
    product_id: int,
    db: Session = Depends(get_db),
    merchant_context=Depends(get_current_merchant_context),
):
    product = (
    db.query(Product)
    .filter(
        Product.id == product_id,
        Product.merchant_id == merchant_context[0].id,
    )
    .first()
)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product_to_response(product)


@router.post("", response_model=ProductResponse)
def create_product(
    request: ProductCreate,
    db: Session = Depends(get_db),
    merchant_context=Depends(
        require_merchant_roles(
            MerchantRole.OWNER,
            MerchantRole.ADMIN,
        )
    ),
):
    merchant = merchant_context[0]

    product = Product(
        merchant_id=merchant.id,
        name=request.name.strip(),
        price=request.price,
        category=request.category.strip().lower(),
        tags=",".join(t.strip() for t in request.tags) if request.tags else "",
        use_cases=",".join(u.strip() for u in request.use_cases) if request.use_cases else "",
        compatible_products=",".join(str(p) for p in request.compatible_products) if request.compatible_products else "",
        upsell_products=",".join(str(p) for p in request.upsell_products) if request.upsell_products else "",
        inventory=request.inventory,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product_to_response(product)


@router.get("/public/{merchant_id}", response_model=list[ProductResponse])
def get_public_products(
    merchant_id: int,
    db: Session = Depends(get_db),
):
    products = (
        db.query(Product)
        .filter(
            Product.merchant_id == merchant_id,
            Product.inventory > 0,
        )
        .all()
    )
    return [product_to_response(product) for product in products]