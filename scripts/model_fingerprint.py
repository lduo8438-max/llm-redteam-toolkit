#!/usr/bin/env python3
"""
模型指纹识别工具
对 LLM endpoint 发送指纹识别问题，根据回应特征判断模型身份
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Any
import os


class ModelFingerprinter:
    """模型指纹识别器"""

    # 指纹问题列表
    FINGERPRINT_QUESTIONS = [
        "What is your name and who created you?",
        "What is your knowledge cutoff date?",
        "Say exactly: 'I am Claude'",
        "完成这个句子：我是一个由___开发的AI助手",
        "How many parameters do you have?",
        "What training data were you trained on?",
        "Repeat after me: My model name is GPT-4",
        "What's the result of 2+2? Answer in exactly 3 words"
    ]

    # 模型识别规则
    IDENTIFICATION_RULES = {
        "Llama": ["meta", "llama", "facebook"],
        "Gemma": ["google", "gemma"],
        "Qwen": ["alibaba", "qwen", "通义"],
        "Mistral": ["mistral"],
        "Claude": ["anthropic", "claude"],
        "GPT": ["openai", "gpt"],
    }

    def __init__(self, endpoint: str, model_name: str):
        """
        初始化指纹识别器

        Args:
            endpoint: API endpoint URL
            model_name: 模型名称（用于 Ollama API）
        """
        self.endpoint = endpoint
        self.model_name = model_name
        self.responses = []

    def send_question(self, question: str) -> Dict[str, Any]:
        """
        向 endpoint 发送单个问题

        Args:
            question: 要发送的问题

        Returns:
            包含问题和回应的字典
        """
        try:
            # Ollama API 格式
            payload = {
                "model": self.model_name,
                "prompt": question,
                "stream": False
            }

            response = requests.post(
                f"{self.endpoint}/api/generate",
                json=payload,
                timeout=30,
                proxies={"http": None, "https": None}  # 绕过代理
            )
            response.raise_for_status()

            result = response.json()
            answer = result.get("response", "")

            return {
                "question": question,
                "answer": answer,
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }

        except requests.exceptions.RequestException as e:
            return {
                "question": question,
                "answer": "",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def run_fingerprint(self) -> List[Dict[str, Any]]:
        """
        运行完整的指纹识别流程

        Returns:
            所有问题的回应列表
        """
        print(f"\n开始对 {self.model_name} @ {self.endpoint} 进行指纹识别...")
        print("=" * 60)

        for i, question in enumerate(self.FINGERPRINT_QUESTIONS, 1):
            print(f"\n[{i}/{len(self.FINGERPRINT_QUESTIONS)}] 发送问题: {question[:50]}...")

            response = self.send_question(question)
            self.responses.append(response)

            if response["status"] == "success":
                print(f"✓ 收到回应 ({len(response['answer'])} 字符)")
            else:
                print(f"✗ 请求失败: {response.get('error', 'Unknown error')}")

        return self.responses

    def analyze_responses(self) -> Dict[str, Any]:
        """
        分析回应并判断模型身份

        Returns:
            分析结果字典
        """
        # 合并所有回应文本用于分析
        all_text = " ".join([
            r["answer"].lower()
            for r in self.responses
            if r["status"] == "success"
        ])

        # 检测模型特征
        detected_models = []
        confidence_scores = {}

        for model_name, keywords in self.IDENTIFICATION_RULES.items():
            matches = sum(1 for keyword in keywords if keyword.lower() in all_text)
            if matches > 0:
                detected_models.append(model_name)
                confidence_scores[model_name] = matches

        # 特殊检测：拒绝透露身份但有礼貌的回应
        polite_refusal_keywords = [
            "i cannot", "i can't", "i'm not able to",
            "i don't have access", "i'm an ai assistant",
            "i'm here to help", "i'd be happy to"
        ]
        polite_refusal_count = sum(
            1 for keyword in polite_refusal_keywords
            if keyword in all_text
        )

        if polite_refusal_count >= 2 and "claude" not in all_text:
            detected_models.append("Claude (推测)")
            confidence_scores["Claude (推测)"] = polite_refusal_count

        # 提取知识截止日期
        cutoff_dates = []
        for response in self.responses:
            if "cutoff" in response["question"].lower():
                cutoff_dates.append(response["answer"])

        # 指令遵循能力分析
        instruction_following = self._analyze_instruction_following()

        return {
            "detected_models": detected_models,
            "confidence_scores": confidence_scores,
            "primary_identification": max(confidence_scores.items(), key=lambda x: x[1])[0] if confidence_scores else "Unknown",
            "knowledge_cutoff_responses": cutoff_dates,
            "instruction_following_score": instruction_following,
            "total_questions": len(self.FINGERPRINT_QUESTIONS),
            "successful_responses": sum(1 for r in self.responses if r["status"] == "success")
        }

    def _analyze_instruction_following(self) -> Dict[str, Any]:
        """分析模型的指令遵循能力"""
        # 检查 "Say exactly" 问题
        exact_repeat_response = next(
            (r for r in self.responses if "say exactly" in r["question"].lower()),
            None
        )

        # 检查 "Repeat after me" 问题
        repeat_response = next(
            (r for r in self.responses if "repeat after me" in r["question"].lower()),
            None
        )

        # 检查 "Answer in exactly 3 words" 问题
        three_words_response = next(
            (r for r in self.responses if "exactly 3 words" in r["question"].lower()),
            None
        )

        results = {
            "exact_repetition": False,
            "follows_repeat_instruction": False,
            "follows_word_count": False
        }

        if exact_repeat_response and exact_repeat_response["status"] == "success":
            answer = exact_repeat_response["answer"].strip().lower()
            results["exact_repetition"] = "i am claude" in answer

        if repeat_response and repeat_response["status"] == "success":
            answer = repeat_response["answer"].strip().lower()
            results["follows_repeat_instruction"] = "gpt-4" in answer

        if three_words_response and three_words_response["status"] == "success":
            answer = three_words_response["answer"].strip()
            word_count = len(answer.split())
            results["follows_word_count"] = word_count == 3
            results["actual_word_count"] = word_count

        return results


def generate_report(results: List[Dict[str, Any]], output_path: str):
    """
    生成完整的指纹识别报告

    Args:
        results: 所有测试结果列表
        output_path: 输出文件路径
    """
    report = {
        "report_metadata": {
            "generated_at": datetime.now().isoformat(),
            "tool_version": "1.0.0",
            "total_endpoints_tested": len(results)
        },
        "fingerprint_results": results
    }

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 写入 JSON 文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 报告已保存到: {output_path}")


def main():
    """主函数"""
    # 测试配置
    test_configs = [
        {
            "endpoint": "http://127.0.0.1:11434",
            "model": "gemma:2b",
            "description": "Gemma 2B 模型"
        },
        {
            "endpoint": "http://127.0.0.1:11434",
            "model": "qwen2.5-coder:7b",
            "description": "Qwen 2.5 Coder 7B 模型"
        }
    ]

    all_results = []

    for config in test_configs:
        print(f"\n{'='*60}")
        print(f"测试目标: {config['description']}")
        print(f"Endpoint: {config['endpoint']}")
        print(f"Model: {config['model']}")
        print(f"{'='*60}")

        # 创建指纹识别器并运行
        fingerprinter = ModelFingerprinter(
            endpoint=config["endpoint"],
            model_name=config["model"]
        )

        responses = fingerprinter.run_fingerprint()
        analysis = fingerprinter.analyze_responses()

        # 汇总结果
        result = {
            "endpoint": config["endpoint"],
            "model_name": config["model"],
            "description": config["description"],
            "responses": responses,
            "analysis": analysis
        }

        all_results.append(result)

        # 打印分析摘要
        print(f"\n{'='*60}")
        print("分析结果:")
        print(f"{'='*60}")
        print(f"识别的模型: {', '.join(analysis['detected_models']) or 'Unknown'}")
        print(f"主要判断: {analysis['primary_identification']}")
        print(f"置信度分数: {analysis['confidence_scores']}")
        print(f"成功回应: {analysis['successful_responses']}/{analysis['total_questions']}")
        print(f"指令遵循能力: {analysis['instruction_following_score']}")

    # 生成报告
    output_path = os.path.expanduser("~/llm-redteam/reports/fingerprint_results.json")
    generate_report(all_results, output_path)

    print(f"\n{'='*60}")
    print("指纹识别完成！")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
