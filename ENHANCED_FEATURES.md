# Enhanced GoHighLevel MCP Server Features

## 🚀 Intelligent LibreChat Integration for OpenAI Agents

This enhanced version of the GoHighLevel MCP server adds intelligent capabilities specifically designed for LibreChat integration with OpenAI agents. The system can now handle multiple tool calling in single user inputs, analyze user intent intelligently, and handle missing data gracefully.

## ✨ Key Enhancements

### 🧠 Intelligent Input Analysis
The server now includes an intelligent agent that can:
- **Parse natural language requests** and understand user intent
- **Extract entities** from user input (names, emails, phone numbers, IDs)
- **Map intents to appropriate tools** with confidence scoring
- **Handle complex, multi-step operations** in a single request

### 🔧 Smart Tool Selection
- **analyze_and_execute**: Main intelligent tool that orchestrates multiple tool calls
- **suggest_tools_for_input**: Get tool suggestions without executing
- **get_missing_parameters**: Check what parameters are needed for tool execution
- **get_available_tools_summary**: Browse available tools organized by category

### 🔍 Missing Parameter Detection
- **Automatic validation** of required parameters before tool execution
- **Intelligent prompting** for missing information with specific guidance
- **Context-aware suggestions** based on the user's request
- **Graceful error handling** with actionable next steps

### 🔄 Multi-Tool Calling Support
- **Sequential tool execution** for complex workflows
- **Dependency management** between related tools
- **Result chaining** where outputs from one tool inform the next
- **Comprehensive progress reporting** for multi-step operations

## 🛠️ Enhanced Tools

### Primary Intelligent Tools

#### `analyze_and_execute`
The main entry point for intelligent tool calling.

**Input**: Natural language request from user
**Features**:
- Analyzes user intent and extracts entities
- Suggests appropriate tools with confidence scores
- Handles missing parameters by asking for clarification
- Executes multiple tools in sequence if needed
- Provides comprehensive results with explanations

**Example Usage**:
```
User: "Create a contact named John Doe with email john@example.com and add him to my Summer Sale campaign"

System Response:
1. Analyzes intent: Contact creation + Campaign assignment
2. Extracts entities: firstName="John", lastName="Doe", email="john@example.com"
3. Identifies missing: locationId for both operations
4. Asks: "I need your GoHighLevel Location ID to create the contact and assign them to the campaign"
5. Once provided, executes both tools in sequence
```

#### `suggest_tools_for_input`
Suggests tools without executing them.

**Use Cases**:
- Preview what the system will do before execution
- Understand tool selection logic
- Debug complex requests

#### `get_missing_parameters`
Check parameter requirements for specific tools.

**Use Cases**:
- Validate tool readiness before execution
- Understand what information is needed
- Build progressive forms in the UI

#### `get_available_tools_summary`
Browse all available tools organized by category.

**Categories**:
- **Contacts**: Contact management operations
- **Campaigns**: Marketing campaign operations  
- **Opportunities**: Sales pipeline management
- **Workflows**: Automation management
- **Other**: Additional GoHighLevel API tools

## 🎯 Intent Recognition

The system recognizes the following intents:

### Contact Management
- **create_contact**: "Create a contact", "Add a new person", "Register customer"
- **search_contacts**: "Find contact", "Show contacts", "List customers"
- **update_contact**: "Update contact", "Modify customer", "Change details"

### Campaign Management
- **create_campaign**: "Create campaign", "New campaign", "Start marketing"
- **get_campaigns**: "Show campaigns", "List campaigns", "View marketing"

### Bulk Operations
- **bulk_operations**: "Bulk update", "Multiple contacts", "Mass operation"

### Generic Operations
- **create**: Any creation-related request
- **search**: Any search/retrieval request
- **update**: Any modification request

## 🔧 Entity Extraction

The system automatically extracts:

### Contact Information
- **Names**: First name, last name detection
- **Email addresses**: Validated email format
- **Phone numbers**: Various phone number formats
- **Contact IDs**: Specific contact identifiers

### System Identifiers
- **Location IDs**: GoHighLevel location identifiers
- **Campaign IDs**: Campaign identifiers
- **Contact IDs**: Extracted from context

## 📚 Usage Examples

### Simple Contact Creation
```
User: "Create a contact for Sarah Johnson with email sarah.johnson@company.com"

System:
1. Intent: create_contact
2. Entities: firstName="Sarah", lastName="Johnson", email="sarah.johnson@company.com"
3. Missing: locationId
4. Response: "I need your GoHighLevel Location ID to create this contact."
```

### Multi-Tool Workflow
```
User: "I want to create a welcome campaign and add all my contacts from location abc123 to it"

System:
1. Intent: Multi-tool operation
2. Plan: 
   - Create campaign (needs name)
   - Get contacts from location
   - Add contacts to campaign
3. Missing: Campaign name
4. Response: "I need a name for the welcome campaign to proceed."
```

