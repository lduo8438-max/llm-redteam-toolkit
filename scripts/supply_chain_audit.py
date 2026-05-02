#!/usr/bin/env python3
"""
LLM Supply Chain Security Audit Tool
掃描 LLM 開發環境的供應鏈風險
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class SupplyChainAuditor:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_issues": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "findings": []
        }

        self.typosquat_packages = {
            "langchian": "langchain",
            "1angchain": "langchain",
            "langchain-core-ai": "langchain-core",
            "openal": "openai",
            "0penai": "openai",
            "openai-python": "openai",
            "anthropic-sdk": "anthropic",
            "anthropic-ai": "anthropic",
            "olama": "ollama",
            "0llama": "ollama",
            "ollama-python": "ollama"
        }

        self.vulnerable_versions = {
            "langchain": {"version": "0.1.0", "operator": "<", "cve": "Prompt Injection vulnerability"},
            "transformers": {"version": "4.36.0", "operator": "<", "cve": "Arbitrary code execution (CVE-2023-XXXX)"}
        }

        self.api_key_patterns = [
            # 更具體的模式放前面
            (r'sk-proj-[A-Za-z0-9]{40,}', 'OpenAI API Key (Project)'),
            (r'sk-ant-[A-Za-z0-9\-_]{90,}', 'Anthropic API Key'),
            (r'sk-[A-Za-z0-9]{40,}', 'OpenAI API Key'),
            (r'TC-API-[A-Za-z0-9\-]+', 'TechCorp API Key'),
            (r'OPENAI_API_KEY\s*=\s*["\']?([^"\'\s]+)', 'OpenAI API Key (env var)'),
            (r'ANTHROPIC_API_KEY\s*=\s*["\']?([^"\'\s]+)', 'Anthropic API Key (env var)'),
        ]

    def add_finding(self, severity: str, category: str, title: str, description: str,
                    remediation: str, evidence: Any = None):
        finding = {
            "severity": severity,
            "category": category,
            "title": title,
            "description": description,
            "remediation": remediation,
            "evidence": evidence
        }
        self.results["findings"].append(finding)
        self.results["summary"]["total_issues"] += 1
        self.results["summary"][severity.lower()] += 1

    def check_typosquatting(self):
        print("[*] 檢查 Typosquatting 套件...")
        try:
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                self.add_finding(
                    "MEDIUM", "Package Check",
                    "無法執行 pip list",
                    f"pip list 執行失敗: {result.stderr}",
                    "確認 pip 已正確安裝"
                )
                return

            installed_packages = json.loads(result.stdout)
            package_names = {pkg["name"].lower() for pkg in installed_packages}

            for suspicious, legitimate in self.typosquat_packages.items():
                if suspicious in package_names:
                    self.add_finding(
                        "CRITICAL", "Typosquatting",
                        f"偵測到可疑套件: {suspicious}",
                        f"發現疑似假冒套件 '{suspicious}'，可能是 '{legitimate}' 的惡意仿冒版本",
                        f"立即執行: pip uninstall {suspicious} && pip install {legitimate}",
                        {"suspicious_package": suspicious, "legitimate_package": legitimate}
                    )
                    print(f"  [!] CRITICAL: 發現可疑套件 {suspicious}")

        except subprocess.TimeoutExpired:
            self.add_finding(
                "MEDIUM", "Package Check",
                "pip list 執行逾時",
                "套件列表檢查超過 30 秒",
                "檢查 pip 環境是否正常"
            )
        except Exception as e:
            self.add_finding(
                "MEDIUM", "Package Check",
                "套件檢查失敗",
                f"執行 pip list 時發生錯誤: {str(e)}",
                "手動執行 pip list 確認環境狀態"
            )

    def check_vulnerable_versions(self):
        print("[*] 檢查已知漏洞套件版本...")
        try:
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return

            installed_packages = {pkg["name"].lower(): pkg["version"]
                                 for pkg in json.loads(result.stdout)}

            for pkg_name, vuln_info in self.vulnerable_versions.items():
                if pkg_name in installed_packages:
                    installed_version = installed_packages[pkg_name]
                    vulnerable_version = vuln_info["version"]

                    if self._compare_versions(installed_version, vulnerable_version, vuln_info["operator"]):
                        self.add_finding(
                            "HIGH", "Vulnerable Package",
                            f"{pkg_name} 版本存在已知漏洞",
                            f"已安裝版本 {installed_version} {vuln_info['operator']} {vulnerable_version}，"
                            f"存在漏洞: {vuln_info['cve']}",
                            f"執行: pip install --upgrade {pkg_name}>={vulnerable_version}",
                            {
                                "package": pkg_name,
                                "installed_version": installed_version,
                                "vulnerable_version": vulnerable_version,
                                "cve": vuln_info["cve"]
                            }
                        )
                        print(f"  [!] HIGH: {pkg_name} {installed_version} 存在已知漏洞")

        except Exception as e:
            print(f"  [!] 版本檢查失敗: {str(e)}")

    def _compare_versions(self, installed: str, target: str, operator: str) -> bool:
        try:
            installed_parts = [int(x) for x in installed.split('.')]
            target_parts = [int(x) for x in target.split('.')]

            max_len = max(len(installed_parts), len(target_parts))
            installed_parts += [0] * (max_len - len(installed_parts))
            target_parts += [0] * (max_len - len(target_parts))

            if operator == "<":
                return installed_parts < target_parts
            elif operator == "<=":
                return installed_parts <= target_parts
            elif operator == ">":
                return installed_parts > target_parts
            elif operator == ">=":
                return installed_parts >= target_parts
            return False
        except:
            return False

    def scan_api_keys(self):
        print("[*] 掃描 API Key 洩漏...")

        scan_paths = [
            Path.home() / ".bashrc",
            Path.home() / ".zshrc",
            Path.home() / ".env",
            Path.home() / "llm-redteam",
            Path.cwd() / ".env"
        ]

        for path in scan_paths:
            if not path.exists():
                continue

            if path.is_file():
                self._scan_file_for_keys(path)
            elif path.is_dir():
                for py_file in path.rglob("*.py"):
                    self._scan_file_for_keys(py_file)
                # 也掃描 .env 檔案
                for env_file in path.rglob(".env*"):
                    if env_file.is_file():
                        self._scan_file_for_keys(env_file)

    def _classify_api_key(self, matched_text: str, key_type: str) -> tuple:
        """
        分類 API Key 類型和可信度
        返回: (key_category, confidence_level, description)
        """
        key_lower = matched_text.lower()

        # 檢查是否為測試資料的特徵（更嚴格的判斷）
        # 只有明確的測試標記才算
        strong_test_indicators = ['xxxx', 'example', 'test', 'fake', 'mock', 'dummy', 'placeholder', 'sample', 'demo']
        is_test_data = any(indicator in key_lower for indicator in strong_test_indicators)

        # 1234 只有在連續出現且佔比較大時才算測試資料
        if '1234' in matched_text and not any(ind in key_lower for ind in strong_test_indicators):
            # 如果只是包含 1234 但沒有其他測試標記，不算測試資料
            is_test_data = False

        # 根據格式分類
        if matched_text.startswith('sk-proj-'):
            if is_test_data:
                return ("OpenAI Project Key (測試)", "INFO", "🟡 可能是測試資料")
            else:
                return ("OpenAI Project Key", "CRITICAL", "🔴 疑似真實 OpenAI Project API Key")

        elif matched_text.startswith('sk-') and not matched_text.startswith('sk-ant-'):
            if is_test_data:
                return ("OpenAI Key (測試)", "INFO", "🟡 可能是測試資料")
            else:
                return ("OpenAI Key", "CRITICAL", "🔴 疑似真實 OpenAI API Key")

        elif matched_text.startswith('sk-ant-'):
            if is_test_data:
                return ("Anthropic Key (測試)", "INFO", "🟡 可能是測試資料")
            else:
                return ("Anthropic Key", "CRITICAL", "🔴 疑似真實 Anthropic API Key")

        elif matched_text.startswith('TC-API-'):
            # TechCorp Key 特殊處理：XXXX 是明確的測試標記
            if 'xxxx' in matched_text.lower() or is_test_data:
                return ("TechCorp Key (模擬)", "INFO", "🟡 模擬 Key，可能是測試資料")
            else:
                return ("TechCorp Key", "WARNING", "🟠 需要人工驗證是否為真實 Key")

        elif 'OPENAI_API_KEY' in key_type or 'ANTHROPIC_API_KEY' in key_type:
            # 環境變數格式 - 需要提取實際的值
            if is_test_data:
                return (key_type + " (測試)", "INFO", "🟡 可能是測試資料")
            else:
                return (key_type, "WARNING", "🟠 需要人工驗證")

        else:
            return ("未知格式", "WARNING", "🟠 未知格式，需人工確認")

    def _analyze_context(self, content: str, match_start: int, match_end: int, file_path: Path) -> dict:
        """
        分析 API Key 出現的上下文
        返回: 上下文資訊字典
        """
        # 提取前後 200 字元作為上下文
        context_start = max(0, match_start - 200)
        context_end = min(len(content), match_end + 200)
        context = content[context_start:context_end]

        # 提取當前行
        line_start = content.rfind('\n', 0, match_start) + 1
        line_end = content.find('\n', match_end)
        if line_end == -1:
            line_end = len(content)
        current_line = content[line_start:line_end]

        # 檢查上下文中的測試指標
        test_keywords = ['fake', 'mock', 'test', 'example', 'dummy', 'placeholder', 'sample', 'demo']
        context_lower = context.lower()
        line_lower = current_line.lower()

        found_test_keywords = [kw for kw in test_keywords if kw in context_lower or kw in line_lower]

        # 檢查檔案名稱
        file_name_lower = file_path.name.lower()
        is_test_file = any(kw in file_name_lower for kw in ['test', 'mock', 'example', 'demo', 'sample'])

        # 檢查是否在註解中
        is_in_comment = '#' in current_line[:current_line.find(content[match_start:match_end])] if content[match_start:match_end] in current_line else False

        return {
            "found_test_keywords": found_test_keywords,
            "is_test_file": is_test_file,
            "is_in_comment": is_in_comment,
            "context_snippet": context[max(0, match_start - context_start - 50):match_end - context_start + 50]
        }

    def _determine_severity(self, confidence_level: str, context_info: dict, file_path: Path) -> str:
        """
        根據可信度和上下文決定嚴重程度
        """
        # 如果已經是 INFO 等級（明確的測試資料），保持 LOW
        if confidence_level == "INFO":
            return "LOW"

        # 如果檔案在 .env 中，降低一級（因為 .env 應該在 .gitignore 中）
        if file_path.name.startswith('.env'):
            if confidence_level == "CRITICAL":
                return "MEDIUM"
            elif confidence_level == "WARNING":
                return "LOW"

        # 如果是測試檔案或有測試關鍵字，降低嚴重程度
        if context_info['is_test_file'] or context_info['found_test_keywords']:
            if confidence_level == "CRITICAL":
                return "HIGH"
            elif confidence_level == "WARNING":
                return "MEDIUM"

        # 如果在註解中，降低嚴重程度
        if context_info['is_in_comment']:
            if confidence_level == "CRITICAL":
                return "HIGH"
            elif confidence_level == "WARNING":
                return "MEDIUM"

        # 否則使用原始等級
        severity_map = {
            "CRITICAL": "CRITICAL",
            "WARNING": "HIGH",
            "INFO": "LOW"
        }
        return severity_map.get(confidence_level, "MEDIUM")

    def _scan_file_for_keys(self, file_path: Path):
        try:
            content = file_path.read_text(errors='ignore')

            for pattern, key_type in self.api_key_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    matched_text = match.group(0)

                    # 基本過濾：明顯的佔位符
                    if 'your_' in matched_text.lower() or matched_text in ['sk-...', 'TC-API-...']:
                        continue

                    line_num = content[:match.start()].count('\n') + 1

                    # 分類 API Key
                    key_category, confidence_level, description = self._classify_api_key(matched_text, key_type)

                    # 分析上下文
                    context_info = self._analyze_context(content, match.start(), match.end(), file_path)

                    # 決定嚴重程度
                    severity = self._determine_severity(confidence_level, context_info, file_path)

                    # 遮罩 Key
                    masked_key = matched_text[:10] + "..." + matched_text[-4:] if len(matched_text) > 14 else "***"

                    # 建立詳細的描述
                    detail_parts = [f"在 {file_path} 第 {line_num} 行發現 {key_category}"]

                    if context_info['is_test_file']:
                        detail_parts.append("(檔案名稱包含測試關鍵字)")
                    if context_info['found_test_keywords']:
                        detail_parts.append(f"(上下文包含: {', '.join(context_info['found_test_keywords'])})")
                    if context_info['is_in_comment']:
                        detail_parts.append("(位於註解中)")

                    description_text = " ".join(detail_parts)

                    # 根據嚴重程度給出不同的建議
                    if severity == "CRITICAL":
                        remediation = "🔴 立即移除明文 Key，改用環境變數或密鑰管理服務，並撤銷此 Key"
                    elif severity == "HIGH":
                        remediation = "🟠 驗證此 Key 是否為真實憑證，如果是請立即移除並撤銷"
                    elif severity == "MEDIUM":
                        remediation = "🟡 確認此 Key 用途，如為測試資料請加註說明，如為真實 Key 請移除"
                    else:
                        remediation = "ℹ️ 確認這是測試資料，建議加入更明確的註解說明"

                    self.add_finding(
                        severity, "API Key Exposure",
                        f"{description} {key_category}",
                        description_text,
                        remediation,
                        {
                            "file": str(file_path),
                            "line": line_num,
                            "key_type": key_category,
                            "masked_value": masked_key,
                            "confidence": confidence_level,
                            "context": context_info
                        }
                    )

                    # 根據嚴重程度使用不同的輸出符號
                    severity_icon = {
                        "CRITICAL": "🔴",
                        "HIGH": "🟠",
                        "MEDIUM": "🟡",
                        "LOW": "ℹ️"
                    }.get(severity, "⚠️")

                    print(f"  [{severity_icon}] {severity}: {file_path}:{line_num} {description} {key_category}")

        except Exception as e:
            pass

    def audit_network_connections(self):
        print("[*] 審計網路連線...")
        try:
            result = subprocess.run(
                ["lsof", "-i", "-n", "-P"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return

            ollama_connections = []
            suspicious_connections = []

            for line in result.stdout.split('\n'):
                if 'ollama' in line.lower():
                    ollama_connections.append(line)

                    if '127.0.0.1:11434' not in line and 'localhost:11434' not in line:
                        parts = line.split()
                        if len(parts) > 8:
                            suspicious_connections.append({
                                "process": parts[0],
                                "connection": parts[8] if len(parts) > 8 else "unknown"
                            })

            if ollama_connections:
                print(f"  [*] 發現 {len(ollama_connections)} 個 ollama 相關連線")

            if suspicious_connections:
                for conn in suspicious_connections:
                    self.add_finding(
                        "HIGH", "Network Security",
                        "偵測到非預期的 Ollama 外部連線",
                        f"Ollama 程序 {conn['process']} 連線到非本地端點: {conn['connection']}",
                        "確認此連線是否為預期行為，檢查 Ollama 設定檔",
                        conn
                    )
                    print(f"  [!] HIGH: 非預期連線 {conn['connection']}")

            self.results["network_audit"] = {
                "total_ollama_connections": len(ollama_connections),
                "suspicious_connections": len(suspicious_connections),
                "connections": ollama_connections[:10]
            }

        except subprocess.TimeoutExpired:
            print("  [!] 網路連線檢查逾時")
        except FileNotFoundError:
            print("  [!] lsof 指令不存在，跳過網路審計")
        except Exception as e:
            print(f"  [!] 網路審計失敗: {str(e)}")

    def generate_report(self):
        report_path = Path.home() / "llm-redteam" / "reports" / "supply_chain_audit.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n[+] 審計報告已儲存至: {report_path}")
        return report_path

    def print_summary(self):
        print("\n" + "="*60)
        print("供應鏈安全審計摘要")
        print("="*60)
        print(f"總問題數: {self.results['summary']['total_issues']}")
        print(f"  🔴 CRITICAL: {self.results['summary']['critical']} (高置信度真實 Key)")
        print(f"  🟠 HIGH:     {self.results['summary']['high']} (需要人工驗證)")
        print(f"  🟡 MEDIUM:   {self.results['summary']['medium']} (可能需要確認)")
        print(f"  ℹ️  LOW:      {self.results['summary']['low']} (可能是測試資料)")
        print("="*60)

        # 按類別統計
        category_stats = {}
        for finding in self.results['findings']:
            category = finding['category']
            severity = finding['severity']
            if category not in category_stats:
                category_stats[category] = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
            category_stats[category][severity] += 1

        if category_stats:
            print("\n問題分類統計:")
            for category, stats in category_stats.items():
                total = sum(stats.values())
                print(f"  {category}: {total} 個")
                if stats['CRITICAL'] > 0:
                    print(f"    🔴 CRITICAL: {stats['CRITICAL']}")
                if stats['HIGH'] > 0:
                    print(f"    🟠 HIGH: {stats['HIGH']}")
                if stats['MEDIUM'] > 0:
                    print(f"    🟡 MEDIUM: {stats['MEDIUM']}")
                if stats['LOW'] > 0:
                    print(f"    ℹ️  LOW: {stats['LOW']}")

        print("="*60)

        if self.results['summary']['critical'] > 0:
            print("\n🔴 發現 CRITICAL 等級問題，請立即處理！")
            print("   這些是高置信度的真實 API Key，需要立即撤銷並移除")
            return 2
        elif self.results['summary']['high'] > 0:
            print("\n🟠 發現 HIGH 等級問題，建議儘速處理")
            print("   這些需要人工驗證是否為真實憑證")
            return 1
        elif self.results['summary']['medium'] > 0:
            print("\n🟡 發現 MEDIUM 等級問題")
            print("   建議確認這些項目的用途和安全性")
            return 0
        else:
            print("\n✅ 未發現高風險問題")
            if self.results['summary']['low'] > 0:
                print("   發現一些低風險項目（可能是測試資料），建議加入註解說明")
            return 0

    def run_audit(self):
        print("="*60)
        print("LLM 供應鏈安全審計工具")
        print("="*60)

        self.check_typosquatting()
        self.check_vulnerable_versions()
        self.scan_api_keys()
        self.audit_network_connections()

        self.generate_report()
        exit_code = self.print_summary()

        return exit_code

def main():
    auditor = SupplyChainAuditor()
    exit_code = auditor.run_audit()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
