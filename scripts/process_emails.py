import subprocess
import json
import re
from pathlib import Path
from email.utils import parseaddr

def process():
    workspace = Path("/home/openclaw/.openclaw/workspace/fleench.me")
    inbox = "holtbot@agentmail.to"
    sender_filter = "webmaster@flench.me"
    
    # 1. Fetch messages
    result = subprocess.run(["agentmail", "message", "list", inbox, "--json"], 
                            capture_output=True, text=True, cwd=workspace)
    if result.returncode != 0:
        print("Failed to list messages")
        return
        
    messages_data = json.loads(result.stdout).get("messages", [])
    if not messages_data:
        print("No messages found")
        return

    tasks = []
    saved_tasks = []
    private_qa = []
    public_qa = []
    
    for msg_meta in messages_data:
        msg_id = msg_meta["messageId"]
        detail = subprocess.run(["agentmail", "message", "get", inbox, msg_id, "--json"], 
                                capture_output=True, text=True, cwd=workspace)
        msg = json.loads(detail.stdout)
        
        if sender_filter not in msg["from"]:
            continue
            
        text = msg.get("text", "")
        
        # Simple task/qa parsing logic
        if "Task:" in text:
            tasks.append(text)
        elif "Private Question:" in text:
            private_qa.append(text)
        elif "Public Question:" in text:
            public_qa.append(text)
        else:
            tasks.append(f"Uncategorized: {text}")

        # 2. Archive
        subprocess.run(["agentmail", "message", "delete", inbox, msg_id], cwd=workspace)
        
    # 3. Report
    print(f"Tasks: {tasks}")
    print(f"Private Q&A: {private_qa}")
    print(f"Public Q&A: {public_qa}")

if __name__ == "__main__":
    process()
