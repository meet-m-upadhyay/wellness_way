"""
V2 Region lookup table for IFCT geographic zones.
"""

from sqlalchemy import Column, Integer, String, Text

from app.database.connection import Base


class V2Region(Base):
    """IFCT region code → human-readable region name."""
    __tablename__ = "v2_regions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(Integer, nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
