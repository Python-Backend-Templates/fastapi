from typing import Dict

from fastapi import status
from pydantic.dataclasses import dataclass


@dataclass
class RequestErrorSchema:
    detail: str


@dataclass
class RequestValidationErrorSchema:
    detail: Dict[str, str]


default_responses = {
    status.HTTP_400_BAD_REQUEST: {
        "model": RequestErrorSchema,
        "description": "Request can not be processed.",
        "content": {"application/json": {"example": {"detail": "Some error."}}},
    },
    status.HTTP_401_UNAUTHORIZED: {
        "model": RequestErrorSchema,
        "description": "Unauthorized.",
        "content": {
            "application/json": {"example": {"detail": "Some authorization error."}}
        },
    },
    status.HTTP_403_FORBIDDEN: {
        "model": RequestErrorSchema,
        "description": "Access to resource is forbidden.",
        "content": {
            "application/json": {"example": {"detail": "Some permission error."}}
        },
    },
    status.HTTP_404_NOT_FOUND: {
        "model": RequestErrorSchema,
        "description": "Requested item was not found",
        "content": {
            "application/json": {"example": {"detail": "Some not found error."}}
        },
    },
    status.HTTP_422_UNPROCESSABLE_ENTITY: {
        "model": RequestValidationErrorSchema,
        "description": "Validation error.",
        "content": {
            "application/json": {
                "example": {
                    "detail": {
                        "field1": "Error for field1.",
                        "field2__subfield1": "Error in nested field2 for subfield1.",
                    }
                }
            }
        },
    },
}
