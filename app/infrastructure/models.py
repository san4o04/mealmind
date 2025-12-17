import uuid
import datetime as dt

from sqlalchemy import String, Integer, Numeric, ForeignKey, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db import Base

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


def uuid_pk():
    return mapped_column(primary_key=True, default=uuid.uuid4)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
    )

    sex: Mapped[str] = mapped_column(String(10))
    age: Mapped[int] = mapped_column(Integer)
    height_cm: Mapped[int] = mapped_column(Integer)
    weight_kg: Mapped[int] = mapped_column(Integer)

    goal: Mapped[str] = mapped_column(String(20))
    activity_level: Mapped[str] = mapped_column(String(20))
    budget_kzt_per_day: Mapped[int] = mapped_column(Integer)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    kcal_per_100g: Mapped[int] = mapped_column(Integer)
    protein_per_100g: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    fat_per_100g: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    carbs_per_100g: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    price_kzt_per_100g: Mapped[float] = mapped_column(Numeric(10, 2), default=0)


class MealPlan(Base):
    __tablename__ = "meal_plans"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)

    plan_date: Mapped[dt.date] = mapped_column(Date)
    target_kcal: Mapped[int] = mapped_column(Integer)

    total_cost_kzt: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    items: Mapped[list["MealPlanItem"]] = relationship(
        "MealPlanItem",
        back_populates="meal_plan",
        cascade="all, delete-orphan",
    )


class MealPlanItem(Base):
    __tablename__ = "meal_plan_items"

    id: Mapped[uuid.UUID] = uuid_pk()
    meal_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("meal_plans.id"), index=True)

    meal_type: Mapped[str] = mapped_column(String(20))
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"))

    grams: Mapped[int] = mapped_column(Integer)
    kcal: Mapped[int] = mapped_column(Integer)
    cost_kzt: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    meal_plan: Mapped["MealPlan"] = relationship("MealPlan", back_populates="items")
