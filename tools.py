from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from handlers.order_tracking import lookup_order, normalize_order_id
from handlers.product_search import _search_products
from store_context import PRODUCTS

logger = logging.getLogger(__name__)


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict[str, Any]


TOOLS: list[ToolDef] = [
    ToolDef(
        name="lookup_order",
        description="Look up the status and details of a customer order by its order ID.",
        parameters={
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID in format NB-XXXXX (e.g., NB-10042)",
                }
            },
            "required": ["order_id"],
        },
    ),
    ToolDef(
        name="search_products",
        description="Search the product catalog for items matching a keyword query.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keywords like 'wireless mouse' or 'charger'",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (default 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    ),
    ToolDef(
        name="check_return_eligibility",
        description="Check if an order is eligible for return based on its status.",
        parameters={
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID in format NB-XXXXX",
                }
            },
            "required": ["order_id"],
        },
    ),
    ToolDef(
        name="create_support_ticket",
        description="Create a support ticket to escalate to a human agent.",
        parameters={
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": "Brief summary of the issue",
                },
                "reason": {
                    "type": "string",
                    "description": "Detailed reason for the ticket",
                },
            },
            "required": ["subject", "reason"],
        },
    ),
    ToolDef(
        name="get_product_details",
        description="Get full details of a product by its SKU or name.",
        parameters={
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "Product SKU (e.g., SKU-001) or product name",
                }
            },
            "required": ["product_id"],
        },
    ),
]


def _lookup_order(order_id: str) -> dict:
    nid = normalize_order_id(order_id)
    order = lookup_order(nid)
    if order:
        return {"found": True, "order": order}
    return {"found": False, "order_id": nid}


def _search_products_tool(query: str, limit: int = 5) -> dict:
    results = _search_products(query, limit=limit)
    return {
        "query": query,
        "count": len(results),
        "results": [
            {
                "id": p["id"],
                "name": p["name"],
                "price": p["price"],
                "category": p["category"],
                "in_stock": p["in_stock"],
                "description": p["description"],
            }
            for p in results
        ],
    }


def _check_return_eligibility(order_id: str) -> dict:
    nid = normalize_order_id(order_id)
    order = lookup_order(nid)
    if not order:
        return {"eligible": False, "reason": "Order not found"}
    if order.get("status") == "Delivered":
        return {"eligible": True, "order_id": nid, "return_window_days": 30}
    return {
        "eligible": False,
        "reason": f"Order status is '{order.get('status')}'. Only delivered orders can be returned.",
    }


async def _create_support_ticket(subject: str, reason: str, user_id: int | None = None) -> dict:
    from db import session_store

    ticket = session_store.create_support_ticket(
        user_id=user_id or 0,
        subject=subject,
        source="ai-function-call",
        reason=reason,
    )
    return {"ticket_id": ticket.get("ticket_id", 0), "status": "open"}


def _get_product_details(product_id: str) -> dict:
    for p in PRODUCTS:
        if p["id"].lower() == product_id.lower() or p["name"].lower() == product_id.lower():
            return {"found": True, "product": p}
    for p in PRODUCTS:
        if product_id.lower() in p["name"].lower():
            return {"found": True, "product": p}
    return {"found": False, "query": product_id}


TOOL_MAP = {
    "lookup_order": _lookup_order,
    "search_products": _search_products_tool,
    "check_return_eligibility": _check_return_eligibility,
    "create_support_ticket": _create_support_ticket,
    "get_product_details": _get_product_details,
}


def get_tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            },
        }
        for t in TOOLS
    ]


async def execute_tool(name: str, arguments: dict[str, Any], user_id: int | None = None) -> str:
    handler = TOOL_MAP.get(name)
    if not handler:
        return f"Error: unknown tool '{name}'"

    try:
        if name == "create_support_ticket":
            result = await handler(
                subject=arguments.get("subject", ""),
                reason=arguments.get("reason", ""),
                user_id=user_id,
            )
        else:
            result = handler(**arguments)
    except Exception as exc:
        logger.exception("Tool %s failed", name)
        return f"Error executing {name}: {exc}"

    import json

    return json.dumps(result, indent=2)
