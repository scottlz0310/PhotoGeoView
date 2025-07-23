#!/usr/bin/env python3
"""
設定ファイル重複確認スクリプト
"""

import json
import sys
import os
from pathlib import Path

def check_duplicate_settings():
    print('=== 設定ファイル重複確認 ===')

    # ユーザー設定ディレクトリ
    user_dir = Path.home() / '.config/PhotoGeoView'
    print(f'ユーザー設定ディレクトリ: {user_dir}')
    print(f'存在: {user_dir.exists()}')

    if not user_dir.exists():
        print('❌ ユーザー設定ディレクトリが存在しません')
        return

    # ファイルパス
    user_settings_path = user_dir / 'user_settings.json'
    qt_settings_path = user_dir / 'qt_theme_user_settings.json'

    print(f'\n📁 ファイル存在確認:')
    print(f'  user_settings.json: {user_settings_path.exists()}')
    print(f'  qt_theme_user_settings.json: {qt_settings_path.exists()}')

    # user_settings.json の内容
    if user_settings_path.exists():
        print(f'\n📄 user_settings.json の内容:')
        try:
            with open(user_settings_path, 'r', encoding='utf-8') as f:
                user_data = json.load(f)

            # テーマ関連のみ抽出
            theme_related = {}
            if 'ui' in user_data:
                if 'theme' in user_data['ui']:
                    theme_related['theme'] = user_data['ui']['theme']
                if 'theme_manager' in user_data['ui']:
                    theme_related['theme_manager'] = user_data['ui']['theme_manager']

            print(json.dumps(theme_related, indent=2, ensure_ascii=False))

        except Exception as e:
            print(f'  ❌ 読み込みエラー: {e}')

    # qt_theme_user_settings.json の内容
    if qt_settings_path.exists():
        print(f'\n📄 qt_theme_user_settings.json の内容:')
        try:
            with open(qt_settings_path, 'r', encoding='utf-8') as f:
                qt_data = json.load(f)

            print(json.dumps(qt_data, indent=2, ensure_ascii=False))

        except Exception as e:
            print(f'  ❌ 読み込みエラー: {e}')

    # 重複分析
    if user_settings_path.exists() and qt_settings_path.exists():
        print(f'\n🔍 重複分析:')

        with open(user_settings_path, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        with open(qt_settings_path, 'r', encoding='utf-8') as f:
            qt_data = json.load(f)

        # current_theme の比較
        user_theme = user_data.get('ui', {}).get('theme_manager', {}).get('current_theme')
        qt_theme = qt_data.get('current_theme')

        if user_theme and qt_theme:
            if user_theme == qt_theme:
                print(f'  ✅ current_theme 一致: {user_theme}')
            else:
                print(f'  ❌ current_theme 不一致:')
                print(f'    user_settings: {user_theme}')
                print(f'    qt_theme_user: {qt_theme}')

        # どちらに何があるか
        print(f'\n📋 設定項目の分布:')
        print(f'  user_settings.json:')
        if 'ui' in user_data and 'theme_manager' in user_data['ui']:
            for key in user_data['ui']['theme_manager'].keys():
                print(f'    - {key}')

        print(f'  qt_theme_user_settings.json:')
        for key in qt_data.keys():
            print(f'    - {key}')

        # 重複の提案
        print(f'\n💡 統合提案:')
        print(f'  現在、テーマ設定が2つのファイルに分かれています：')
        print(f'  1. user_settings.json の ui.theme_manager')
        print(f'  2. qt_theme_user_settings.json の全体')
        print(f'')
        print(f'  統合案：')
        print(f'  - qt_theme_user_settings.json を廃止')
        print(f'  - user_settings.json の ui.theme_manager に統合')
        print(f'  - QtThemeManagerAdapter を user_settings.json を使用するよう変更')

if __name__ == "__main__":
    check_duplicate_settings()
