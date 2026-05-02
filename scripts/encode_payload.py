#!/usr/bin/env python3
import sys
import base64
import json
from pathlib import Path
from urllib.parse import quote

def encode_payload(text):
    """Generate multiple encoding variants for security testing"""
    return {
        "original": text,
        "base64": base64.b64encode(text.encode()).decode(),
        "rot13": text.translate(str.maketrans(
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
            'NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm'
        )),
        "hex": text.encode().hex(),
        "unicode_escape": text.encode('unicode_escape').decode(),
        "url_encoded": quote(text),
        "reversed": text[::-1],
        "ascii_decimal": ' '.join(str(ord(c)) for c in text)
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 encode_payload.py \"your test string\"")
        sys.exit(1)

    payload = ' '.join(sys.argv[1:])
    results = encode_payload(payload)

    print("\n=== Encoded Payloads ===\n")
    for encoding, value in results.items():
        print(f"{encoding}:")
        print(f"  {value}\n")

    output_path = Path.home() / "llm-redteam/payloads/encoded_payloads.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"✓ Saved to {output_path}")
