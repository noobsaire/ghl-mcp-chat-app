#!/usr/bin/env python3
"""
Intelligent Agent for GoHighLevel MCP Server

This module adds intelligent input analysis, multi-tool calling, and missing parameter detection
to enhance the LibreChat integration for OpenAI agents.
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import asyncio


@dataclass
class ToolCall:
    """Represents a tool call with its parameters and validation status."""
    tool_name: str
    parameters: Dict[str, Any]
    missing_params: List[str]
    confidence: float
    description: str


@dataclass
class InputAnalysis:
    """Result of analyzing user input for tool calling."""
    intent: str
    entities: Dict[str, Any]
    suggested_tools: List[ToolCall]
    requires_clarification: bool
    clarification_message: Optional[str] = None


class IntelligentAgent:
    """
    Intelligent agent that analyzes user input and orchestrates multiple tool calls.
    Designed to work seamlessly with OpenAI agents and LibreChat.
    """
    
    def __init__(self, available_tools: Dict[str, Dict[str, Any]]):
        """
        Initialize the intelligent agent with available tools.
        
        Args:
            available_tools: Dictionary of tool names to their OpenAPI specifications
        """
        self.available_tools = available_tools
        self.intent_patterns = self._build_intent_patterns()
        self.entity_extractors = self._build_entity_extractors()
    
    def _build_intent_patterns(self) -> Dict[str, List[str]]:
        """Build patterns for intent recognition."""
        return {
            "create_contact": [
                r"create.*contact",
                r"add.*contact",
                r"new contact",
                r"register.*person",
                r"add.*person.*crm"
            ],
            "search_contacts": [
                r"find.*contact",
                r"search.*contact",
                r"look.*contact",
                r"get.*contact.*list",
                r"show.*contact"
            ],
            "update_contact": [
                r"update.*contact",
                r"modify.*contact",
                r"edit.*contact",
                r"change.*contact"
            ],
            "create_campaign": [
                r"create.*campaign",
                r"new campaign",
                r"start.*campaign",
                r"launch.*campaign"
            ],
            "get_campaigns": [
                r"show.*campaign",
                r"list.*campaign",
                r"get.*campaign",
                r"view.*campaign"
            ],
            "bulk_operations": [
                r"bulk.*",
                r"batch.*",
                r"multiple.*",
                r"all.*contact",
                r"mass.*"
            ]
        }
    
    def _build_entity_extractors(self) -> Dict[str, str]:
        """Build regex patterns for entity extraction."""
        return {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b",
            "name": r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b",
            "location_id": r"\b[a-zA-Z0-9]{20,}\b",  # Typical GHL location ID pattern
            "contact_id": r"\bcontact[_-]?id[:\s]*([a-zA-Z0-9]+)\b",
            "campaign_id": r"\bcampaign[_-]?id[:\s]*([a-zA-Z0-9]+)\b"
        }
    
    async def analyze_input(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> InputAnalysis:
        """
        Analyze user input to determine intent and extract entities.
        
        Args:
            user_input: The user's natural language input
            context: Optional context from previous interactions
            
        Returns:
            InputAnalysis with detected intent, entities, and suggested tools
        """
        user_input_lower = user_input.lower()
        
        # Extract entities
        entities = self._extract_entities(user_input)
        
        # Detect intent
        intent = self._detect_intent(user_input_lower)
        
        # Get suggested tools based on intent and entities
        suggested_tools = await self._suggest_tools(intent, entities, user_input)
        
        # Check if clarification is needed
        requires_clarification = any(tool.missing_params for tool in suggested_tools)
        clarification_message = self._generate_clarification_message(suggested_tools) if requires_clarification else None
        
        return InputAnalysis(
            intent=intent,
            entities=entities,
            suggested_tools=suggested_tools,
            requires_clarification=requires_clarification,
            clarification_message=clarification_message
        )
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from text using regex patterns."""
        entities = {}
        
        for entity_type, pattern in self.entity_extractors.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[entity_type] = matches[0] if len(matches) == 1 else matches
        
        # Extract names more intelligently
        if "name" in entities:
            names = entities["name"] if isinstance(entities["name"], list) else [entities["name"]]
            # Try to split first/last name
            for name in names:
                parts = name.split()
                if len(parts) >= 2:
                    entities["firstName"] = parts[0]
                    entities["lastName"] = " ".join(parts[1:])
                elif len(parts) == 1:
                    entities["firstName"] = parts[0]
        
        return entities
    
    def _detect_intent(self, text: str) -> str:
        """Detect user intent from text."""
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return intent
        
        # Default intent based on keywords
        if any(word in text for word in ["create", "add", "new"]):
            return "create"
        elif any(word in text for word in ["find", "search", "get", "show", "list"]):
            return "search"
        elif any(word in text for word in ["update", "modify", "edit", "change"]):
            return "update"
        
        return "unknown"
    
    async def _suggest_tools(self, intent: str, entities: Dict[str, Any], user_input: str) -> List[ToolCall]:
        """Suggest tools based on intent and entities."""
        suggestions = []
        
        # Map intents to tool suggestions
        if intent == "create_contact":
            suggestions.extend(await self._suggest_contact_creation_tools(entities))
        elif intent == "search_contacts":
            suggestions.extend(await self._suggest_contact_search_tools(entities))
        elif intent == "update_contact":
            suggestions.extend(await self._suggest_contact_update_tools(entities))
        elif intent == "create_campaign":
            suggestions.extend(await self._suggest_campaign_creation_tools(entities))
        elif intent == "get_campaigns":
            suggestions.extend(await self._suggest_campaign_list_tools(entities))
        elif intent == "bulk_operations":
            suggestions.extend(await self._suggest_bulk_operation_tools(entities, user_input))
        
        # If no specific suggestions, try to infer from available tools
        if not suggestions and intent != "unknown":
            suggestions.extend(await self._suggest_generic_tools(intent, entities))
        
        return suggestions
    
    async def _suggest_contact_creation_tools(self, entities: Dict[str, Any]) -> List[ToolCall]:
        """Suggest tools for contact creation."""
        suggestions = []
        
        if "create_contact" in self.available_tools:
            tool_spec = self.available_tools["create_contact"]
            params = {}
            missing_params = []
            
            # Map entities to parameters
            if "firstName" in entities:
                params["firstName"] = entities["firstName"]
            else:
                missing_params.append("firstName")
            
            if "lastName" in entities:
                params["lastName"] = entities["lastName"]
            
            if "email" in entities:
                params["email"] = entities["email"]
            
            if "phone" in entities:
                params["phone"] = entities["phone"]
            
            # Location ID is usually required
            if "location_id" in entities:
                params["locationId"] = entities["location_id"]
            else:
                missing_params.append("locationId")
            
            suggestions.append(ToolCall(
                tool_name="create_contact",
                parameters=params,
                missing_params=missing_params,
                confidence=0.9,
                description="Create a new contact with the provided information"
            ))
        
        return suggestions
    
    async def _suggest_contact_search_tools(self, entities: Dict[str, Any]) -> List[ToolCall]:
        """Suggest tools for contact searching."""
        suggestions = []
        
        # If we have specific contact ID, get that contact
        if "contact_id" in entities and "get_contact" in self.available_tools:
            suggestions.append(ToolCall(
                tool_name="get_contact",
                parameters={"contactId": entities["contact_id"]},
                missing_params=[],
                confidence=0.95,
                description="Get specific contact by ID"
            ))
        
        # Otherwise, list contacts with filters
        if "get_contacts" in self.available_tools:
            params = {}
            missing_params = []
            
            if "location_id" in entities:
                params["locationId"] = entities["location_id"]
            else:
                missing_params.append("locationId")
            
            suggestions.append(ToolCall(
                tool_name="get_contacts",
                parameters=params,
                missing_params=missing_params,
                confidence=0.8,
                description="Get list of contacts"
            ))
        
        return suggestions
    
    async def _suggest_contact_update_tools(self, entities: Dict[str, Any]) -> List[ToolCall]:
        """Suggest tools for contact updating."""
        suggestions = []
        
        if "update_contact" in self.available_tools:
            params = {}
            missing_params = []
            
            if "contact_id" in entities:
                params["contactId"] = entities["contact_id"]
            else:
                missing_params.append("contactId")
            
            # Build update payload
            update_data = {}
            if "firstName" in entities:
                update_data["firstName"] = entities["firstName"]
            if "lastName" in entities:
                update_data["lastName"] = entities["lastName"]
            if "email" in entities:
                update_data["email"] = entities["email"]
            if "phone" in entities:
                update_data["phone"] = entities["phone"]
            
            if update_data:
                params["request_body"] = update_data
            
            suggestions.append(ToolCall(
                tool_name="update_contact",
                parameters=params,
                missing_params=missing_params,
                confidence=0.85,
                description="Update contact with new information"
            ))
        
        return suggestions
    
    async def _suggest_campaign_creation_tools(self, entities: Dict[str, Any]) -> List[ToolCall]:
        """Suggest tools for campaign creation."""
        suggestions = []
        
        if "create_campaign" in self.available_tools:
            params = {}
            missing_params = []
            
            if "location_id" in entities:
                params["locationId"] = entities["location_id"]
            else:
                missing_params.append("locationId")
            
            # Campaign name is required but might not be explicitly extracted
            missing_params.append("name")
            
            suggestions.append(ToolCall(
                tool_name="create_campaign",
                parameters=params,
                missing_params=missing_params,
                confidence=0.8,
                description="Create a new marketing campaign"
            ))
        
        return suggestions
    
    async def _suggest_campaign_list_tools(self, entities: Dict[str, Any]) -> List[ToolCall]:
        """Suggest tools for listing campaigns."""
        suggestions = []
        
        if "get_campaigns" in self.available_tools:
            params = {}
            missing_params = []
            
            if "location_id" in entities:
                params["locationId"] = entities["location_id"]
            else:
                missing_params.append("locationId")
            
            suggestions.append(ToolCall(
                tool_name="get_campaigns",
                parameters=params,
                missing_params=missing_params,
                confidence=0.9,
                description="Get list of campaigns"
            ))
        
        return suggestions
    
    async def _suggest_bulk_operation_tools(self, entities: Dict[str, Any], user_input: str) -> List[ToolCall]:
        """Suggest tools for bulk operations."""
        suggestions = []
        
        # For bulk operations, we might need multiple sequential calls
        if "contact" in user_input.lower():
            # First get contacts, then perform operations on them
            if "get_contacts" in self.available_tools:
                params = {}
                missing_params = []
                
                if "location_id" in entities:
                    params["locationId"] = entities["location_id"]
                else:
                    missing_params.append("locationId")
                
                suggestions.append(ToolCall(
                    tool_name="get_contacts",
                    parameters=params,
                    missing_params=missing_params,
                    confidence=0.7,
                    description="Get contacts for bulk operation"
                ))
        
        return suggestions
    
    async def _suggest_generic_tools(self, intent: str, entities: Dict[str, Any]) -> List[ToolCall]:
        """Suggest tools based on generic intent patterns."""
        suggestions = []
        
        # Match tools by name patterns
        for tool_name in self.available_tools:
            confidence = 0.0
            
            if intent == "create" and "create" in tool_name:
                confidence = 0.6
            elif intent == "search" and any(word in tool_name for word in ["get", "list", "search"]):
                confidence = 0.6
            elif intent == "update" and "update" in tool_name:
                confidence = 0.6
            
            if confidence > 0:
                suggestions.append(ToolCall(
                    tool_name=tool_name,
                    parameters={},
                    missing_params=["locationId"],  # Most GHL tools need this
                    confidence=confidence,
                    description=f"Generic suggestion for {intent} operation"
                ))
        
        return suggestions
    
    def _generate_clarification_message(self, tools: List[ToolCall]) -> str:
        """Generate a clarification message for missing parameters."""
        if not tools:
            return "I need more information to help you."
        
        missing_params = set()
        for tool in tools:
            missing_params.update(tool.missing_params)
        
        if not missing_params:
            return None
        
        param_descriptions = {
            "locationId": "your GoHighLevel Location ID",
            "firstName": "the first name",
            "lastName": "the last name",
            "email": "the email address",
            "phone": "the phone number",
            "contactId": "the contact ID",
            "campaignId": "the campaign ID",
            "name": "the name"
        }
        
        missing_descriptions = []
        for param in missing_params:
            desc = param_descriptions.get(param, param)
            missing_descriptions.append(desc)
        
        if len(missing_descriptions) == 1:
            return f"I need {missing_descriptions[0]} to complete this request."
        elif len(missing_descriptions) == 2:
            return f"I need {missing_descriptions[0]} and {missing_descriptions[1]} to complete this request."
        else:
            return f"I need {', '.join(missing_descriptions[:-1])}, and {missing_descriptions[-1]} to complete this request."
    
    async def execute_tool_sequence(self, tools: List[ToolCall], mcp_server) -> List[Dict[str, Any]]:
        """
        Execute a sequence of tool calls.
        
        Args:
            tools: List of tool calls to execute
            mcp_server: The MCP server instance
            
        Returns:
            List of results from tool executions
        """
        results = []
        
        for tool in tools:
            if tool.missing_params:
                results.append({
                    "error": f"Missing required parameters: {', '.join(tool.missing_params)}",
                    "tool": tool.tool_name,
                    "missing_params": tool.missing_params
                })
                continue
            
            try:
                # Execute the tool (this would be implemented with actual MCP tool calling)
                result = await self._execute_single_tool(tool, mcp_server)
                results.append({
                    "success": True,
                    "tool": tool.tool_name,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "error": str(e),
                    "tool": tool.tool_name,
                    "parameters": tool.parameters
                })
        
        return results
    
    async def _execute_single_tool(self, tool: ToolCall, mcp_server) -> Dict[str, Any]:
        """
        Execute a single tool call.
        This is a placeholder - actual implementation would use MCP protocol.
        """
        # This would integrate with the actual MCP server tool execution
        return {
            "message": f"Executed {tool.tool_name} with parameters {tool.parameters}",
            "parameters": tool.parameters
        }