#!/usr/bin/env python3
"""
Enhanced GoHighLevel MCP Server with Intelligent Agent

This enhanced version adds intelligent input analysis, multi-tool calling, and missing parameter detection
for optimal LibreChat integration with OpenAI agents.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx
from fastmcp import FastMCP
from fastmcp.server.openapi import RouteMap, MCPType
from dotenv import load_dotenv

from intelligent_agent import IntelligentAgent, InputAnalysis, ToolCall

# Load environment variables from .env file
load_dotenv()


def load_openapi_specs(docs_path: Path) -> Dict[str, Dict[str, Any]]:
    """Load all OpenAPI specifications from the docs directory."""
    specs = {}
    
    # Find all JSON files that contain OpenAPI specifications
    json_files = [
        f for f in docs_path.glob("**/*.json")
        if f.name not in ["toc.json", "highlevel-teams.json"]
    ]
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                spec = json.load(f)
                
            # Verify it's an OpenAPI spec
            if "openapi" in spec and "paths" in spec:
                specs[json_file.stem] = spec
                print(f"Loaded OpenAPI spec: {json_file.name}")
        except Exception as e:
            print(f"Error loading {json_file.name}: {e}")
    
    return specs


def fix_openapi_schema(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Fix common OpenAPI schema issues in the GoHighLevel specifications."""
    # Fix missing response schemas
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            if "responses" in details:
                for status_code, response in details["responses"].items():
                    if "description" not in response:
                        response["description"] = f"Response for {method.upper()} {path}"
                    
                    # Add basic schema if missing
                    if "content" not in response:
                        response["content"] = {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "data": {"type": "object"}
                                    }
                                }
                            }
                        }
    
    # Fix missing security schemes
    if "components" not in spec:
        spec["components"] = {}
    
    if "securitySchemes" not in spec["components"]:
        spec["components"]["securitySchemes"] = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    
    # Add security to all operations if missing
    if "security" not in spec:
        spec["security"] = [{"bearerAuth": []}]
    
    return spec


