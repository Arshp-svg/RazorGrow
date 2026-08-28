from sqlalchemy import (Float, Integer, String, Column, ForeignKey, Boolean)
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    price: Mapped[float] = mapped_column(Float)

    category: Mapped[str] = mapped_column(String(100))
    tags: Mapped[str] = mapped_column(String(500), default="")
    use_cases: Mapped[str] = mapped_column(String(500), default="")

    compatible_products: Mapped[str] = mapped_column(
        String(500),
        default="",
    )

    upsell_products: Mapped[str] = mapped_column(
        String(500),
        default="",
    )

    inventory: Mapped[int] = mapped_column(Integer, default=0)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.id"),
        nullable=False,
    )

    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="created",
    )

    razorpay_order_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    

class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(String, nullable=True)

    status = Column(
        String,
        nullable=False,
        default="active",
    )

    subtotal = Column(
        Float,
        nullable=False,
        default=0,
    )

    total = Column(
        Float,
        nullable=False,
        default=0,
    )

    items = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan",
    )


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)

    cart_id = Column(
        Integer,
        ForeignKey("carts.id"),
        nullable=False,
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False,
    )

    quantity = Column(
        Integer,
        nullable=False,
        default=1,
    )

    unit_price = Column(
        Float,
        nullable=False,
    )

    cart = relationship(
        "Cart",
        back_populates="items",
    )

    product = relationship("Product")
    

class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)

    max_order_amount = Column(
        Float,
        nullable=False,
        default=100000,
    )

    max_discount = Column(
        Float,
        nullable=False,
        default=0,
    )

    confirmation_required = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    approval_threshold = Column(
        Float,
        nullable=True,
        default=None,
    )