from __future__ import annotations

from dataclasses import asdict
from datetime import date

from pgvector.sqlalchemy import Vector
from sqlalchemy import Date, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column


# Define the models
class Base(DeclarativeBase, MappedAsDataclass):
    pass


class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column()
    brand: Mapped[str] = mapped_column()
    name: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    price: Mapped[float] = mapped_column()
    embedding: Mapped[Vector] = mapped_column(Vector(1536))  # ada-002

    def to_dict(self, include_embedding: bool = False):
        model_dict = asdict(self)
        if include_embedding:
            model_dict["embedding"] = model_dict["embedding"].tolist()
        else:
            del model_dict["embedding"]
        return model_dict

    def to_str_for_rag(self):
        return f"Name:{self.name} Description:{self.description} Price:{self.price} Brand:{self.brand} Type:{self.type}"

    def to_str_for_embedding(self):
        return f"Name: {self.name} Description: {self.description} Type: {self.type}"


class Kefi_Event(Base):
    __tablename__ = "kefi_events"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    category: Mapped[str] = mapped_column()
    price: Mapped[float] = mapped_column()
    start_date: Mapped[str] = mapped_column()
    start_date_typed: Mapped[date] = mapped_column(Date)
    embedding: Mapped[Vector] = mapped_column(Vector(1536))  # ada-002

    def to_dict(self, include_embedding: bool = False):
        model_dict = asdict(self)
        if include_embedding:
            model_dict["embedding"] = model_dict["embedding"].tolist()
        else:
            del model_dict["embedding"]
        return model_dict

    def to_str_for_rag(self):
        return f"Name:{self.name} Description:{self.description} Category:{self.category} Price:{self.price} Start Date:{self.start_date_typed}"

    def to_str_for_embedding(self):
        return f"Name: {self.name} Description: {self.description} Category: {self.category}"


# Define HNSW index to support vector similarity search through the vector_cosine_ops access method (cosine distance).
index = Index(
    "hnsw_index_for_innerproduct_item_embedding",
    Item.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_ip_ops"},
)

event_index = Index(
    "hnsw_index_for_innerproduct_event_embedding",
    Kefi_Event.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_ip_ops"},
)
