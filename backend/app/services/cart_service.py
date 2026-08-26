from sqlalchemy.orm import Session

from app.models.models import Cart, CartItem, Product


def get_or_create_cart(
    db: Session,
    customer_id: str | None = None,
) -> Cart:
    cart = (
        db.query(Cart)
        .filter(
            Cart.customer_id == customer_id,
            Cart.status == "active",
        )
        .first()
    )

    if cart is None:
        cart = Cart(
            customer_id=customer_id,
            status="active",
            subtotal=0,
            total=0,
        )

        db.add(cart)
        db.commit()
        db.refresh(cart)

    return cart


def recalculate_cart(cart: Cart) -> Cart:
    cart.subtotal = sum(
        item.quantity * item.unit_price
        for item in cart.items
    )

    cart.total = cart.subtotal

    return cart


def add_to_cart(
    db: Session,
    cart: Cart,
    product_id: int,
    quantity: int = 1,
) -> Cart:
    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero"
        )

    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if product is None:
        raise ValueError(
            f"Product {product_id} not found"
        )

    if product.inventory < quantity:
        raise ValueError(
            f"Insufficient inventory for {product.name}"
        )

    item = (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product.id,
        )
        .first()
    )

    if item is None:
        item = CartItem(
            cart_id=cart.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=product.price,
        )

        db.add(item)
    else:
        new_quantity = item.quantity + quantity

        if product.inventory < new_quantity:
            raise ValueError(
                f"Insufficient inventory for {product.name}"
            )

        item.quantity = new_quantity
        item.unit_price = product.price

    db.flush()
    db.refresh(cart)

    recalculate_cart(cart)

    db.commit()
    db.refresh(cart)

    return cart


def remove_from_cart(
    db: Session,
    cart: Cart,
    product_id: int,
) -> Cart:
    item = (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id,
        )
        .first()
    )

    if item is None:
        raise ValueError(
            f"Product {product_id} is not in the cart"
        )

    db.delete(item)
    db.flush()

    db.refresh(cart)

    recalculate_cart(cart)

    db.commit()
    db.refresh(cart)

    return cart


def validate_checkout(
    cart: Cart,
) -> Cart:
    if cart.status != "active":
        raise ValueError(
            "Cart is not active"
        )

    if not cart.items:
        raise ValueError(
            "Cart is empty"
        )

    recalculate_cart(cart)

    if cart.total <= 0:
        raise ValueError(
            "Cart total must be greater than zero"
        )

    return cart