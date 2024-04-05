from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Float
from database import Base


class Orders(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    order_date = Column(DateTime, index=True)
    total_price = Column(Float, index=True)
    payment_method = Column(String, index=True)
    payment_status = Column(String, index=True)

