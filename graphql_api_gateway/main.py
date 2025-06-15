from fastapi import FastAPI
from ariadne import QueryType, MutationType, InterfaceType, UnionType, make_executable_schema, load_schema_from_path
from ariadne.graphql import GraphQLError
from ariadne.asgi import GraphQL
import os
import requests
from utils import (
    convert_contacts_response_to_camel,
    convert_contact_response_to_camel,
    convert_graphql_input_to_api_payload,
    decode_node_id
)

app = FastAPI(
    title="GraphQL API Gateway",
    description="Gateway that aggregates APIs of Contacts and provides a unified GraphQL interface."
)
type_defs = load_schema_from_path("schema.graphql")
CONTACT_SERVICE_URL = os.getenv("CONTACT_SERVICE_URL", "http://localhost:8000")

query = QueryType()
node_interface = InterfaceType("Node")
create_contact_payload = UnionType("CreateContactPayload")
contact_union = UnionType("ContactUnion")

@query.field("contacts")
async def resolve_contacts(_, info):
    try:
        response = requests.get(f"{CONTACT_SERVICE_URL}/contacts")
        response.raise_for_status() # Gera HTTPError para respostas 4xx/5xx
        contacts = response.json()

        # Convert all contacts to camelCase
        camel_contacts = convert_contacts_response_to_camel(contacts)

        return camel_contacts # Retorna os dados JSON dos contatos
    except requests.exceptions.RequestException as e:
        raise GraphQLError(f"Error fetching contacts: {e}")

@query.field("contact")
async def resolve_contact(_, info, input):
    contact_id = input["contactId"]

    decoded = decode_node_id(contact_id)
    if decoded:
        type_name, entity_id = decoded
        if type_name != "ContactType":
            return {"message": "Invalid contact type"}
        contact_id = entity_id

    try:
        response = requests.get(f"{CONTACT_SERVICE_URL}/contacts/{contact_id}")
        response.raise_for_status() # Gera HTTPError para respostas 4xx/5xx
        contact = response.json()

        camel_contact = convert_contact_response_to_camel(contact)

        return camel_contact
    except requests.exceptions.RequestException as e:
        if "404" in str(e):
            return {"message": f"Contact with ID {contact_id} not found"}
        return {"message": f"Error fetching contact: {e}"}


@query.field("node")
async def resolve_node(_, info, id):
    """
    Resolve a Node by its globally unique ID.
    The ID format is base64(TypeName:entity_id)
    """
    decoded = decode_node_id(id)
    if not decoded:
        raise GraphQLError("Invalid Node ID format")

    type_name, entity_id = decoded

    if type_name == "ContactType":
        try:
            response = requests.get(f"{CONTACT_SERVICE_URL}/contacts/{entity_id}")
            response.raise_for_status()
            contact = response.json()
            return convert_contact_response_to_camel(contact)
        except requests.exceptions.RequestException as e:
            if "404" in str(e):
                return None  # Node not found
            raise GraphQLError(f"Error fetching contact: {e}")

    # For unknown types, return None
    return None


@node_interface.type_resolver
def resolve_node_type(obj, *_):
    """
    Determine the concrete type of a Node interface object.
    """
    if isinstance(obj, dict):
        # Check if this looks like a contact
        if "name" in obj and "category" in obj and "phoneNumbers" in obj:
            return "ContactType"

    return None


@create_contact_payload.type_resolver
def resolve_create_contact_payload_type(obj, *_):
    """
    Determine the concrete type of a CreateContactPayload union object.
    """
    if isinstance(obj, dict):
        if "message" in obj:
            return "ErrorType"
        elif "name" in obj and "category" in obj:
            return "ContactType"
    return None


@contact_union.type_resolver
def resolve_contact_union_type(obj, *_):
    """
    Determine the concrete type of a ContactUnion object.
    """
    if isinstance(obj, dict):
        if "message" in obj:
            return "ErrorType"
        elif "name" in obj and "category" in obj:
            return "ContactType"
    return None


mutation = MutationType()

