"""
Setup script for advanced RAG system
Automates the entire setup process
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking environment...")
    
    # Check if we're in the right directory
    if not Path("../simple_rag_system.py").exists():
        print("❌ Please run this script from the advanced_rag directory")
        return False
    
    # Check environment variables
    env_file = Path("../.env")
    if not env_file.exists():
        print("❌ .env file not found in parent directory")
        return False
    
    # Load and check required variables
    required_vars = ['GOOGLE_API_KEY', 'SUPABASE_URL', 'SUPABASE_KEY']
    missing_vars = []
    
    with open(env_file) as f:
        env_content = f.read()
        for var in required_vars:
            if f"{var}=" not in env_content:
                missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ Environment check passed")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    # Check if requirements file exists
    if not Path("requirements_advanced.txt").exists():
        print("❌ requirements_advanced.txt not found")
        return False
    
    # Install dependencies - try pip3 first, then pip
    success = run_command(
        "pip3 install -r requirements_advanced.txt",
        "Installing Python packages with pip3"
    )
    
    if not success:
        success = run_command(
            "pip install -r requirements_advanced.txt", 
            "Installing Python packages with pip"
        )
    
    return success

def sync_data():
    """Synchronize data for safe testing"""
    print("🔄 Synchronizing data...")
    
    try:
        from data_sync import DataSynchronizer
        
        syncer = DataSynchronizer()
        success = syncer.sync_data(create_subset=True)
        
        if success:
            print("✅ Data synchronization completed")
            return True
        else:
            print("❌ Data synchronization failed")
            return False
            
    except Exception as e:
        print(f"❌ Data sync failed: {str(e)}")
        return False

def setup_vector_store():
    """Setup and populate vector store"""
    print("🗄️ Setting up vector store...")
    
    try:
        # Import and run vector store setup
        from vector_store import VectorStoreManager
        
        manager = VectorStoreManager()
        
        # Check if already populated
        if manager.collection.count() > 0:
            print(f"✅ Vector store already has {manager.collection.count()} documents")
            return True
        
        # Populate vector store
        print("📥 Populating vector store with survey data...")
        manager.populate_vector_store()
        
        if manager.collection.count() > 0:
            print(f"✅ Vector store populated with {manager.collection.count()} documents")
            return True
        else:
            print("❌ Vector store population failed")
            return False
            
    except Exception as e:
        print(f"❌ Vector store setup failed: {str(e)}")
        return False

def test_system():
    """Test the complete system"""
    print("🧪 Testing system...")
    
    try:
        from test_advanced import main as run_tests
        
        # Redirect stdout to capture test output
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            run_tests()
        
        output = f.getvalue()
        
        if "ALL TESTS PASSED" in output:
            print("✅ All system tests passed")
            return True
        else:
            print("❌ Some tests failed")
            print("Last few lines of test output:")
            lines = output.split('\n')[-10:]
            for line in lines:
                if line.strip():
                    print(f"   {line}")
            return False
            
    except Exception as e:
        print(f"❌ System testing failed: {str(e)}")
        return False

def main():
    """Run complete setup process"""
    print("🚀 ADVANCED RAG SYSTEM SETUP")
    print("=" * 50)
    print("This script will:")
    print("1. Check environment configuration")
    print("2. Install required dependencies")
    print("3. Synchronize data safely")
    print("4. Setup and populate vector store")
    print("5. Test the complete system")
    print("=" * 50)
    
    # Step 1: Environment check
    if not check_environment():
        print("\n❌ Setup failed at environment check")
        return
    
    # Step 2: Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed at dependency installation")
        return
    
    # Step 3: Data synchronization
    if not sync_data():
        print("\n❌ Setup failed at data synchronization")
        return
    
    # Step 4: Setup vector store
    if not setup_vector_store():
        print("\n❌ Setup failed at vector store setup")
        return
    
    # Step 5: Test system
    if not test_system():
        print("\n⚠️  Setup completed but some tests failed")
        print("You can still try running the system manually")
    else:
        print("\n🎉 SETUP COMPLETED SUCCESSFULLY!")
    
    print("\n" + "=" * 50)
    print("NEXT STEPS:")
    print("=" * 50)
    print("1. Test individual components:")
    print("   python embeddings_test.py")
    print("   python vector_store.py")
    print("   python langchain_rag.py")
    print("")
    print("2. Run comprehensive tests:")
    print("   python test_advanced.py")
    print("")
    print("3. Start the advanced server:")
    print("   python advanced_server.py")
    print("")
    print("4. Run objective benchmark comparison:")
    print("   python benchmark_comparison.py")
    print("")
    print("5. Compare with simple system:")
    print("   # Advanced server runs on port 8001")
    print("   # Simple server runs on port 8000")
    print("")
    print("6. Sync fresh data when needed:")
    print("   python data_sync.py")
    print("=" * 50)

if __name__ == "__main__":
    main()