from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    BigInteger
)

from .meta import Base


class UsageLog(Base):
    __tablename__ = 'usagelog'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(BigInteger)
    caller_ip = Column(Text)
    endpoint = Column(Text)
    body = Column(Text)


Index('faillog_idx', UsageLog.id, unique=True)
