#!/usr/bin/env python3
"""
Enhanced GoHighLevel MCP Server Setup Script

This script helps set up the enhanced server with intelligent features
for optimal LibreChat integration.
"""

import os
import shutil
from pathlib import Path


def create_env_file():
    """Create .env file with placeholder values."""
    env_content = """# Enhanced GoHighLevel MCP Server Configuration

# Required: Your GoHighLevel API credentials
GHL_API_KEY=your-ghl-api-key-here
GHL_LOCATION_ID=your-ghl-location-id-here

# Optional: API base URL (usually no need to change)
GHL_BASE_URL=https://services.leadconnectorhq.com

# Optional: Transport configuration
MCP_TRANSPORT=stdio
MCP_HOST=127.0.0.1
MCP_PORT=8000

# Optional: Enable experimental features
FASTMCP_EXPERIMENTAL_ENABLE_NEW_OPENAPI_PARSER=true
FASTMCP_LOG_LEVEL=INFO

# Optional: Enhanced features
INTELLIGENT_AGENT_ENABLED=true
MULTI_TOOL_CALLING_ENABLED=true
PARAMETER_VALIDATION_ENABLED=true
"""
    
    env_path = Path(".env")
    if not env_path.exists():
        with open(env_path, "w") as f:
            f.write(env_content)
        print("✅ Created .env file with default configuration")
        print("📝 Please edit .env and add your actual GoHighLevel credentials")
    else:
        print("ℹ️  .env file already exists")


def setup_librechat_config():
    """Set up LibreChat configuration."""
    src = Path("librechat.enhanced.yaml")
    
    if src.exists():
        print("✅ Enhanced LibreChat configuration available")
        print("📄 Copy librechat.enhanced.yaml to your LibreChat installation:")
        print("   cp librechat.enhanced.yaml /path/to/librechat/librechat.yaml")
    else:
        print("❌ Enhanced LibreChat configuration not found")


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import fastmcp
        import aiohttp
        import pydantic
        import httpx
        print("✅ All required dependencies are installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: pip install -r requirements.txt")


def verify_enhanced_files():
    """Verify enhanced files are present."""
    required_files = [
        "src/enhanced_main.py",
        "src/intelligent_agent.py", 
        "librechat.enhanced.yaml",
        "test_intelligent_features.py",
        "ENHANCED_FEATURES.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing enhanced files: {', '.join(missing_files)}")
        return False
    else:
        print("✅ All enhanced files are present")
        return True


def main():
    """Main setup function."""
    print("🚀 Enhanced GoHighLevel MCP Server Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("src/main.py").exists():
        print("❌ Please run this script from the ghl-mcp-chat-app directory")
        return
    
    print("\n📋 Checking setup...")
    
    # Verify enhanced files
    if not verify_enhanced_files():
        print("❌ Setup incomplete - missing enhanced files")
        return
    
    # Check dependencies
    check_dependencies()
    
    # Create environment file
    create_env_file()
    
    # Setup LibreChat config
    setup_librechat_config()
    
    print("\n" + "=" * 50)
    print("🎉 Setup Complete!")
    print("\n📝 Next Steps:")
    print("1. Edit .env and add your GoHighLevel API credentials")
    print("2. Copy librechat.enhanced.yaml to your LibreChat installation")
    print("3. Start the enhanced server: python src/enhanced_main.py")
    print("4. Test the features: python test_intelligent_features.py")
    print("\n📚 Documentation:")
    print("• ENHANCED_FEATURES.md - Detailed feature documentation")
    print("• librechat.enhanced.yaml - Optimized LibreChat configuration")
    print("\n🤖 The enhanced server provides:")
    print("• Intelligent input analysis")
    print("• Multi-tool calling support")
    print("• Missing parameter detection")
    print("• OpenAI agent optimization")
    
    print("\n💡 For LibreChat integration, use the 'analyze_and_execute' tool")
    print("   for intelligent, multi-step operations!")


if __name__ == "__main__":
    main()