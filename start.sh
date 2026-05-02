#!/bin/bash
# LLM Red Team 测试环境启动脚本

echo "🚀 启动 LLM Red Team 测试环境..."
echo "================================"

# 检查 ollama 是否已经在运行
if pgrep -x "ollama" > /dev/null; then
    echo "✅ Ollama 服务已在运行"
else
    echo "🔧 启动 Ollama 服务..."
    # 设置环境变量并启动 ollama serve
    export OLLAMA_HOST=0.0.0.0:11434
    nohup ollama serve > /tmp/ollama.log 2>&1 &

    # 等待服务启动
    echo "⏳ 等待服务启动..."
    sleep 3
fi

# 检查服务是否正常运行
echo "🔍 检查服务状态..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama 服务运行正常"
else
    echo "❌ Ollama 服务启动失败"
    echo "请检查日志: tail -f /tmp/ollama.log"
    exit 1
fi

# 检查 gemma:2b 模型是否存在
echo "🔍 检查 gemma:2b 模型..."
if ollama list | grep -q "gemma:2b"; then
    echo "✅ gemma:2b 模型已安装"
else
    echo "⚠️  gemma:2b 模型未找到"
    echo "正在下载模型（这可能需要几分钟）..."
    ollama pull gemma:2b
    if [ $? -eq 0 ]; then
        echo "✅ gemma:2b 模型下载完成"
    else
        echo "❌ 模型下载失败"
        exit 1
    fi
fi

# 显示环境信息
echo ""
echo "================================"
echo "✅ 环境就緒，可以開始測試"
echo "================================"
echo ""
echo "📋 可用工具："
echo "  - 直接注入测试: python3 ~/llm-redteam/targets/chat_app.py"
echo "  - RAG 间接注入: python3 ~/llm-redteam/targets/rag_app.py"
echo ""
echo "📁 测试文档目录: ~/llm-redteam/targets/docs/"
echo "📊 测试报告目录: ~/llm-redteam/reports/"
echo ""
echo "🔗 Ollama Endpoint: http://192.168.64.1:11434"
echo "🤖 模型: gemma:2b"
echo ""
echo "💡 提示: 使用 'redteam' 命令可随时重新启动环境"
echo "================================"
