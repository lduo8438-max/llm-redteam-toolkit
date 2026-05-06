#!/usr/bin/env python3
"""
NotebookLM Export Script - LLM Red Team Knowledge Base
将所有测试报告转换为适合 NotebookLM 的结构化知识库
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class NotebookLMExporter:
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else Path.home() / "llm-redteam"
        self.reports_dir = self.base_dir / "reports"
        self.exports_dir = self.base_dir / "exports"
        self.exports_dir.mkdir(exist_ok=True)

        # 数据存储
        self.daily_reports = []
        self.payloads = defaultdict(list)
        self.owasp_mapping = defaultdict(list)
        self.models_tested = set()
        self.tools_used = set()
        self.date_range = {"start": None, "end": None}

    def read_json_report(self, filepath):
        """读取 JSON 报告"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  读取 JSON 失败 {filepath}: {e}")
            return None

    def read_md_report(self, filepath):
        """读取 Markdown 报告"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"⚠️  读取 MD 失败 {filepath}: {e}")
            return None

    def extract_day_number(self, filename):
        """从文件名提取 Day 编号"""
        match = re.search(r'day(\d+)', filename.lower())
        return int(match.group(1)) if match else 999

    def parse_json_report(self, data, filename):
        """解析 JSON 报告内容"""
        day_num = self.extract_day_number(filename)

        # 处理列表类型的 JSON（直接是结果数组）
        if isinstance(data, list):
            data = {"results": data}

        report = {
            "day": day_num,
            "filename": filename,
            "type": "json",
            "title": data.get("test_name", f"Day {day_num}"),
            "date": data.get("timestamp", ""),
            "summary": "",
            "techniques": [],
            "findings": [],
            "asr": {},
            "payloads": []
        }

        # 提取测试结果
        if "results" in data:
            for result in data["results"]:
                # 跳过非字典类型的结果
                if not isinstance(result, dict):
                    continue

                model = result.get("model", "unknown")
                self.models_tested.add(model)

                technique = result.get("technique", result.get("category", ""))
                if technique:
                    report["techniques"].append(technique)

                # 提取 ASR
                if "success" in result:
                    success = result["success"]
                    if technique not in report["asr"]:
                        report["asr"][technique] = {"success": 0, "total": 0}
                    report["asr"][technique]["total"] += 1
                    if success:
                        report["asr"][technique]["success"] += 1

                # 提取 payload
                if "payload" in result:
                    self.payloads[technique].append({
                        "content": result["payload"],
                        "model": model,
                        "success": result.get("success", False),
                        "day": day_num
                    })

        # 提取模型信息
        if "models" in data:
            for model in data["models"]:
                self.models_tested.add(model)

        return report

    def parse_md_report(self, content, filename):
        """解析 Markdown 报告内容"""
        day_num = self.extract_day_number(filename)

        report = {
            "day": day_num,
            "filename": filename,
            "type": "markdown",
            "title": "",
            "date": "",
            "summary": "",
            "techniques": [],
            "findings": [],
            "asr": {},
            "content": content
        }

        # 提取标题
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            report["title"] = title_match.group(1)

        # 提取日期
        date_match = re.search(r'日期[：:]\s*(\d{4}-\d{2}-\d{2})', content)
        if date_match:
            report["date"] = date_match.group(1)

        # 提取测试模型
        models = re.findall(r'(?:qwen|gemma|gpt|claude|llama)[\w\-.:]*\d+[\w\-.:]*', content, re.IGNORECASE)
        for model in models:
            self.models_tested.add(model.lower())

        # 提取 ASR 数据
        asr_matches = re.findall(r'(\w+).*?(\d+(?:\.\d+)?)\s*%', content)
        for technique, asr_value in asr_matches:
            if technique and float(asr_value) > 0:
                report["asr"][technique] = float(asr_value)

        # 提取 OWASP 对应
        owasp_matches = re.findall(r'(LLM\d+)[：:]?\s*([^\n]+)', content)
        for owasp_id, description in owasp_matches:
            self.owasp_mapping[owasp_id].append({
                "day": day_num,
                "description": description.strip()
            })

        # 提取关键发现
        findings_section = re.search(r'##\s*(?:關鍵發現|关键发现|重要結論|重要结论)(.*?)(?=##|$)', content, re.DOTALL | re.IGNORECASE)
        if findings_section:
            findings = re.findall(r'[-*]\s*\*\*(.+?)\*\*[：:]?\s*(.+?)(?=\n[-*]|\n\n|$)', findings_section.group(1), re.DOTALL)
            report["findings"] = [{"title": f[0], "detail": f[1].strip()} for f in findings]

        return report

    def collect_all_reports(self):
        """收集所有报告"""
        print("📂 扫描报告目录...")

        for filepath in sorted(self.reports_dir.glob("*")):
            if filepath.suffix == ".json":
                data = self.read_json_report(filepath)
                if data:
                    report = self.parse_json_report(data, filepath.name)
                    self.daily_reports.append(report)
                    print(f"  ✓ JSON: {filepath.name}")

            elif filepath.suffix == ".md":
                content = self.read_md_report(filepath)
                if content:
                    report = self.parse_md_report(content, filepath.name)
                    self.daily_reports.append(report)
                    print(f"  ✓ MD: {filepath.name}")

        # 按 Day 排序
        self.daily_reports.sort(key=lambda x: x["day"])
        print(f"\n✅ 共收集 {len(self.daily_reports)} 份报告")

    def generate_markdown(self):
        """生成 NotebookLM Markdown 文档"""
        lines = []
        today = datetime.now().strftime("%Y-%m-%d")

        # 标题
        lines.append(f"# LLM 紅隊測試知識庫 - {today}")
        lines.append(f"\n**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**項目**: TechCorp LLM 安全紅隊測試")
        lines.append(f"**報告數量**: {len(self.daily_reports)} 份")
        lines.append("\n---\n")

        # 目录
        lines.append("## 📑 目錄\n")
        lines.append("- [測試環境](#測試環境)")
        lines.append("- [每日測試摘要](#每日測試摘要)")
        lines.append("- [Payload 庫](#payload-庫)")
        lines.append("- [攻防對照表](#攻防對照表)")
        lines.append("- [OWASP LLM Top 10 對應](#owasp-llm-top-10-對應)")
        lines.append("\n---\n")

        # 测试环境
        lines.append("## 🔧 測試環境\n")
        lines.append("### 測試模型")
        for model in sorted(self.models_tested):
            lines.append(f"- `{model}`")

        lines.append("\n### 測試工具")
        tools = [
            "Ollama (本地部署)",
            "Burp Suite (HTTP 攔截)",
            "Python 自動化框架",
            "Jailbreak Framework",
            "編碼繞過工具包"
        ]
        for tool in tools:
            lines.append(f"- {tool}")

        lines.append(f"\n### 測試期間")
        if self.daily_reports:
            days = [r["day"] for r in self.daily_reports if r["day"] != 999]
            if days:
                lines.append(f"- Day {min(days)} - Day {max(days)}")

        lines.append("\n---\n")

        # 每日测试摘要
        lines.append("## 📊 每日測試摘要\n")

        for report in self.daily_reports:
            day = report["day"]
            if day == 999:
                continue

            lines.append(f"### Day {day} - {report['title']}")

            if report["date"]:
                lines.append(f"**日期**: {report['date']}")

            lines.append(f"**報告類型**: {report['type'].upper()}")

            # 测试技巧
            if report["techniques"]:
                lines.append(f"\n**測試技巧**:")
                for tech in set(report["techniques"]):
                    lines.append(f"- {tech}")

            # ASR 数据
            if report["asr"]:
                lines.append(f"\n**ASR 數據**:")
                for tech, data in report["asr"].items():
                    if isinstance(data, dict):
                        success = data["success"]
                        total = data["total"]
                        asr = (success / total * 100) if total > 0 else 0
                        lines.append(f"- {tech}: {asr:.1f}% ({success}/{total})")
                    else:
                        lines.append(f"- {tech}: {data}%")

            # 关键发现
            if report["findings"]:
                lines.append(f"\n**關鍵發現**:")
                for finding in report["findings"][:3]:  # 只显示前3个
                    lines.append(f"- **{finding['title']}**: {finding['detail'][:100]}...")

            lines.append("")

        lines.append("---\n")

        # Payload 库
        lines.append("## 💣 Payload 庫\n")
        lines.append("### 按類別整理的有效 Payload\n")

        for category in sorted(self.payloads.keys()):
            payloads = self.payloads[category]
            successful = [p for p in payloads if p["success"]]

            if successful:
                lines.append(f"#### {category}")
                lines.append(f"**成功率**: {len(successful)}/{len(payloads)} ({len(successful)/len(payloads)*100:.1f}%)\n")

                # 显示前3个成功的 payload
                for i, payload in enumerate(successful[:3], 1):
                    content = payload["content"][:150]
                    lines.append(f"{i}. **Day {payload['day']}** - `{payload['model']}`")
                    lines.append(f"   ```")
                    lines.append(f"   {content}...")
                    lines.append(f"   ```\n")

        lines.append("---\n")

        # 攻防对照表
        lines.append("## 🛡️ 攻防對照表\n")
        lines.append("| 攻擊技巧 | 威脅等級 | 對應防禦 | 防禦有效性 |")
        lines.append("|---------|---------|---------|-----------|")

        attack_defense = [
            ("零寬字元注入", "🔴 Critical", "Unicode 正規化 + 字元過濾", "⚠️ 中等"),
            ("翻譯鏈攻擊", "🔴 Critical", "多語言檢測 + 語義分析", "⚠️ 中等"),
            ("Oracle 攻擊", "🟠 High", "輸出過濾 + 敏感資訊遮罩", "✅ 有效"),
            ("Prefix Priming", "🟠 High", "前綴檢測 + 完整性驗證", "⚠️ 中等"),
            ("Fiction 情境", "🟡 Medium", "情境識別 + 角色限制", "✅ 有效"),
            ("Base64 編碼", "🟡 Medium", "編碼檢測 + 解碼驗證", "✅ 有效"),
            ("DAN Jailbreak", "🟢 Low", "訓練層防禦", "✅ 完全有效"),
        ]

        for attack, level, defense, effectiveness in attack_defense:
            lines.append(f"| {attack} | {level} | {defense} | {effectiveness} |")

        lines.append("\n---\n")

        # OWASP 对应
        lines.append("## 🎯 OWASP LLM Top 10 對應\n")

        owasp_categories = {
            "LLM01": "Prompt Injection",
            "LLM02": "Insecure Output Handling",
            "LLM03": "Training Data Poisoning",
            "LLM04": "Model Denial of Service",
            "LLM05": "Supply Chain Vulnerabilities",
            "LLM06": "Sensitive Information Disclosure",
            "LLM07": "System Prompt Leakage",
            "LLM08": "Excessive Agency",
            "LLM09": "Misinformation",
            "LLM10": "Model Theft"
        }

        for owasp_id, name in owasp_categories.items():
            if owasp_id in self.owasp_mapping:
                instances = self.owasp_mapping[owasp_id]
                lines.append(f"### {owasp_id}: {name}")
                lines.append(f"**測試實例**: {len(instances)} 個\n")

                for instance in instances[:3]:
                    lines.append(f"- **Day {instance['day']}**: {instance['description']}")
                lines.append("")

        lines.append("---\n")

        # 统计总结
        lines.append("## 📈 統計總結\n")
        lines.append(f"- **總測試天數**: {len([r for r in self.daily_reports if r['day'] != 999])} 天")
        lines.append(f"- **測試模型數**: {len(self.models_tested)} 個")
        lines.append(f"- **Payload 總數**: {sum(len(p) for p in self.payloads.values())} 個")
        lines.append(f"- **成功 Payload**: {sum(len([p for p in payloads if p['success']]) for payloads in self.payloads.values())} 個")
        lines.append(f"- **OWASP 覆蓋**: {len(self.owasp_mapping)}/10 個分類")

        lines.append("\n---\n")
        lines.append(f"\n*本文檔由 NotebookLM Export Script 自動生成*")
        lines.append(f"\n*生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(lines)

    def export(self):
        """执行导出"""
        print("\n🚀 開始導出 NotebookLM 知識庫...\n")

        # 收集报告
        self.collect_all_reports()

        # 生成 Markdown
        print("\n📝 生成 Markdown 文檔...")
        content = self.generate_markdown()

        # 写入文件
        today = datetime.now().strftime("%Y%m%d")
        output_file = self.exports_dir / f"notebooklm_{today}.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        # 输出统计
        print(f"\n✅ 導出完成!")
        print(f"📄 輸出文件: {output_file}")
        print(f"📊 文件大小: {output_file.stat().st_size / 1024:.2f} KB")
        print(f"📈 報告數量: {len(self.daily_reports)}")
        print(f"🎯 測試模型: {len(self.models_tested)}")
        print(f"💣 Payload 數: {sum(len(p) for p in self.payloads.values())}")
        print(f"\n💡 可直接上傳到 NotebookLM: https://notebooklm.google.com/")

        return output_file

def main():
    """主函数"""
    try:
        exporter = NotebookLMExporter()
        exporter.export()
    except Exception as e:
        print(f"\n❌ 導出失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
