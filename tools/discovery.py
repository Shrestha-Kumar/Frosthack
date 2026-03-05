import os
import json
from typing import List, Optional, Dict
import httpx
from pydantic import BaseModel, create_model
from langchain_core.tools import StructuredTool
from models import ToolDefinition, CampaignState

def load_openapi_spec(spec_path: str) -> dict:
    """Load OpenAPI spec from file at runtime."""
    with open(spec_path) as f:
        return json.load(f)

def compress_spec_for_context(spec: dict) -> dict:
    """Remove verbose descriptions to fit into LLM context window."""
    compressed = {
        "openapi": spec.get("openapi"),
        "info": {"title": spec.get("info", {}).get("title", "")},
        "paths": {}
    }
    for path, path_item in spec.get("paths", {}).items():
        compressed["paths"][path] = {}
        for method, operation in path_item.items():
            if method.lower() in ["get", "post", "put", "delete", "patch"]:
                compressed["paths"][path][method] = {
                    "operationId": operation.get("operationId", f"{method}_{path.replace('/', '_')}"),
                    "summary": operation.get("summary", ""),
                    "parameters": operation.get("parameters", []),
                    "requestBody": operation.get("requestBody", {}),
                    "responses": {
                        k: {"description": v.get("description", "")}
                        for k, v in operation.get("responses", {}).items()
                    }
                }
    return compressed

def _openapi_type_to_python(openapi_type: str):
    mapping = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict
    }
    return mapping.get(openapi_type, str)

def create_api_tool_from_operation(
    path: str,
    method: str,
    operation: dict,
    base_url: str,
    api_key: str,
    full_spec: dict = None  # Added to allow $ref lookups
) -> StructuredTool:
    """Dynamically create a LangChain StructuredTool from an OpenAPI operation."""
    operation_id = operation.get("operationId", f"{method}_{path.replace('/', '_')}")
    summary = operation.get("summary", "No description provided.")
    parameters = operation.get("parameters", [])
    request_body = operation.get("requestBody", {})

    field_definitions = {}

    # Parse query/path parameters
    for param in parameters:
        param_name = param["name"]
        param_type = _openapi_type_to_python(param.get("schema", {}).get("type", "string"))
        required = param.get("required", False)
        if required:
            field_definitions[param_name] = (param_type, ...)
        else:
            field_definitions[param_name] = (Optional[param_type], None)

    # Parse JSON request body
    if request_body:
        content = request_body.get("content", {})
        json_schema = content.get("application/json", {}).get("schema", {})
        
        # --- NEW: Resolve $ref if it exists ---
        if "$ref" in json_schema and full_spec:
            ref_path = json_schema["$ref"].split("/")
            resolved = full_spec
            for part in ref_path[1:]:
                resolved = resolved.get(part, {})
            json_schema = resolved
        # --------------------------------------

        for prop_name, prop_schema in json_schema.get("properties", {}).items():
            prop_type = _openapi_type_to_python(prop_schema.get("type", "string"))
            required_props = json_schema.get("required", [])
            if prop_name in required_props:
                field_definitions[prop_name] = (prop_type, ...)
            else:
                field_definitions[prop_name] = (Optional[prop_type], None)

    # Create dynamic Pydantic input model
    DynamicInputModel = create_model(f"{operation_id}_input", **field_definitions)

    def tool_fn(**kwargs) -> dict:
        validated = DynamicInputModel(**kwargs)
        url = f"{base_url}{path}"
        headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }

        try:
            if method.lower() == "get":
                response = httpx.get(url, params=validated.model_dump(exclude_none=True), headers=headers)
            elif method.lower() == "post":
                response = httpx.post(url, json=validated.model_dump(exclude_none=True), headers=headers)
            else:
                response = httpx.request(method.upper(), url, json=validated.model_dump(exclude_none=True), headers=headers)
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"API call failed with status {e.response.status_code}", "details": e.response.text}
        except Exception as e:
            return {"error": str(e)}

    return StructuredTool(
        name=operation_id,
        description=summary,
        args_schema=DynamicInputModel,
        func=tool_fn
    )

# Store loaded tools at the module level
_LOADED_TOOLS: List[StructuredTool] = []

def load_openapi_tools_node(state: CampaignState) -> dict:
    """LangGraph node: runs at startup, populates discovered_tools in state."""
    spec = load_openapi_spec("campaignx_api.json") # Pointing to the JSON you downloaded
    compressed = compress_spec_for_context(spec)

    tools = []
    tool_definitions = []
    
    base_url = os.getenv("CAMPAIGNX_API_BASE_URL", "http://localhost:4010")
    api_key = os.getenv("CAMPAIGNX_API_KEY", "mock_key")

    for path, path_item in compressed["paths"].items():
        for method, operation in path_item.items():
            tool = create_api_tool_from_operation(path, method, operation, base_url, api_key, spec)
            tools.append(tool)
            tool_definitions.append(ToolDefinition(
                name=tool.name,
                description=tool.description,
                endpoint=path,
                method=method.upper(),
                parameters_schema=operation
            ))

    global _LOADED_TOOLS
    _LOADED_TOOLS = tools

    return {
        "openapi_spec": compressed,
        "discovered_tools": tool_definitions
    }

def get_loaded_tools() -> List[StructuredTool]:
    return _LOADED_TOOLS