"""
비밀번호 인코딩/디코딩 유틸리티
로컬 저장용 간단한 base64 인코딩 시스템
"""

import os
import base64
import json
from typing import Optional


class PasswordEncryption:
    """비밀번호 base64 인코딩/디코딩 클래스"""

    def __init__(self, config_dir: str = "./config"):
        """
        Args:
            config_dir: 설정 디렉토리 경로
        """
        self.config_dir = config_dir
        self.passwords_file = os.path.join(config_dir, '.passwords.json')

        # 설정 디렉토리가 없으면 생성
        os.makedirs(config_dir, exist_ok=True)

    def _encode_password(self, password: str) -> str:
        """비밀번호를 base64로 인코딩"""
        try:
            # UTF-8로 인코딩 후 base64로 변환
            encoded_bytes = base64.b64encode(password.encode('utf-8'))
            return encoded_bytes.decode('utf-8')
        except Exception:
            return password  # 인코딩 실패시 원본 반환

    def _decode_password(self, encoded_password: str) -> str:
        """base64로 인코딩된 비밀번호를 디코딩"""
        try:
            # base64 디코딩 후 UTF-8로 변환
            decoded_bytes = base64.b64decode(encoded_password.encode('utf-8'))
            return decoded_bytes.decode('utf-8')
        except Exception:
            return encoded_password  # 디코딩 실패시 원본 반환

    def _load_passwords(self) -> dict:
        """저장된 비밀번호 파일 로드"""
        try:
            if os.path.exists(self.passwords_file):
                with open(self.passwords_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _save_passwords(self, passwords: dict) -> bool:
        """비밀번호 파일에 저장"""
        try:
            with open(self.passwords_file, 'w', encoding='utf-8') as f:
                json.dump(passwords, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def save_password(self, key: str, password: str) -> bool:
        """
        비밀번호를 인코딩하여 저장

        Args:
            key: 비밀번호 키 (예: 'NAVER_PW', 'TISTORY_PW')
            password: 저장할 비밀번호

        Returns:
            저장 성공 여부
        """
        try:
            passwords = self._load_passwords()
            encoded_password = self._encode_password(password)
            passwords[key] = encoded_password
            return self._save_passwords(passwords)
        except Exception:
            return False

    def get_password(self, key: str) -> Optional[str]:
        """
        저장된 비밀번호를 디코딩하여 반환

        Args:
            key: 비밀번호 키 (예: 'NAVER_PW', 'TISTORY_PW')

        Returns:
            디코딩된 비밀번호 또는 None
        """
        try:
            passwords = self._load_passwords()
            if key in passwords:
                encoded_password = passwords[key]
                return self._decode_password(encoded_password)
            return None
        except Exception:
            return None

    def delete_password(self, key: str) -> bool:
        """
        저장된 비밀번호 삭제

        Args:
            key: 삭제할 비밀번호 키

        Returns:
            삭제 성공 여부
        """
        try:
            passwords = self._load_passwords()
            if key in passwords:
                del passwords[key]
                return self._save_passwords(passwords)
            return True  # 이미 없으면 성공으로 처리
        except Exception:
            return False

    def list_stored_keys(self) -> list:
        """저장된 비밀번호 키 목록 반환"""
        try:
            passwords = self._load_passwords()
            return list(passwords.keys())
        except Exception:
            return []

    def clear_all_passwords(self) -> bool:
        """모든 저장된 비밀번호 삭제"""
        try:
            return self._save_passwords({})
        except Exception:
            return False