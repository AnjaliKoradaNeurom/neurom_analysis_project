#!/usr/bin/env python3
"""
Environment variable checker for Neurom AI Website Analyzer
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def check_environment():
    """Check if all required environment variables are properly loaded"""
    
    print("🔍 Environment Variable Checker")
    print("=" * 50)
    
    # Try to load .env file
    env_path = Path('.env')
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Found .env file: {env_path.absolute()}")
    else:
        print(f"❌ No .env file found at: {env_path.absolute()}")
        return False
    
    # Check critical environment variables
    checks = []
    
    # OpenAI API Key
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        if openai_key.startswith('sk-'):
            print(f"✅ OpenAI API Key: Found (length: {len(openai_key)})")
            checks.append(True)
        else:
            print(f"❌ OpenAI API Key: Invalid format (should start with 'sk-')")
            checks.append(False)
    else:
        print("❌ OpenAI API Key: Not found")
        checks.append(False)
    
    # Google API Key
    google_key = os.getenv('GOOGLE_API_KEY')
    if google_key:
        if google_key.startswith('AIza'):
            print(f"✅ Google API Key: Found (length: {len(google_key)})")
            checks.append(True)
        else:
            print(f"⚠️ Google API Key: Unusual format (expected to start with 'AIza')")
            checks.append(True)  # Still count as valid
    else:
        print("⚠️ Google API Key: Not found (optional)")
        checks.append(True)  # Optional, so don't fail
    
    # Server Configuration
    host = os.getenv('HOST', '0.0.0.0')
    port = os.getenv('PORT', '8000')
    debug = os.getenv('DEBUG', 'false')
    
    print(f"✅ Server Config: HOST={host}, PORT={port}, DEBUG={debug}")
    checks.append(True)
    
    # Optional configurations
    optional_vars = [
        'LIGHTHOUSE_PATH',
        'DEEPINFRA_API_KEY',
        'GROQ_API_KEY',
        'XAI_API_KEY',
        'FAL_KEY',
        'DATABASE_URL'
    ]
    
    print("\n📋 Optional Configuration:")
    for var in optional_vars:
        value = os.getenv(var)
        if value and not value.startswith('your-'):
            print(f"✅ {var}: Configured")
        else:
            print(f"⚪ {var}: Not configured (optional)")
    
    # Summary
    print("\n" + "=" * 50)
    if all(checks):
        print("✅ All critical environment variables are properly configured!")
        print("🚀 Ready to start the application")
        return True
    else:
        print("❌ Some critical environment variables are missing or invalid")
        print("Please check your .env file and try again")
        return False

def main():
    """Main function"""
    try:
        success = check_environment()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error checking environment: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