### Contact Search and Update
```
User: "Find John Smith and update his phone to 555-0199"

System:
1. Intent: search + update
2. Plan:
   - Search for contacts named John Smith
   - Update the found contact's phone
3. Missing: locationId for search
4. Response: "I need your Location ID to search for John Smith."
```

## 🤖 OpenAI Agent Integration

### Function Calling Optimization
- **Structured parameters**: All tools use clear, typed parameters
- **Detailed descriptions**: Comprehensive tool and parameter descriptions
- **Error handling**: Graceful error responses with suggestions
- **Result formatting**: Consistent, parseable response formats

### Token Efficiency
- **Smart tool selection**: Reduces unnecessary tool calls
- **Batch operations**: Combines related operations
- **Context preservation**: Maintains state across calls
- **Compressed responses**: Efficient result formatting

### Natural Language Interface
- **Intent understanding**: Processes natural language requests
- **Entity extraction**: Automatically finds relevant data in requests
- **Clarification dialogs**: Asks specific questions for missing data
- **Explanation generation**: Provides clear explanations of actions

## 🔧 Configuration for LibreChat

### Basic Configuration
Use the provided `librechat.enhanced.yaml` for optimal setup:

```yaml
mcpServers:
  gohighlevel:
    name: "GoHighLevel CRM (Enhanced)"
    command: "python"
    args: ["/path/to/ghl-mcp-app/src/enhanced_main.py"]
    env:
      GHL_API_KEY: "your-ghl-api-key-here"
      GHL_LOCATION_ID: "your-ghl-location-id-here"
```

### Tool Whitelisting
For optimal performance, whitelist the key intelligent tools:

```yaml
tools:
  enabled: true
  whitelist:
    - "analyze_and_execute"          # Main intelligent tool
    - "suggest_tools_for_input"      # Tool suggestions
    - "get_missing_parameters"       # Parameter validation
    - "get_available_tools_summary"  # Tool browsing
    # Add specific GoHighLevel tools as needed
    - "get_contacts"
    - "create_contact"
    - "get_campaigns"
    - "create_campaign"
```

### Model Configuration
Optimize OpenAI models for tool calling:

```yaml
models:
  openai:
    gpt-4o:
      temperature: 0.1  # Lower temperature for consistent tool calling
      tools:
        enabled: true
        preferred: ["analyze_and_execute"]
        parallel: true  # Enable parallel tool calling
```

## 🧪 Testing the Enhanced Features

Run the test suite to verify functionality:

```bash
python test_intelligent_features.py
```

This tests:
- Intent recognition accuracy
- Entity extraction capabilities
- Missing parameter detection
- Multi-tool orchestration
- Error handling and recovery

## 🚦 Getting Started

### 1. Start the Enhanced Server
```bash
python src/enhanced_main.py
```

### 2. Configure LibreChat
Copy and customize the enhanced configuration:
```bash
cp librechat.enhanced.yaml /path/to/librechat/librechat.yaml
```

### 3. Update API Credentials
Edit the configuration file with your actual GoHighLevel credentials:
- `GHL_API_KEY`: Your GoHighLevel API key
- `GHL_LOCATION_ID`: Your GoHighLevel location ID

### 4. Restart LibreChat
Restart LibreChat to load the new configuration.

### 5. Test the Integration
Try these example requests in LibreChat:

- "Create a contact named Alice with email alice@example.com"
- "Show me all my campaigns"
- "I want to create a follow-up campaign for all contacts"
- "Find contact with ID 12345 and update their phone number"

## 🔍 Troubleshooting

### Common Issues

**"Missing Location ID" errors**:
- Ensure `GHL_LOCATION_ID` is set in your environment
- Double-check the location ID in your GoHighLevel settings

**Tool selection issues**:
- Use more specific language in requests
- Try the `suggest_tools_for_input` tool to see what the system understands
- Check available tools with `get_available_tools_summary`

**Multi-tool operations failing**:
- Ensure all required parameters are provided upfront
- Use the `analyze_and_execute` tool for complex operations
- Check individual tool requirements with `get_missing_parameters`

### Debug Mode
Enable verbose logging:
```bash
export FASTMCP_LOG_LEVEL=DEBUG
python src/enhanced_main.py
```

## 🎉 Benefits for OpenAI Agents

### Enhanced User Experience
- **Natural language processing**: Users can speak naturally
- **Intelligent clarification**: System asks for exactly what's needed
- **Multi-step automation**: Complex workflows in single requests
- **Comprehensive feedback**: Clear explanations of what was done

### Developer Benefits  
- **Reduced complexity**: Less need to handle individual tools
- **Better error handling**: Graceful failures with recovery suggestions
- **Consistent interface**: Unified tool calling patterns
- **Comprehensive logging**: Detailed operation tracking

### Performance Improvements
- **Fewer API calls**: Intelligent batching and optimization
- **Context preservation**: Maintains state across operations
- **Smart caching**: Reuses results where appropriate
- **Efficient parameter handling**: Validates before execution

---

The enhanced GoHighLevel MCP server transforms the LibreChat experience, making it feel like you have an intelligent CRM assistant that understands natural language and can handle complex, multi-step operations with ease.