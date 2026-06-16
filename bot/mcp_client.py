"""InsureFlow Bot — MCP Client.

Connects to the local InsureFlow MCP server over Streamable HTTP and
exposes LLM-callable tool wrappers for the customer journey.
"""

import json
import httpx
from loguru import logger
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from pipecat.services.llm_service import FunctionCallParams

from config import config


MCP_TOOL_NAME_MAP = {
    "submit_insurance_form": "tool_submit_insurance_form",
    "get_quotes": "tool_get_quotes",
    "select_plan": "tool_select_plan",
    "select_add_ons": "tool_select_add_ons",
    "create_payment": "tool_create_payment",
    "send_payment_otp": "tool_send_payment_otp",
    "verify_payment_otp": "tool_verify_payment_otp",
    "get_payment_status": "tool_get_payment_status",
    "get_policy": "tool_get_policy",
    "send_login_otp": "tool_send_login_otp",
    "verify_login_otp": "tool_verify_login_otp",
    "get_user_transactions": "tool_get_user_transactions",
    "get_latest_incomplete_journey": "tool_get_latest_incomplete_journey",
    "list_user_policies": "tool_list_user_policies",
}


# ── OpenAI-compatible Tool Definitions ────────────────────────────────────────
# Groq uses OpenAI API format for function calling.
# These tell Groq WHAT each tool does and WHAT parameters to pass.
# Groq reads these at startup and decides when to call each tool during conversation.

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "submit_insurance_form",
            "description": (
                "Submit the customer's insurance form to create a new transaction. "
                "Call this once you have mobile_number, insurance_type, first_name, last_name. "
                "Returns a transaction_id — save it for all future calls."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "mobile_number": {"type": "string", "description": "10-digit mobile number"},
                    "insurance_type": {
                        "type": "string",
                        "enum": ["health", "life", "general"],
                        "description": "Type of insurance the customer wants",
                    },
                    "proposer_first_name": {"type": "string"},
                    "proposer_last_name": {"type": "string"},
                    "proposer_email": {"type": "string"},
                    "proposer_dob": {
                        "type": "string",
                        "description": "Date of birth in YYYY-MM-DD format",
                    },
                    "proposer_gender": {"type": "string", "enum": ["male", "female", "other"]},
                    "sum_insured_requested": {"type": "number", "description": "Coverage amount in rupees"},
                    "policy_term_years": {"type": "integer", "description": "Policy term in years"},
                    "city": {"type": "string"},
                    "state": {"type": "string"},
                },
                "required": [
                    "mobile_number",
                    "insurance_type",
                    "proposer_first_name",
                    "proposer_last_name",
                    "sum_insured_requested",
                    "policy_term_years",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_login_otp",
            "description": "Send a mock OTP to the customer's mobile number for verification.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mobile_number": {"type": "string"},
                },
                "required": ["mobile_number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "verify_login_otp",
            "description": (
                "Verify the OTP the customer received on their mobile. "
                "Returns a JWT token and user_id on success — save both."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "mobile_number": {"type": "string"},
                    "otp": {"type": "string"},
                },
                "required": ["mobile_number", "otp"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_quotes",
            "description": "Fetch available insurance quotes for the customer's transaction.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {"type": "string"},
                },
                "required": ["transaction_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "select_plan",
            "description": "Save the customer's selected insurance plan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {"type": "string"},
                    "selected_plan_id": {"type": "string"},
                },
                "required": ["transaction_id", "selected_plan_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "select_add_ons",
            "description": (
                "Save the customer's selected add-ons for their plan. "
                "Pass an empty list if the customer does not want any add-ons."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {"type": "string"},
                    "selected_plan_id": {"type": "string"},
                    "selected_add_ons": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "price": {"type": "number"},
                            },
                        },
                        "description": "List of selected add-ons. Pass empty list if none.",
                    },
                },
                "required": ["transaction_id", "selected_plan_id", "selected_add_ons"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_payment",
            "description": (
                "Create a payment session for the transaction. "
                "Returns a payment_reference — save it for payment OTP steps."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {"type": "string"},
                    "user_id": {"type": "string"},
                    "amount": {"type": "number", "description": "Total premium amount in rupees"},
                },
                "required": ["transaction_id", "user_id", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_payment_otp",
            "description": "Send a payment OTP to the customer's mobile for payment confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "payment_reference": {"type": "string"},
                },
                "required": ["payment_reference"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "verify_payment_otp",
            "description": (
                "Verify the customer's payment OTP to complete payment. "
                "On success, the insurance policy is automatically issued."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {"type": "string"},
                    "payment_reference": {"type": "string"},
                    "otp": {"type": "string"},
                },
                "required": ["transaction_id", "payment_reference", "otp"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_policy",
            "description": "Fetch one issued policy by policy number after the customer is logged in.",
            "parameters": {
                "type": "object",
                "properties": {
                    "policy_number": {"type": "string"},
                    "token": {"type": "string"},
                },
                "required": ["policy_number", "token"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_user_policies",
            "description": "List all issued insurance policies for the customer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "token": {"type": "string"},
                },
                "required": ["user_id", "token"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_transactions",
            "description": "List all transactions for a returning customer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "token": {"type": "string"},
                },
                "required": ["user_id", "token"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_latest_incomplete_journey",
            "description": (
                "For returning customers — fetch their latest incomplete insurance journey "
                "so they can resume from where they left off."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "mobile_number": {"type": "string"},
                    "token": {"type": "string"},
                },
                "required": ["mobile_number", "token"],
            },
        },
    },
]


# ── MCP HTTP Client ────────────────────────────────────────────────────────────

async def call_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """Call one MCP tool over Streamable HTTP and normalize the result."""

    actual_tool_name = MCP_TOOL_NAME_MAP.get(tool_name, tool_name)
    try:
        async with streamablehttp_client(config.mcp_server_url) as (
            read_stream,
            write_stream,
            _,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(actual_tool_name, arguments or {})
                normalized = _normalize_tool_result(result)
                logger.debug(f"MCP tool '{actual_tool_name}' returned: {normalized}")
                return normalized
    except httpx.RequestError as e:
        logger.error(f"MCP tool '{actual_tool_name}' request failed: {e}")
        return {"error": "Could not reach the insurance backend. Please try again."}
    except Exception as e:
        logger.error(f"MCP tool '{actual_tool_name}' failed: {e}")
        return {"error": "Backend returned an error. Please try again."}


def _normalize_tool_result(result) -> dict:
    """Convert an MCP CallToolResult into a plain dict for the LLM layer."""

    if getattr(result, "structuredContent", None):
        return result.structuredContent

    texts: list[str] = []
    for item in getattr(result, "content", []) or []:
        text = getattr(item, "text", None)
        if text:
            texts.append(text)

    if texts:
        merged_text = "\n".join(texts).strip()
        try:
            payload = json.loads(merged_text)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            pass

        if getattr(result, "isError", False):
            return {"error": merged_text}
        return {"message": merged_text}

    if getattr(result, "isError", False):
        return {"error": "Tool call failed."}
    return {}


# ── Tool Handler Functions ─────────────────────────────────────────────────────
# Each function is registered with Groq via llm.register_function().
# When Groq decides to call a tool, Pipecat invokes the matching function here.
# params.arguments contains the arguments Groq passed.
# params.result_callback() sends the result back to Groq.

async def submit_insurance_form(params: FunctionCallParams):
    """Submits customer form. Returns transaction_id."""
    result = await call_mcp_tool("submit_insurance_form", params.arguments)
    await params.result_callback(result)


async def send_login_otp(params: FunctionCallParams):
    """Sends OTP to customer mobile."""
    result = await call_mcp_tool("send_login_otp", params.arguments)
    await params.result_callback(result)


async def verify_login_otp(params: FunctionCallParams):
    """Verifies OTP. Returns token and user_id."""
    result = await call_mcp_tool("verify_login_otp", params.arguments)
    await params.result_callback(result)


async def get_quotes(params: FunctionCallParams):
    """Fetches insurance plans from provider backend."""
    result = await call_mcp_tool("get_quotes", params.arguments)
    await params.result_callback(result)


async def select_plan(params: FunctionCallParams):
    """Saves selected plan on the transaction."""
    result = await call_mcp_tool("select_plan", params.arguments)
    await params.result_callback(result)


async def select_add_ons(params: FunctionCallParams):
    """Saves selected add-ons (or empty list)."""
    result = await call_mcp_tool("select_add_ons", params.arguments)
    await params.result_callback(result)


async def create_payment(params: FunctionCallParams):
    """Creates payment session. Returns payment_reference."""
    result = await call_mcp_tool("create_payment", params.arguments)
    await params.result_callback(result)


async def send_payment_otp(params: FunctionCallParams):
    """Sends payment OTP to customer mobile."""
    result = await call_mcp_tool("send_payment_otp", params.arguments)
    await params.result_callback(result)


async def verify_payment_otp(params: FunctionCallParams):
    """Verifies payment OTP. Policy is auto-issued on success."""
    result = await call_mcp_tool("verify_payment_otp", params.arguments)
    await params.result_callback(result)


async def get_policy(params: FunctionCallParams):
    """Fetches one issued policy for a logged-in customer."""
    result = await call_mcp_tool("get_policy", params.arguments)
    await params.result_callback(result)


async def list_user_policies(params: FunctionCallParams):
    """Returns all issued policies for the customer."""
    result = await call_mcp_tool("list_user_policies", params.arguments)
    await params.result_callback(result)


async def get_user_transactions(params: FunctionCallParams):
    """Returns all transactions for a returning customer."""
    result = await call_mcp_tool("get_user_transactions", params.arguments)
    await params.result_callback(result)


async def get_latest_incomplete_journey(params: FunctionCallParams):
    """Returns the latest incomplete journey for a returning customer."""
    result = await call_mcp_tool("get_latest_incomplete_journey", params.arguments)
    await params.result_callback(result)


# ── Register All Tools with LLM ───────────────────────────────────────────────

def register_tools(llm) -> None:
    """
    Register all MCP tool functions with the LLM service.
    Call this once after creating the Groq LLM instance.

    Usage:
        from mcp_client import register_tools, TOOLS
        llm = GroqLLMService(...)
        register_tools(llm)
    """
    llm.register_function("submit_insurance_form", submit_insurance_form)
    llm.register_function("send_login_otp", send_login_otp)
    llm.register_function("verify_login_otp", verify_login_otp)
    llm.register_function("get_quotes", get_quotes)
    llm.register_function("select_plan", select_plan)
    llm.register_function("select_add_ons", select_add_ons)
    llm.register_function("create_payment", create_payment)
    llm.register_function("send_payment_otp", send_payment_otp)
    llm.register_function("verify_payment_otp", verify_payment_otp)
    llm.register_function("get_policy", get_policy)
    llm.register_function("list_user_policies", list_user_policies)
    llm.register_function("get_user_transactions", get_user_transactions)
    llm.register_function("get_latest_incomplete_journey", get_latest_incomplete_journey)
    logger.info("All 12 MCP tools registered with LLM.")