@mutation.field("createContact")
async def resolve_create_contact(_, info, input):
    # Convert GraphQL input to API payload format
    payload = convert_graphql_input_to_api_payload(input)

    try:
        response = requests.post(
            f"{CONTACT_SERVICE_URL}/contacts",
            json=payload
        )
        response.raise_for_status()
        contact = response.json()

        # Convert contact response to camelCase
        camel_contact = convert_contact_response_to_camel(contact)

        return camel_contact
    except requests.exceptions.RequestException as e:
        if "400" in str(e):
            return {"message": "Contact with this name and category already exists"}
        return {"message": f"Error creating contact: {e}"}
    except Exception as e:
        return {"message": f"Internal error in GraphQL Gateway: {e}"}

@mutation.field("updateContact")
async def resolve_update_contact(_, info, input):
    # Decode the Node ID to get the actual entity ID
    decoded = decode_node_id(input["id"])
    if not decoded:
        return {"message": "Invalid contact ID format"}

    type_name, contact_id = decoded
    if type_name != "ContactType":
        return {"message": "Invalid contact type"}

    update_data = None
    try:
        # First, fetch the existing contact to get current values
        get_response = requests.get(f"{CONTACT_SERVICE_URL}/contacts/{contact_id}")
        get_response.raise_for_status()
        existing_contact = get_response.json()

        # Prepare update data by merging existing data with new data
        update_data = {
            "name": input.get("name", existing_contact["name"]),
            "category": input.get("category", existing_contact["category"])
        }

        # Handle phone numbers conversion
        if "phoneNumbers" in input:
            # Convert from GraphQL format to API format
            phone_numbers_snake = []
            for phone in input["phoneNumbers"]:
                phone_numbers_snake.append({
                    "number": phone["number"],
                    "type_number": phone["typeNumber"]
                })
            update_data["phone_numbers"] = phone_numbers_snake
        else:
            # Use existing phone numbers (already in correct format)
            update_data["phone_numbers"] = existing_contact["phone_numbers"]

        # Send the complete update payload
        response = requests.put(
            f"{CONTACT_SERVICE_URL}/contacts/{contact_id}",
            json=update_data
        )

        response.raise_for_status()
        contact = response.json()
        camel_contact = convert_contact_response_to_camel(contact)

        return camel_contact
    except requests.exceptions.RequestException as e:
        if "404" in str(e):
            return {"message": f"Contact {contact_id} not found"}
        elif "422" in str(e):
            try:
                if hasattr(e, 'response') and e.response is not None:
                    error_detail = e.response.json()
                    return {"message": f"Validation error updating contact: {error_detail}"}
                else:
                    payload_info = f"Payload: {update_data}" if update_data else "No payload data"
                    return {"message": f"Validation error updating contact. {payload_info}"}
            except:
                payload_info = f"Payload: {update_data}" if update_data else "No payload data"
                return {"message": f"Validation error updating contact. {payload_info}"}
        return {"message": f"Error updating contact: {e}"}
    except Exception as e:
        return {"message": f"Internal error in GraphQL Gateway: {e}"}

@mutation.field("deleteContact")
async def resolve_delete_contact(_, info, input):
    # Decode the Node ID to get the actual entity ID
    decoded = decode_node_id(input["id"])
    if not decoded:
        return {"message": "Invalid contact ID format"}

    type_name, contact_id = decoded
    if type_name != "ContactType":
        return {"message": "Invalid contact type"}
    try:
        response = requests.delete(f"{CONTACT_SERVICE_URL}/contacts/{contact_id}")
        response.raise_for_status()
        return {"message": "Contact deleted successfully"}
    except requests.exceptions.RequestException as e:
        if "404" in str(e):
            return {"message": f"Contact with ID {contact_id} not found"}
        return {"message": f"Error deleting contact: {e}"}
    except Exception as e:
        return {"message": f"Internal error in GraphQL Gateway: {e}"}

schema = make_executable_schema(type_defs, query, mutation, node_interface, create_contact_payload, contact_union)

app.mount("/graphql", GraphQL(schema, debug=True)) # debug=True para habilitar o GraphQL IDE
