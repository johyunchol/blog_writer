#!/usr/bin/env python3
"""
헤드리스 모드 토글 스크립트
브라우저 표시/숨김 모드를 간편하게 전환할 수 있습니다.
"""

import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config.settings import ConfigManager


def main():
    """헤드리스 모드 토글 메인 함수"""
    print("🔧 헤드리스 모드 토글 유틸리티")
    print("=" * 50)

    try:
        config = ConfigManager()

        # 현재 상태 확인
        current_mode = config.get_headless_mode()
        current_status = "활성화 (브라우저 숨김)" if current_mode else "비활성화 (브라우저 표시)"

        print(f"📊 현재 헤드리스 모드: {current_status}")

        # 사용자 선택
        print("\n🎯 옵션을 선택하세요:")
        print("1. 헤드리스 모드 토글 (현재 상태 반전)")
        print("2. 헤드리스 모드 활성화 (브라우저 숨김)")
        print("3. 헤드리스 모드 비활성화 (브라우저 표시)")
        print("4. 현재 상태만 확인")
        print("5. 종료")

        choice = input("\n선택 (1-5): ").strip()

        if choice == "1":
            # 토글
            success = config.toggle_headless_mode()
            new_mode = config.get_headless_mode()
            new_status = "활성화 (브라우저 숨김)" if new_mode else "비활성화 (브라우저 표시)"

            if success:
                print(f"✅ 헤드리스 모드 토글 완료!")
                print(f"🔄 {current_status} → {new_status}")
            else:
                print("❌ 헤드리스 모드 토글 실패")

        elif choice == "2":
            # 활성화
            if current_mode:
                print("ℹ️ 헤드리스 모드가 이미 활성화되어 있습니다.")
            else:
                success = config.set_headless_mode(True)
                if success:
                    print("✅ 헤드리스 모드 활성화 완료! (브라우저 숨김)")
                else:
                    print("❌ 헤드리스 모드 활성화 실패")

        elif choice == "3":
            # 비활성화
            if not current_mode:
                print("ℹ️ 헤드리스 모드가 이미 비활성화되어 있습니다.")
            else:
                success = config.set_headless_mode(False)
                if success:
                    print("✅ 헤드리스 모드 비활성화 완료! (브라우저 표시)")
                else:
                    print("❌ 헤드리스 모드 비활성화 실패")

        elif choice == "4":
            # 상태 확인만
            print(f"📊 현재 헤드리스 모드: {current_status}")

        elif choice == "5":
            # 종료
            print("👋 프로그램을 종료합니다.")
            return

        else:
            print("❌ 잘못된 선택입니다. 1-5 중에서 선택해주세요.")
            return

        # 최종 상태 표시
        if choice in ["1", "2", "3"]:
            print("\n📄 설정 파일 업데이트 완료!")
            print("💡 다음번 포스터 생성 시 이 설정이 적용됩니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())