#!/bin/bash

# Ensure filesystem MCP server is installed
npm install -g @modelcontextprotocol/server-filesystem

# Register the filesystem MCP server with Gemini CLI
# This links the server to your current project directory
gemini mcp add filesystem \
  --command "npx" \
  --args "-y @modelcontextprotocol/server-filesystem /home/openclaw/.openclaw/workspace/fleench.me"

echo "Configuration complete. The Gemini CLI is now linked to your repository."
