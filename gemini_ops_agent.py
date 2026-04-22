import os
import subprocess
import datetime
from google import genai
from google.genai import types

# 1. Load your existing, shared sources of truth (No changes to Claude needed)
def load_system_instructions():
    try:
        with open("system-prompt.txt", "r") as f:
            prompt = f.read()
        with open("server-ops-runbook.md", "r") as f:
            runbook = f.read()
        return f"{prompt}\n\n=== RUNBOOK ===\n{runbook}"
    except FileNotFoundError:
        return "You are an automated operations and remediation agent. Act safely."

# 2. Define Gemini's Tool (Function Calling)
# This replicates what guard-ops-harness.py does for Claude, but natively for Gemini
def execute_server_command(command: str, mode: str, justification: str) -> str:
    """
    Executes a server command via the opsctl harness. 
    
    Args:
        command: The bash command or opsctl command to run.
        mode: Must be either 'Observe' or 'Repair'.
        justification: A brief explanation of why this command is safe and necessary.
    """
    print(f"\n[GEMINI TOOL EXECUTION]")
    print(f"Mode: {mode}")
    print(f"Command: {command}")
    print(f"Justification: {justification}")
    
    # Enforce Observe vs Repair modes at the harness level
    if mode not in ["Observe", "Repair"]:
        return "ERROR: Mode must be 'Observe' or 'Repair'."
        
    if mode == "Observe":
        # Deny list for Observe mode
        dangerous_keywords = ["rm", "restart", "stop", "down", "kill", "chmod", "chown"]
        if any(keyword in command for keyword in dangerous_keywords):
            return f"ERROR: Command contains dangerous keywords not allowed in Observe mode."
            
    if mode == "Repair":
        # Explicit human-in-the-loop prompt before proceeding
        print(f"\n[WARNING] Gemini is requesting REPAIR mode execution.")
        approval = input(f"Allow command: `{command}`? (y/n): ")
        if approval.lower() != 'y':
            with open("gemini_ops_audit.log", "a") as log_file:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_file.write(f"[{timestamp}] REJECTED REPAIR | CMD: {command} | JUSTIFICATION: {justification}\n")
            print("[DENIED] Command execution blocked by user.")
            return "ERROR: Human operator denied the execution of this REPAIR command."
        
    # Execute the command
    try:
        # Using timeout and capture_output to ensure the agent doesn't hang forever
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=60
        )
        output = result.stdout if result.returncode == 0 else f"ERROR:\n{result.stderr}"
        
        # Keep a local log file of every executed command
        with open("gemini_ops_audit.log", "a") as log_file:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"[{timestamp}] MODE: {mode} | CMD: {command} | JUSTIFICATION: {justification} | SUCCESS: {result.returncode == 0}\n")
            
        return output
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out after 60 seconds."
    except Exception as e:
        return f"ERROR: {str(e)}"

# 3. Initialize the Gemini Agent
def main():
    # Ensure your API key is set in the environment: GEMINI_API_KEY
    client = genai.Client()
    
    instructions = load_system_instructions()
    
    # Configure the model to use your tools and system instructions
    config = types.GenerateContentConfig(
        system_instruction=instructions,
        tools=[execute_server_command],
        temperature=0.2, # Low temp for deterministic DevOps tasks
    )
    
    print("Starting Gemini Server Ops Agent (Type 'exit' to quit)...\n")
    chat = client.chats.create(model="gemini-2.5-pro", config=config)
    
    while True:
        user_input = input("Operator> ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        response = chat.send_message(user_input)
        
        # Print Gemini's reasoning and response
        print(f"\nGemini> {response.text}\n")

if __name__ == "__main__":
    main()