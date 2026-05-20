"""Quick manual test of the AI extraction."""
import os, sys
import litellm
litellm.set_verbose = True

sys.path.insert(0, os.getcwd())
from app.services.ai import extract_from_text

test_text = "Met with Alice from Acme Corp on 2025-04-02. Discussed Q2 planning and pricing. She seemed positive. We need to send a quote and schedule a follow-up."

print("Sending test text to Mistral Small...")
try:
    result = extract_from_text(test_text)
    print("Extraction result:")
    print(result)
except Exception as e:
    print("Error:", e)
