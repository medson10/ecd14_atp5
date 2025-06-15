import enum
from fastapi import FastAPI, HTTPException, Depends, Response
from pydantic import BaseModel, model_validator
from sqlalchemy import create_engine, Column, String, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from typing import List
import uuid

app = FastAPI(
  title="Serviço de Contatos",
  description="Gerencia contatos e seu estoque com persistência em PostgreSQL."
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@postgres-service:5432/mydatabase")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ContactCategory(enum.Enum):
  PERSONAL = "PERSONAL"
  FAMILY = "FAMILY"
  BUSINESS = "BUSINESS"

class ContactDB(Base):
  __tablename__ = "contacts"
  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
  name = Column(String)
  phone_numbers = Column(JSON)
  category = Column(Enum(ContactCategory))

class ContactPhoneNumberType(enum.Enum):
  WORK = "WORK"
  HOME = "HOME"
  MOBILE = "MOBILE"

class ContactPhoneNumber(BaseModel):
  number: str
  type_number: ContactPhoneNumberType

class ContactBase(BaseModel):
  name: str
  category: ContactCategory
  phone_numbers: List[ContactPhoneNumber]

class Contact(ContactBase):
  id: uuid.UUID

  @model_validator(mode='before')
  @classmethod
  def convert_phone_numbers(cls, data):
    if isinstance(data, dict) and 'phone_numbers' in data:
      # Convert JSON phone numbers back to ContactPhoneNumber objects
      phone_numbers = data['phone_numbers']
      if phone_numbers and isinstance(phone_numbers[0], dict):
        converted_phones = []
        for phone in phone_numbers:
          converted_phones.append(ContactPhoneNumber(
            number=phone['number'],
            type_number=ContactPhoneNumberType(phone['type_number'])
          ))
        data['phone_numbers'] = converted_phones
    return data

  class Config:
    from_attributes = True

def create_db_tables():
  Base.metadata.create_all(bind=engine)
  db = SessionLocal()
  try:
    if db.query(ContactDB).count() == 0:
      print("Populating initial contact data...")
      db.add_all([
        ContactDB(
          id=uuid.uuid4(),
          name="John Smith",
          category=ContactCategory.PERSONAL,
          phone_numbers=[
            {"number": "1234567890", "type_number": "MOBILE"},
            {"number": "0987654321", "type_number": "WORK"},
            {"number": "5555555555", "type_number": "HOME"}
          ]
        ),
        ContactDB(
          id=uuid.uuid4(),
          name="Jane Smith",
          category=ContactCategory.PERSONAL,
          phone_numbers=[
            {"number": "1111111111", "type_number": "MOBILE"},
            {"number": "2222222222", "type_number": "WORK"},
            {"number": "3333333333", "type_number": "HOME"}
          ]
        ),
        ContactDB(
          id=uuid.uuid4(),
          name="Jane Doe",
          category=ContactCategory.FAMILY,
          phone_numbers=[
            {"number": "4444444444", "type_number": "MOBILE"},
            {"number": "6666666666", "type_number": "WORK"},
            {"number": "7777777777", "type_number": "HOME"}
          ]
        ),
        ContactDB(
          id=uuid.uuid4(),
          name="John Doe Inc",
          category=ContactCategory.BUSINESS,
          phone_numbers=[
            {"number": "8888888888", "type_number": "MOBILE"},
            {"number": "9999999999", "type_number": "WORK"},
            {"number": "1010101010", "type_number": "HOME"}
          ]
        ),
      ])
      db.commit()
      print("Initial contact data inserted successfully.")
  finally:
    db.close()

@app.on_event("startup")
async def startup_event():
  create_db_tables()
  print(f"Service connected to database: {DATABASE_URL}")

def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()

@app.get("/contacts/{contact_id}", response_model=Contact)
def get_contact(contact_id: str, db = Depends(get_db)):
  contact = db.query(ContactDB).filter(ContactDB.id == uuid.UUID(contact_id)).first()
  if contact is None:
    raise HTTPException(status_code=404, detail="Contact not found")
  return contact

@app.get("/contacts", response_model=list[Contact])
def list_contacts(db = Depends(get_db)):
  return db.query(ContactDB).all()

@app.post("/contacts", status_code=201, response_model=Contact)
def create_contact(contact_data: ContactBase, db = Depends(get_db)):
  db_contact = db.query(ContactDB).filter(ContactDB.name == contact_data.name, ContactDB.category == contact_data.category).first()
  if db_contact:
    raise HTTPException(status_code=400, detail="Contact with this name and category already exists")

  # Convert phone_numbers to JSON-serializable format
  phone_numbers_json = [
    {"number": phone.number, "type_number": phone.type_number.value}
    for phone in contact_data.phone_numbers
  ]

  new_contact = ContactDB(
    name=contact_data.name,
    category=contact_data.category,
    phone_numbers=phone_numbers_json
  )
  db.add(new_contact)
  db.commit()
  db.refresh(new_contact)
  return new_contact

@app.put("/contacts/{contact_id}", status_code=200, response_model=Contact)
def update_contact(contact_id: str, contact_data: ContactBase, db = Depends(get_db)):
  db_contact = db.query(ContactDB).filter(ContactDB.id == uuid.UUID(contact_id)).first()
  if db_contact is None:
    raise HTTPException(status_code=404, detail="Contact not found")

  # Convert phone_numbers to JSON-serializable format
  phone_numbers_json = [
    {"number": phone.number, "type_number": phone.type_number.value}
    for phone in contact_data.phone_numbers
  ]

  db_contact.name = contact_data.name
  db_contact.category = contact_data.category
  db_contact.phone_numbers = phone_numbers_json

  db.commit()
  db.refresh(db_contact)
  return db_contact

@app.delete("/contacts/{contact_id}", status_code=204)
def delete_contact(contact_id: str, db = Depends(get_db)):
  db_contact = db.query(ContactDB).filter(ContactDB.id == uuid.UUID(contact_id)).first()
  if db_contact is None:
    raise HTTPException(status_code=404, detail="Contact not found")

  db.delete(db_contact)
  db.commit()
  return Response(status_code=204)
