# GraphQL API Gateway - Case Conversion Utilities

This GraphQL API Gateway provides seamless integration between GraphQL (which uses camelCase conventions) and Python REST APIs (which use snake_case conventions). The utilities automatically handle field name conversions in both directions.

## Overview

The gateway includes reusable utility functions in `utils.py` that handle the conversion between different naming conventions:

- **GraphQL → Python API**: camelCase → snake_case
- **Python API → GraphQL**: snake_case → camelCase

## Utility Functions

### Basic Conversion Functions

#### `snake_to_camel(snake_str: str) → str`
Converts a single snake_case string to camelCase.

```python
snake_to_camel("phone_numbers")  # → "phoneNumbers"
snake_to_camel("contact_id")     # → "contactId"
snake_to_camel("type_number")    # → "typeNumber"
```

#### `camel_to_snake(camel_str: str) → str`
Converts a single camelCase string to snake_case.

```python
camel_to_snake("phoneNumbers")  # → "phone_numbers"
camel_to_snake("contactId")     # → "contact_id"
camel_to_snake("typeNumber")    # → "type_number"
```

### Dictionary and List Conversion Functions

#### `convert_dict_keys_to_camel(data: Dict[str, Any]) → Dict[str, Any]`
Recursively converts all dictionary keys from snake_case to camelCase.

```python
input_data = {
    "contact_id": "123",
    "phone_numbers": [{"number": "123", "type_number": "MOBILE"}]
}
# Result: {"contactId": "123", "phoneNumbers": [{"number": "123", "typeNumber": "MOBILE"}]}
```

#### `convert_dict_keys_to_snake(data: Dict[str, Any]) → Dict[str, Any]`
Recursively converts all dictionary keys from camelCase to snake_case.

#### `convert_list_to_camel(data: List[Any]) → List[Any]`
Recursively converts list items containing dictionaries from snake_case to camelCase.

#### `convert_list_to_snake(data: List[Any]) → List[Any]`
Recursively converts list items containing dictionaries from camelCase to snake_case.

### Contact-Specific Functions

#### `convert_contact_response_to_camel(contact: Dict[str, Any]) → Dict[str, Any]`
Specialized function for converting contact responses from the API to GraphQL format.
Handles the specific `phone_numbers` → `phoneNumbers` conversion with proper nested field mapping.

```python
api_response = {
    "id": "uuid-123",
    "name": "John Doe",
    "phone_numbers": [{"number": "123", "type_number": "MOBILE"}]
}
# Result: {"id": "uuid-123", "name": "John Doe", "phoneNumbers": [{"number": "123", "typeNumber": "MOBILE"}]}
```

#### `convert_phone_numbers_input_to_snake(phone_numbers: List[Dict[str, Any]]) → List[Dict[str, Any]]`
Converts phone number arrays from GraphQL input format to API format.

```python
graphql_input = [{"number": "123", "typeNumber": "MOBILE"}]
# Result: [{"number": "123", "type_number": "MOBILE"}]
```

#### `convert_contacts_response_to_camel(contacts: List[Dict[str, Any]]) → List[Dict[str, Any]]`
Converts an array of contacts from API response format to GraphQL format.

#### `convert_graphql_input_to_api_payload(input_data: Dict[str, Any]) → Dict[str, Any]`
Comprehensive function that converts entire GraphQL input objects to API payload format.
Handles both general field conversion and specific phone number conversion.

```python
graphql_input = {
    "name": "John Doe",
    "phoneNumbers": [{"number": "123", "typeNumber": "MOBILE"}]
}
# Result: {"name": "John Doe", "phone_numbers": [{"number": "123", "type_number": "MOBILE"}]}
```

## Usage in GraphQL Resolvers

### Query Resolvers
```python
@query.field("contacts")
async def resolve_contacts(_, info):
    response = requests.get(f"{CONTACT_SERVICE_URL}/contacts")
    contacts = response.json()
    return convert_contacts_response_to_camel(contacts)
```

### Mutation Resolvers
```python
@mutation.field("createContact")
async def resolve_create_contact(_, info, input):
    payload = convert_graphql_input_to_api_payload(input)
    response = requests.post(f"{CONTACT_SERVICE_URL}/contacts", json=payload)
    contact = response.json()
    return convert_contact_response_to_camel(contact)
```

## Testing

Run the test suite to verify all utility functions work correctly:

```bash
cd graphql_api_gateway
python test_utils.py
```

The test suite covers:
- Basic string conversion
- Nested dictionary and list conversion
- Contact-specific conversions
- Edge cases (empty inputs, None values)
- Complex nested structures
- Roundtrip conversions

## GraphQL Schema Conventions

The GraphQL schema follows standard GraphQL naming conventions:

- **Fields**: camelCase (`phoneNumbers`, `contactId`, `typeNumber`)
- **Types**: PascalCase (`ContactType`, `PhoneNumberType`)
- **Enums**: UPPER_CASE (`MOBILE`, `WORK`, `HOME`)
- **Arguments**: camelCase (`contactId`, `phoneNumbers`)

## API Integration

The utility functions automatically handle the mapping between:

**GraphQL (camelCase)**:
```graphql
{
  contactId: "123"
  phoneNumbers: [
    { number: "123", typeNumber: MOBILE }
  ]
}
```

**Python API (snake_case)**:
```json
{
  "contact_id": "123",
  "phone_numbers": [
    { "number": "123", "type_number": "MOBILE" }
  ]
}
```

## Error Handling

The utility functions are designed to be robust:
- Handle None values gracefully
- Work with empty collections
- Preserve non-dictionary/list values unchanged
- Maintain data types during conversion

## Performance Considerations

- Functions use recursive processing for nested structures
- Conversion is done in-memory with new object creation
- Suitable for typical API response sizes
- Consider caching for frequently converted large datasets