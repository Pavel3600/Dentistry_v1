from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.client_models import Clients
from app.schemas.client_schema import ClientCreateSchema

def create_client(
    data: ClientCreateSchema,
    session: Session
) -> Clients:
    client = Clients(**data.model_dump())
    session.add(client)
    session.commit()
    session.refresh(client)
    return client

def get_clients(session: Session) -> list[Clients]:
    return session.scalars(select(Clients)).all()