import re
import base64
from typing import Dict, Any, List, Optional, Tuple


def snake_to_camel(snake_str: str) -> str:
    """
    Convert snake_case string to camelCase.

    Examples:
        snake_to_camel("phone_numbers") -> "phoneNumbers"
        snake_to_camel("contact_id") -> "contactId"
        snake_to_camel("type_number") -> "typeNumber"
    """
    components = snake_str.split('_')
    return components[0] + ''.join(word.capitalize() for word in components[1:])


def camel_to_snake(camel_str: str) -> str:
    """
    Convert camelCase string to snake_case.

    Examples:
        camel_to_snake("phoneNumbers") -> "phone_numbers"
        camel_to_snake("contactId") -> "contact_id"
        camel_to_snake("typeNumber") -> "type_number"
    """
    return re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()


def convert_dict_keys_to_camel(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively convert all dictionary keys from snake_case to camelCase.

    Args:
        data: Dictionary with snake_case keys

    Returns:
        Dictionary with camelCase keys
    """
    if isinstance(data, dict):
        converted = {}
        for key, value in data.items():
            new_key = snake_to_camel(key)
            if isinstance(value, dict):
                converted[new_key] = convert_dict_keys_to_camel(value)
            elif isinstance(value, list):
                converted[new_key] = convert_list_to_camel(value)
            else:
                converted[new_key] = value
        return converted
    return data


def convert_list_to_camel(data: List[Any]) -> List[Any]:
    """
    Recursively convert list items from snake_case to camelCase.

    Args:
        data: List that may contain dictionaries with snake_case keys

    Returns:
        List with camelCase keys in nested dictionaries
    """
    converted_list = []
    for item in data:
        if isinstance(item, dict):
            converted_list.append(convert_dict_keys_to_camel(item))
        elif isinstance(item, list):
            converted_list.append(convert_list_to_camel(item))
        else:
            converted_list.append(item)
    return converted_list


def convert_dict_keys_to_snake(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively convert all dictionary keys from camelCase to snake_case.

    Args:
        data: Dictionary with camelCase keys

    Returns:
        Dictionary with snake_case keys
    """
    if isinstance(data, dict):
        converted = {}
        for key, value in data.items():
            new_key = camel_to_snake(key)
            if isinstance(value, dict):
                converted[new_key] = convert_dict_keys_to_snake(value)
            elif isinstance(value, list):
                converted[new_key] = convert_list_to_snake(value)
            else:
                converted[new_key] = value
        return converted
    return data


def convert_list_to_snake(data: List[Any]) -> List[Any]:
    """
    Recursively convert list items from camelCase to snake_case.

    Args:
        data: List that may contain dictionaries with camelCase keys

    Returns:
        List with snake_case keys in nested dictionaries
    """
    converted_list = []
    for item in data:
        if isinstance(item, dict):
            converted_list.append(convert_dict_keys_to_snake(item))
        elif isinstance(item, list):
            converted_list.append(convert_list_to_snake(item))
        else:
            converted_list.append(item)
    return converted_list


def convert_contact_response_to_camel(contact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a contact response from snake_case to camelCase with specific handling
    for phone_numbers field and Node ID encoding.

    Args:
        contact: Contact dictionary from the API response

    Returns:
        Contact dictionary with camelCase field names and encoded Node ID
    """
    if isinstance(contact, dict) and "phone_numbers" in contact:
        # Handle phone_numbers specifically
        phone_numbers_camel = []
        for phone in contact["phone_numbers"]:
            phone_numbers_camel.append({
                "number": phone["number"],
                "typeNumber": phone["type_number"]
            })

        # Create new contact dict with camelCase
        camel_contact = convert_dict_keys_to_camel(contact)
        camel_contact["phoneNumbers"] = phone_numbers_camel

        # Remove the old snake_case field if it exists
        if "phone_numbers" in camel_contact:
            del camel_contact["phone_numbers"]

        # Encode the ID as a Node ID
        if "id" in camel_contact:
            camel_contact["id"] = encode_node_id("ContactType", str(camel_contact["id"]))

        return camel_contact

    # For non-contact dictionaries or dictionaries without phone_numbers
    converted = convert_dict_keys_to_camel(contact)

    # If this is a contact (has typical contact fields), encode the ID
    if isinstance(converted, dict) and "id" in converted and ("name" in converted or "category" in converted):
        converted["id"] = encode_node_id("ContactType", str(converted["id"]))

    return converted


def convert_phone_numbers_input_to_snake(phone_numbers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert phoneNumbers input from camelCase to snake_case for API calls.

    Args:
        phone_numbers: List of phone number dictionaries with camelCase keys

    Returns:
        List of phone number dictionaries with snake_case keys
    """
    phone_numbers_snake = []
    for phone in phone_numbers:
        phone_numbers_snake.append({
            "number": phone["number"],
            "type_number": phone["typeNumber"]
        })
    return phone_numbers_snake


def convert_contacts_response_to_camel(contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert a list of contacts from snake_case to camelCase.

    Args:
        contacts: List of contact dictionaries from API response

    Returns:
        List of contact dictionaries with camelCase field names
    """
    return [convert_contact_response_to_camel(contact) for contact in contacts]


def convert_graphql_input_to_api_payload(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert GraphQL input data to API payload format.
    Handles both general field conversion and specific phone number conversion.

    Args:
        input_data: GraphQL input dictionary with camelCase keys

    Returns:
        API payload dictionary with snake_case keys
    """
    payload = {}

    for key, value in input_data.items():
        if key == "phoneNumbers" and value:
            payload["phone_numbers"] = convert_phone_numbers_input_to_snake(value)
        else:
            snake_key = camel_to_snake(key)
            payload[snake_key] = value

    return payload


def encode_node_id(type_name: str, entity_id: str) -> str:
    """
    Encode a Node ID by combining type name and entity ID with base64 encoding.

    Args:
        type_name: The GraphQL type name (e.g., "ContactType")
        entity_id: The entity's internal ID

    Returns:
        Base64 encoded string in format: base64(type_name:entity_id)
    """
    combined = f"{type_name}:{entity_id}"
    encoded_bytes = base64.b64encode(combined.encode('utf-8'))
    return encoded_bytes.decode('utf-8')


def decode_node_id(node_id: str) -> Optional[Tuple[str, str]]:
    """
    Decode a Node ID to extract type name and entity ID.

    Args:
        node_id: Base64 encoded Node ID

    Returns:
        Tuple of (type_name, entity_id) or None if invalid
    """
    try:
        decoded_bytes = base64.b64decode(node_id.encode('utf-8'))
        decoded_string = decoded_bytes.decode('utf-8')

        if ':' not in decoded_string:
            return None

        type_name, entity_id = decoded_string.split(':', 1)
        return (type_name, entity_id)
    except Exception:
        return None
