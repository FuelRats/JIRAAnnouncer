from sqlalchemy import (
    Column,
    Index,
    Integer,
    BigInteger,
    JSON,
)

from .meta import Base


class TravisMessage(Base):
    __tablename__ = 'travismessage'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(BigInteger)
    payload = Column(JSON)


Index('travis_idx', TravisMessage.id, unique=True)
