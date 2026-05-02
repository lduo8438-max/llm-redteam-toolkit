#!/usr/bin/env python3
"""Test a single payload against the target."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'targets'))
from chat_app import chat

if __name__ == "__main__":
    payload = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Payload: ")
    print(chat(payload))
