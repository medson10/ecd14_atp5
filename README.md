# ECD14 - ATP5

This is a a project to demonstrate a structure of microservices using K8s, GraphQL, Postgres, and FastAPI

## Getting Started

### Create the images
```bash
create_images.sh
```

### Initialize the containers
```bash
init_containers.sh
```

### Verify if they are running (status 'running')
```bash
kubectl get pods
kubectl get pods --watch
```

### Access the GraphQL gateway at http://localhost:30004/graphql

## Case Conversion

The GraphQL gateway includes automatic utilities for converting between naming conventions:
- **GraphQL**: camelCase (phoneNumbers, typeNumber)
- **API Python**: snake_case (phone_numbers, type_number)

The conversion functions are in `graphql_api_gateway/utils.py` and are automatically applied in the resolvers.

# Query contacts:
```graphql
query {
  contacts {
    id
    name
    category
    phoneNumbers {
      number
      typeNumber
    }
  }
}
```

# Create a contact:

```graphql
mutation {
  createContact(input: {
    name: "João Silva"
    category: PERSONAL
    phoneNumbers: [
      { number: "11999999999", typeNumber: MOBILE }
      { number: "1133333333", typeNumber: HOME }
    ]
  }) {
    ... on ContactType {
      id
      name
      category
      phoneNumbers {
        number
        typeNumber
      }
    }
    ... on ErrorType {
      message
    }
  }
}
```

# Query a specific contact:
```graphql
query {
  contact(input: { contactId: "seu-id-aqui" }) {
    ... on ContactType {
      id
      name
      category
      phoneNumbers {
        number
        typeNumber
      }
    }
    ... on ErrorType {
      message
    }
  }
}
```

# Query a node
```graphql
query {
  node(input: { id: "seu-id-aqui" }) {
    __typename
    ... on ContactType {
      id
      name
      category
      phoneNumbers {
        number
        typeNumber
      }
    }
  }
}
```

# Update a contact:
```graphql
mutation {
  updateContact(input: {
    id: "seu-id-aqui"
    name: "João Silva Atualizado"
    category: BUSINESS
    phoneNumbers: [
      { number: "11888888888", typeNumber: WORK }
    ]
  }) {
    ... on ContactType {
      id
      name
      category
    }
    ... on ErrorType {
      message
    }
  }
}
```

# Delete a contact:
```graphql
mutation {
  deleteContact(input: { id: "seu-id-aqui" }) {
    ... on ContactType {
      id
    }
    ... on ErrorType {
      message
    }
  }
}
```

## Project Structure
- **contact_service/**: REST API service for managing contacts
- **graphql_api_gateway/**: GraphQL gateway with automatic naming conversion
  - `utils.py`: Utility functions for camelCase ↔ snake_case conversion, and global ID decoding
  - `schema.graphql`: GraphQL schema with camelCase conventions
- **k8s/**: Kubernetes deployment configurations

## Data Types

### Contact Categories
- `PERSONAL`: Personal contacts
- `FAMILY`: Family contacts
- `BUSINESS`: Business contacts

### Phone Types
- `MOBILE`: Mobile
- `WORK`: Work
- `HOME`: Home