def merge_openapi_specs(specs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Merge multiple OpenAPI specifications into a single spec."""
    merged_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "GoHighLevel API",
            "description": "Unified GoHighLevel API endpoints",
            "version": "1.0.0"
        },
        "paths": {},
        "components": {
            "schemas": {},
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        },
        "security": [
            {"bearerAuth": []}
        ]
    }
    
    # Merge all paths and components
    for spec_name, spec in specs.items():
        # Merge paths
        for path, methods in spec.get("paths", {}).items():
            if path not in merged_spec["paths"]:
                merged_spec["paths"][path] = {}
            merged_spec["paths"][path].update(methods)
        
        # Merge components/schemas
        if "components" in spec and "schemas" in spec["components"]:
            merged_spec["components"]["schemas"].update(spec["components"]["schemas"])
    
    return merged_spec


def extract_tool_specifications(merged_spec: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Extract tool specifications from the merged OpenAPI spec."""
    tools = {}
    
    for path, methods in merged_spec.get("paths", {}).items():
        for method, details in methods.items():
            operation_id = details.get("operationId")
            if operation_id:
                tools[operation_id] = {
                    "path": path,
                    "method": method.upper(),
                    "summary": details.get("summary", ""),
                    "description": details.get("description", ""),
                    "parameters": details.get("parameters", []),
                    "requestBody": details.get("requestBody", {}),
                    "responses": details.get("responses", {})
                }
    
    return tools


class EnhancedGHLServer:
    """Enhanced GoHighLevel MCP Server with intelligent agent capabilities."""
    
    def __init__(self, mcp_server: FastMCP, intelligent_agent: IntelligentAgent):
        self.mcp_server = mcp_server
        self.intelligent_agent = intelligent_agent
        
        # Add custom tools for intelligent processing
        self._register_enhanced_tools()
    
    def _register_enhanced_tools(self):
        """Register enhanced tools for intelligent processing."""
        
        @self.mcp_server.tool()
        async def analyze_and_execute(user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """
            Analyze user input and execute appropriate tools intelligently.
            
            This is the main entry point for intelligent tool calling that:
            1. Analyzes user input to understand intent
            2. Extracts entities and parameters
            3. Suggests appropriate tools
            4. Handles missing parameters by asking for clarification
            5. Executes multiple tools if needed
            
            Args:
                user_input: Natural language input from the user
                context: Optional context from previous interactions
                
            Returns:
                Result of analysis and tool execution
            """
            try:
                # Analyze the input
                analysis = await self.intelligent_agent.analyze_input(user_input, context)
                
                # If clarification is needed, return the clarification message
                if analysis.requires_clarification:
                    return {
                        "status": "clarification_needed",
                        "message": analysis.clarification_message,
                        "suggested_tools": [
                            {
                                "name": tool.tool_name,
                                "missing_params": tool.missing_params,
                                "description": tool.description
                            }
                            for tool in analysis.suggested_tools
                        ],
                        "extracted_entities": analysis.entities
                    }
                
                # Execute the suggested tools
                if analysis.suggested_tools:
                    results = await self.intelligent_agent.execute_tool_sequence(
                        analysis.suggested_tools, 
                        self.mcp_server
                    )
                    
                    return {
                        "status": "success",
                        "intent": analysis.intent,
                        "entities": analysis.entities,
                        "tools_executed": len([r for r in results if r.get("success")]),
                        "results": results
                    }
                else:
                    return {
                        "status": "no_tools_found",
                        "message": "I couldn't determine what action to take based on your input.",
                        "intent": analysis.intent,
                        "entities": analysis.entities,
                        "suggestion": "Please try being more specific about what you'd like to do."
                    }
                    
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Error processing request: {str(e)}",
                    "error_type": type(e).__name__
                }
        
        @self.mcp_server.tool()
        async def get_missing_parameters(tool_name: str, current_params: Dict[str, Any] = None) -> Dict[str, Any]:
            """
            Get information about missing parameters for a specific tool.
            
            Args:
                tool_name: Name of the tool to check
                current_params: Currently available parameters
                
            Returns:
                Information about missing parameters
            """
            if current_params is None:
                current_params = {}
                
            tool_spec = self.intelligent_agent.available_tools.get(tool_name)
            
            if not tool_spec:
                return {
                    "error": f"Tool '{tool_name}' not found",
                    "available_tools": list(self.intelligent_agent.available_tools.keys())
                }
            
            # Analyze what parameters are missing
            required_params = []
            optional_params = []
            
            # Extract from parameters
            for param in tool_spec.get("parameters", []):
                param_name = param.get("name")
                if param.get("required", False):
                    if param_name not in current_params:
                        required_params.append({
                            "name": param_name,
                            "type": param.get("schema", {}).get("type", "string"),
                            "description": param.get("description", "")
                        })
                else:
                    optional_params.append({
                        "name": param_name,
                        "type": param.get("schema", {}).get("type", "string"),
                        "description": param.get("description", "")
                    })
            
            # Check request body requirements
            request_body = tool_spec.get("requestBody", {})
            if request_body.get("required", False):
                if "request_body" not in current_params:
                    required_params.append({
                        "name": "request_body",
                        "type": "object",
                        "description": "Request body data"
                    })
            
            return {
                "tool_name": tool_name,
                "required_missing": required_params,
                "optional_available": optional_params,
                "current_params": list(current_params.keys()),
                "ready_to_execute": len(required_params) == 0
            }
        
        @self.mcp_server.tool()
        async def suggest_tools_for_input(user_input: str) -> Dict[str, Any]:
            """
            Suggest tools based on user input without executing them.
            
            Args:
                user_input: Natural language input from the user
                
            Returns:
                Suggested tools with confidence scores
            """
            try:
                analysis = await self.intelligent_agent.analyze_input(user_input)
                
                return {
                    "intent": analysis.intent,
                    "entities": analysis.entities,
                    "suggestions": [
                        {
                            "tool_name": tool.tool_name,
                            "confidence": tool.confidence,
                            "description": tool.description,
                            "parameters": tool.parameters,
                            "missing_params": tool.missing_params,
                            "ready_to_execute": len(tool.missing_params) == 0
                        }
                        for tool in analysis.suggested_tools
                    ]
                }
                
            except Exception as e:
                return {
                    "error": f"Error analyzing input: {str(e)}",
                    "error_type": type(e).__name__
                }
        
        @self.mcp_server.tool()
        async def get_available_tools_summary() -> Dict[str, Any]:
            """
            Get a summary of all available tools organized by category.
            
            Returns:
                Organized summary of available tools
            """
            tools_by_category = {
                "contacts": [],
                "campaigns": [],
                "opportunities": [],
                "workflows": [],
                "other": []
            }
            
            for tool_name, tool_spec in self.intelligent_agent.available_tools.items():
                # Categorize tools
                category = "other"
                if "contact" in tool_name.lower():
                    category = "contacts"
                elif "campaign" in tool_name.lower():
                    category = "campaigns"
                elif "opportunit" in tool_name.lower():
                    category = "opportunities"
                elif "workflow" in tool_name.lower():
                    category = "workflows"
                
                tools_by_category[category].append({
                    "name": tool_name,
                    "method": tool_spec.get("method", ""),
                    "path": tool_spec.get("path", ""),
                    "summary": tool_spec.get("summary", ""),
                    "description": tool_spec.get("description", "")
                })
            
            return {
                "total_tools": len(self.intelligent_agent.available_tools),
                "categories": tools_by_category,
                "usage_tip": "Use 'analyze_and_execute' for intelligent tool selection and execution"
            }


async def create_enhanced_ghl_server():
    """Create the enhanced GoHighLevel MCP server with intelligent agent."""
    
    # Get configuration from environment variables
    api_key = os.getenv("GHL_API_KEY", "placeholder-key")
    location_id = os.getenv("GHL_LOCATION_ID", "placeholder-location")
    base_url = os.getenv("GHL_BASE_URL", "https://services.leadconnectorhq.com")
    
    # Set up the HTTP client with authentication
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-API-KEY": api_key,
        "locationid": location_id,
        "Version": "2021-07-28",
        "Content-Type": "application/json"
    }
    
    client = httpx.AsyncClient(
        base_url=base_url,
        headers=headers,
        timeout=30.0
    )
    
    # Load and merge OpenAPI specifications
    project_root = Path(__file__).parents[1]
    docs_path = project_root / "docs"
    
    print("Loading GoHighLevel OpenAPI specifications...")
    specs = load_openapi_specs(docs_path)
    
    if not specs:
        raise RuntimeError("No valid OpenAPI specifications found in docs directory")
    
    print(f"Found {len(specs)} OpenAPI specifications")
    merged_spec = merge_openapi_specs(specs)
    
    # Fix schema issues
    print("Fixing OpenAPI schema issues...")
    merged_spec = fix_openapi_schema(merged_spec)
    
    print(f"Merged into single specification with {len(merged_spec['paths'])} endpoints")
    
    # Extract tool specifications for the intelligent agent
    tool_specs = extract_tool_specifications(merged_spec)
    print(f"Extracted {len(tool_specs)} tool specifications")
    
    # Define custom route mappings for better organization
    route_maps = [
        # Convert all non-GET endpoints to tools
        RouteMap(
            methods=["POST", "PUT", "PATCH", "DELETE"],
            pattern=r".*",
            mcp_type=MCPType.TOOL,
            mcp_tags={"ghl", "api", "write"}
        ),
        
        # Convert all GET endpoints to tools for better compatibility
        RouteMap(
            methods=["GET"],
            pattern=r".*",
            mcp_type=MCPType.TOOL,
            mcp_tags={"ghl", "api", "read"}
        ),
        
        # Exclude any admin or internal endpoints if they exist
        RouteMap(
            pattern=r".*/admin/.*",
            mcp_type=MCPType.EXCLUDE
        ),
        
        RouteMap(
            tags={"internal"},
            mcp_type=MCPType.EXCLUDE
        )
    ]
    
    # Create the base MCP server from the merged OpenAPI specification
    mcp = FastMCP.from_openapi(
        openapi_spec=merged_spec,
        client=client,
        name="Enhanced GoHighLevel MCP Server",
        route_maps=route_maps,
        tags={"ghl", "crm", "marketing", "intelligent"}
    )
    
    # Create the intelligent agent
    intelligent_agent = IntelligentAgent(tool_specs)
    
    # Create the enhanced server wrapper
    enhanced_server = EnhancedGHLServer(mcp, intelligent_agent)
    
    print(f"Created enhanced MCP server with intelligent agent!")
    print(f"Available tools: {len(tool_specs)}")
    print("Enhanced features:")
    print("  - Intelligent input analysis")
    print("  - Multi-tool calling support")
    print("  - Missing parameter detection")
    print("  - OpenAI agent optimization")
    
    return enhanced_server.mcp_server


