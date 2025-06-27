#!/usr/bin/env python3
"""
啟動服務器並顯示多IP用戶獨立性信息
"""

import os
import sys
from app import app

def print_banner():
    """打印啟動橫幅"""
    print("=" * 60)
    print("🚀 TSD AI 助手 - 多IP用戶獨立性版本")
    print("=" * 60)
    print("✨ 新功能:")
    print("   • 每個IP用戶都有獨立的agent執行環境")
    print("   • 支持多IP並發使用，互不影響")
    print("   • 保持原有的lock機制和頁面刷新停止功能")
    print("=" * 60)
    print("🌐 服務器將在 http://0.0.0.0:5000 啟動")
    print("📝 測試多IP功能: python test_multi_ip.py")
    print("=" * 60)

def check_dependencies():
    """檢查依賴項"""
    required_modules = [
        'flask', 'ollama', 'autogen', 'langchain', 
        'pandas', 'docx', 'numpy', 'sklearn', 'opencc'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("❌ 缺少以下依賴項:")
        for module in missing_modules:
            print(f"   - {module}")
        print("\n請安裝缺少的依賴項:")
        print("pip install flask ollama autogen langchain pandas python-docx numpy scikit-learn opencc-python-reimplemented")
        return False
    
    print("✅ 所有依賴項檢查通過")
    return True

def main():
    """主函數"""
    print_banner()
    
    # 檢查依賴項
    if not check_dependencies():
        sys.exit(1)
    
    # 檢查必要的目錄和文件
    if not os.path.exists('templates'):
        print("❌ 缺少 templates 目錄")
        sys.exit(1)
    
    if not os.path.exists('static'):
        print("❌ 缺少 static 目錄")
        sys.exit(1)
    
    print("✅ 環境檢查完成")
    print("\n🚀 啟動服務器...")
    
    try:
        # 啟動Flask應用
        app.run(
            host='0.0.0.0', 
            port=5000, 
            debug=True,
            use_reloader=False  # 避免重複啟動
        )
    except KeyboardInterrupt:
        print("\n👋 服務器已停止")
    except Exception as e:
        print(f"❌ 啟動服務器時發生錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 