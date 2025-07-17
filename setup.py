import os
from dotenv import load_dotenv
import subprocess

# Load environment variables from .env file
load_dotenv()

GUARDRAILS_TOKEN = os.getenv("GUARDRAILS_TOKEN")
if not GUARDRAILS_TOKEN:
    raise RuntimeError("GUARDRAILS_TOKEN not found in .env file.")

# Run the guardrails configuration and hub install commands
subprocess.run([
    "guardrails", "configure",
    "--disable-metrics",
    "--disable-remote-inferencing",
    "--token", GUARDRAILS_TOKEN
], check=True)

subprocess.run([
    "guardrails", "hub", "install", "hub://guardrails/detect_pii"
], check=True)

subprocess.run([
    "guardrails", "hub", "install", "hub://cartesia/mentions_drugs"
], check=True)

subprocess.run([
    "guardrails", "hub", "install", "hub://guardrails/web_sanitization"
], check=True)
