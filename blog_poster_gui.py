#!/usr/bin/env python3
"""
통합 블로그 포스팅 시스템 GUI 런처
GUI 버전의 메인 실행 스크립트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.gui.main_window import BlogPosterGUI

    def main():
        """메인 함수"""
        print("🚀 통합 블로그 포스팅 시스템 GUI 시작...")

        try:
            app = BlogPosterGUI()
            app.run()
        except Exception as e:
            print(f"❌ GUI 실행 실패: {e}")
            import traceback
            traceback.print_exc()
            return 1

        return 0

    if __name__ == "__main__":
        sys.exit(main())

except ImportError as e:
    print(f"❌ GUI 모듈 import 실패: {e}")
    print("tkinter가 설치되어 있는지 확인해주세요.")
    print("macOS: 기본 설치됨")
    print("Linux: sudo apt-get install python3-tk")
    print("Windows: 기본 설치됨 (Python 설치 시)")
    sys.exit(1)