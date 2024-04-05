from fastapi import APIRouter
from schemas import events as events_schema
from models import events as events_model
from dependencies import db_dependency, HTTPException

router = APIRouter(
    prefix="/api/v1/event"
)


@router.get("/{event_id}")
async def read_event(event_id: int, db: db_dependency):
    result = db.query(events_model.Events).filter(events_model.Events.id == event_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Event not found")
    return result


@router.post("/")
async def create_event(event: events_schema.EventBase, db: db_dependency):
    existing_event = db.query(events_model.Events).filter(events_model.Events.event_name == event.event_name).first()
    if existing_event:
        raise HTTPException(status_code=400, detail="Event already exists")

    db_event = events_model.Events(
        event_name=event.event_name, description=event.description, organizer_id=event.organizer_id,
        location=event.location, date=event.date, image=event.image
    )
    db.add(db_event)
    db.commit()
    # Optional: To return the newly created event
    # db.refresh(db_event)
    # return db_event
    return {"statusCode": 200, "message": "Event created successfully"}