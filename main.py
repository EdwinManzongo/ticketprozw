from fastapi import FastAPI
from routers import users, events, orders, tickets


app = FastAPI(
    title="Ticket Pro ZW",
    description="Ticket Pro ZW API",
    version="1.0.0",
)

app.include_router(users.router)
app.include_router(events.router)
app.include_router(orders.router)
app.include_router(tickets.router)


@app.get("/")
async def root():
    return {"message": "Welcome to TicketProZW API"}
