from fastapi import APIRouter
from schemas import tickets as tickets_schema
from models import tickets as tickets_model
from dependencies import db_dependency, HTTPException

router = APIRouter(
    prefix="/api/v1/ticket"
)


@router.get("/{ticket_id}")
async def read_ticket(ticket_id: int, db: db_dependency):
    result = db.query(tickets_model.Tickets).filter(tickets_model.Tickets.id == ticket_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return result


@router.post("/")
async def create_ticket(ticket: tickets_schema.TicketBase, db: db_dependency):
    existing_ticket = db.query(tickets_model.Tickets).filter(
        tickets_model.Tickets.order_id == ticket.order_id and
        tickets_model.Tickets.ticket_type_id == ticket.ticket_type_id).first()

    if existing_ticket:
        raise HTTPException(status_code=400, detail="Ticket already exists")
    else:
        db_tickets = tickets_model.Tickets(
            order_id=ticket.order_id, ticket_type_id=ticket.ticket_type_id, seat_number=ticket.seat_number,
            qr_code=ticket.qr_code, checked_in=ticket.checked_in, checked_out=ticket.checked_out
        )
        db.add(db_tickets)
        db.commit()
        return {"statusCode": 200, "message": "Ticket successfully created"}


@router.get("/types/{ticket_type_id}")
async def read_ticket_type(ticket_type_id: int, db: db_dependency):
    # tickets_model.TicketTypes.event_id == event_id and
    result = db.query(tickets_model.TicketTypes).filter(tickets_model.TicketTypes.id == ticket_type_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Ticket type not found")
    return result


@router.post("/types/")
async def create_ticket_type(ticket_type: tickets_schema.TicketTypeBase, db: db_dependency):
    # tickets_model.TicketTypes.event_id == ticket_type.event_id and
    existing_ticket_type = db.query(tickets_model.TicketTypes).filter(
        tickets_model.TicketTypes.name == ticket_type.name).first()
    if existing_ticket_type:
        raise HTTPException(status_code=400, detail="Ticket type already exists")

    db_ticket_type = tickets_model.TicketTypes(
        event_id=ticket_type.event_id, name=ticket_type.name, description=ticket_type.description,
        price=ticket_type.price, quantity=ticket_type.quantity
    )
    db.add(db_ticket_type)
    db.commit()
    # Optional: To return the newly created ticket type
    # db.refresh(db_ticket_type)
    # return db_ticket_type
    return {"statusCode": 200, "message": "Ticket type created successfully"}


@router.get("/all/types/")
async def read_all_ticket_type(db: db_dependency):
    result = db.query(tickets_model.TicketTypes).all()
    return result
