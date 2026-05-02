#!/usr/bin/env python3
import re
from typing import Tuple, Dict, List

def filter_output(text: str) -> Tuple[str, Dict[str, List[str]]]:
    """過濾 PII 並返回過濾後文字和偵測報告"""
    report = {
        "email": [],
        "phone": [],
        "ip": [],
        "api_key": [],
        "credit_card": [],
        "id_number": [],
        "internal_host": []
    }

    # 信用卡號（先匹配避免被電話號碼截走）
    card_pattern = r'\b\d{4}[-\s]\d{4}[-\s]\d{4}[-\s]\d{4}\b'
    for match in re.finditer(card_pattern, text):
        report["credit_card"].append(match.group())
        text = text.replace(match.group(), "****-****-****-****")

    # IP 地址（先匹配避免被電話號碼截走）
    ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    for match in re.finditer(ip_pattern, text):
        report["ip"].append(match.group())
        text = text.replace(match.group(), "***.***.***.***")

    # 電話號碼
    phone_pattern = r'\+?\d{1,4}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
    for match in re.finditer(phone_pattern, text):
        if len(re.sub(r'\D', '', match.group())) >= 8:
            report["phone"].append(match.group())
            text = text.replace(match.group(), "+886-***-***-****")

    # Email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    for match in re.finditer(email_pattern, text):
        report["email"].append(match.group())
        user, domain = match.group().split('@')
        text = text.replace(match.group(), f"{user}@{domain[0]}***.{domain.split('.')[-1]}")

    # API Key (sk- 開頭或長英數字串)
    api_pattern = r'\b(?:sk-|api[_-]?key[_-]?)[a-zA-Z0-9]{20,}\b|\b[a-zA-Z0-9]{32,}\b'
    for match in re.finditer(api_pattern, text):
        if not match.group().replace('-', '').replace('.', '').isdigit():
            report["api_key"].append(match.group())
            text = text.replace(match.group(), "[REDACTED-API-KEY]")

    # 台灣身分證字號
    id_pattern = r'\b[A-Z][12]\d{8}\b'
    for match in re.finditer(id_pattern, text):
        report["id_number"].append(match.group())
        text = text.replace(match.group(), "[REDACTED-ID]")

    # 內部域名
    internal_pattern = r'\b[\w.-]+\.(?:internal|corp|local)\b'
    for match in re.finditer(internal_pattern, text):
        report["internal_host"].append(match.group())
        text = text.replace(match.group(), "[INTERNAL-HOST]")

    return text, report

def wrap_llm_call(prompt: str, model: str, endpoint: str) -> Tuple[str, Dict]:
    """包裝 LLM 呼叫並自動過濾輸出"""
    # 模擬 LLM 呼叫（實際使用時替換為真實 API 呼叫）
    llm_output = f"Mock response for: {prompt}"
    filtered_output, report = filter_output(llm_output)
    return filtered_output, report

if __name__ == "__main__":
    test_text = """Please contact admin@company.com or call +886-912-345-678.
Server is at 192.168.1.100 (api.corp.internal).
API Key: sk-abc123def456ghi789jkl012.
Card: 4532-1234-5678-9012"""

    print("=== PII Filter Test ===\n")
    print("原始文字:")
    print(test_text)
    print("\n" + "="*50 + "\n")

    filtered, report = filter_output(test_text)

    print("過濾後文字:")
    print(filtered)
    print("\n" + "="*50 + "\n")

    print("偵測報告:")
    for pii_type, items in report.items():
        if items:
            print(f"  {pii_type}: {items}")
