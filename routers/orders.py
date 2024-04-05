from fastapi import APIRouter
from schemas import orders as orders_schema
from models import orders as orders_model
from dependencies import db_dependency, HTTPException

router = APIRouter(
    prefix="/api/v1/order"
)


@router.get("/{order_id}")
async def read_order(order_id: int, db: db_dependency):
    result = db.query(orders_model.Orders).filter(orders_model.Orders.id == order_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Order not found")
    return result


@router.post("/")
async def create_order(order: orders_schema.OrderBase, db: db_dependency):
    existing_order = db.query(orders_model.Orders).filter(
        orders_model.Orders.user_id == order.user_id and orders_model.Orders.order_date == order.order_date).first()

    if existing_order:
        raise HTTPException(status_code=400, detail="Order already exists")
    else:
        db_order = orders_model.Orders(
            user_id=order.user_id, event_id=order.event_id, order_date=order.order_date, total_price=order.total_price,
            payment_method=order.payment_method, payment_status=order.payment_status
        )
        db.add(db_order)
        db.commit()
        return {"statusCode": 200, "message": "Order created successfully"}