def main():
    """Main entry point for the enhanced MCP server."""
    try:
        print("Starting Enhanced GoHighLevel MCP Server...")
        print("Features: Intelligent Agent, Multi-Tool Calling, Parameter Validation")
        print("Transport: STDIO (default)")
        print()
        
        # Create the enhanced server asynchronously
        server = asyncio.run(create_enhanced_ghl_server())
        
        print("\n" + "="*60)
        print("🤖 ENHANCED SERVER READY FOR LIBRECHAT INTEGRATION!")
        print("="*60)
        print()
        print("Key Tools for OpenAI Agents:")
        print("  • analyze_and_execute - Main intelligent tool calling")
        print("  • suggest_tools_for_input - Get tool suggestions")
        print("  • get_missing_parameters - Check parameter requirements")
        print("  • get_available_tools_summary - Browse available tools")
        print()
        print("The server now supports:")
        print("  ✓ Multi-tool calling in single requests")
        print("  ✓ Intelligent input analysis")
        print("  ✓ Missing parameter detection")
        print("  ✓ Natural language to tool mapping")
        print("  ✓ OpenAI agent optimization")
        print()
        
        # Get transport configuration
        transport = os.getenv("MCP_TRANSPORT", "stdio")
        host = os.getenv("MCP_HOST", "127.0.0.1")
        port = int(os.getenv("MCP_PORT", "8000"))
        
        if transport.lower() == "http":
            print(f"Starting with HTTP transport on {host}:{port}")
            print(f"Server URL: http://{host}:{port}/mcp")
            server.run(transport="http", host=host, port=port)
        else:
            print("Starting with STDIO transport (recommended for LibreChat)...")
            server.run()
        
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()