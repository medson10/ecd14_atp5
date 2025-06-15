#!/bin/bash
docker build -t contact-service:latest ./contact_service
docker build -t graphql-api-gateway:latest ./graphql_api_gateway
