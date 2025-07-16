#!/usr/bin/env python3
"""
Install required dependencies for environment debugging and consistency testing
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def main():
    """Main installation function"""
    print("🔧 Installing Dependencies for Environment Debugging")
    print("=" * 55)
    
    # Required packages
    packages = [
        "aiohttp==3.9.1",
        "beautifulsoup4==4.12.2",
        "certifi==2023.11.17",
        "lxml==4.9.3",
        "brotli==1.1.0",
        "charset-normalizer==3.3.2",
        "idna==3.6",
        "multidict==6.0.4",
        "yarl==1.9.4",
        "soupsieve==2.5"
    ]
    
    successful = 0
    failed = 0
    
    for package in packages:
        print(f"\n📦 Installing {package}...")
        if install_package(package):
            successful += 1
        else:
            failed += 1
    
    print(f"\n🎯 Installation Summary:")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All dependencies installed successfully!")
        print("You can now run the debug and consistency test scripts.")
    else:
        print(f"\n⚠️  {failed} packages failed to install.")
        print("Please check the error messages above and try installing manually.")
    
    # Verify installations
    print(f"\n🔍 Verifying installations...")
    
    verification_imports = [
        ("aiohttp", "aiohttp"),
        ("beautifulsoup4", "bs4"),
        ("certifi", "certifi"),
        ("lxml", "lxml"),
        ("brotli", "brotli")
    ]
    
    for package_name, import_name in verification_imports:
        try:
            __import__(import_name)
            print(f"✅ {package_name} - OK")
        except ImportError:
            print(f"❌ {package_name} - Import failed")

if __name__ == "__main__":
    main()
