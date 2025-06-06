import os
import subprocess
import json
from pathlib import Path

def run_command(command):
    """Run a shell command and return its output"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print(f"Error output: {e.stderr}")
        raise

def setup_virtual_environment():
    """Set up Python virtual environment"""
    print("Setting up virtual environment...")
    run_command("python -m venv venv")
    
    # Activate virtual environment
    if os.name == 'nt':  # Windows
        activate_script = "venv\\Scripts\\activate"
    else:  # Unix/Linux
        activate_script = "source venv/bin/activate"
    
    return activate_script

def install_dependencies(activate_script):
    """Install project dependencies"""
    print("Installing dependencies...")
    run_command(f"{activate_script} && pip install -r requirements.txt")
    run_command(f"{activate_script} && pip install aws-cdk-lib")

def deploy_infrastructure():
    """Deploy AWS infrastructure using CDK"""
    print("Deploying infrastructure...")
    
    # Initialize CDK app if not already initialized
    if not Path("cdk.json").exists():
        run_command("cdk init app --language python")
    
    # Deploy the stack
    run_command("cdk deploy --require-approval never")

def upload_initial_data():
    """Upload initial knowledge base and model data to S3"""
    print("Uploading initial data...")
    
    # Create knowledge base directory if it doesn't exist
    os.makedirs("data/knowledge_base", exist_ok=True)
    
    # Create initial knowledge base file
    initial_kb = {
        "intents": {
            "greeting": {
                "patterns": ["hi", "hello", "hey", "good morning", "good afternoon"],
                "responses": ["Hello!", "Hi there!", "Hey! How can I help you?"]
            },
            "farewell": {
                "patterns": ["bye", "goodbye", "see you", "see you later"],
                "responses": ["Goodbye!", "See you later!", "Take care!"]
            },
            "thanks": {
                "patterns": ["thank you", "thanks", "appreciate it"],
                "responses": ["You're welcome!", "Happy to help!", "Anytime!"]
            }
        }
    }
    
    with open("data/knowledge_base/initial_kb.json", "w") as f:
        json.dump(initial_kb, f, indent=2)
    
    # Upload to S3 (replace with your bucket name)
    run_command("aws s3 cp data/knowledge_base/initial_kb.json s3://chatbot-knowledge-base/knowledge_base.json")

def main():
    """Main deployment function"""
    try:
        # Setup virtual environment
        activate_script = setup_virtual_environment()
        
        # Install dependencies
        install_dependencies(activate_script)
        
        # Deploy infrastructure
        deploy_infrastructure()
        
        # Upload initial data
        upload_initial_data()
        
        print("Deployment completed successfully!")
        
    except Exception as e:
        print(f"Deployment failed: {str(e)}")
        raise

if __name__ == "__main__":
    main() 