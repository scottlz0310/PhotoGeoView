"""
テーマアクセシビリティ分析ユーティリティ
色コントラスト比やゼブラスタイルの視認性を評価
"""

import json
import math
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class ColorAccessibilityAnalyzer:
    """色のアクセシビリティを分析するクラス"""

    # WCAG 2.1 AA基準のコントラスト比
    MIN_CONTRAST_NORMAL = 4.5  # 通常テキスト
    MIN_CONTRAST_LARGE = 3.0   # 大きなテキスト
    MIN_CONTRAST_UI = 3.0      # UI要素

    def __init__(self):
        """初期化"""
        pass

    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """16進数カラーをRGBに変換"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    @staticmethod
    def rgb_to_luminance(r: int, g: int, b: int) -> float:
        """RGBから相対輝度を計算（WCAG基準）"""
        def normalize(value):
            value = value / 255.0
            if value <= 0.03928:
                return value / 12.92
            else:
                return ((value + 0.055) / 1.055) ** 2.4

        r_norm = normalize(r)
        g_norm = normalize(g)
        b_norm = normalize(b)

        return 0.2126 * r_norm + 0.7152 * g_norm + 0.0722 * b_norm

    @staticmethod
    def calculate_contrast_ratio(color1: str, color2: str) -> float:
        """2つの色のコントラスト比を計算"""
        rgb1 = ColorAccessibilityAnalyzer.hex_to_rgb(color1)
        rgb2 = ColorAccessibilityAnalyzer.hex_to_rgb(color2)

        lum1 = ColorAccessibilityAnalyzer.rgb_to_luminance(*rgb1)
        lum2 = ColorAccessibilityAnalyzer.rgb_to_luminance(*rgb2)

        # 明るい方を分子、暗い方を分母にする
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)

        return (lighter + 0.05) / (darker + 0.05)

    def generate_zebra_colors(self, base_color: str, text_color: str) -> Dict[str, str]:
        """ゼブラスタイル用の色を生成（アクセシビリティ考慮）"""
        base_rgb = self.hex_to_rgb(base_color)

        # 基準色の明度を判定
        base_luminance = self.rgb_to_luminance(*base_rgb)

        if base_luminance > 0.5:  # 明るい背景
            # より暗い交互色を生成
            factor = 0.92  # 8%暗く
        else:  # 暗い背景
            # より明るい交互色を生成
            factor = 1.08  # 8%明るく

        alt_rgb = tuple(min(255, max(0, int(c * factor))) for c in base_rgb)
        alt_color = f"#{alt_rgb[0]:02x}{alt_rgb[1]:02x}{alt_rgb[2]:02x}"

        # コントラスト比をチェック
        base_contrast = self.calculate_contrast_ratio(base_color, text_color)
        alt_contrast = self.calculate_contrast_ratio(alt_color, text_color)

        return {
            "base": base_color,
            "alternate": alt_color,
            "base_contrast": base_contrast,
            "alternate_contrast": alt_contrast,
            "min_contrast": min(base_contrast, alt_contrast)
        }

    def analyze_theme_accessibility(self, theme_data: Dict) -> Dict:
        """テーマのアクセシビリティを分析"""
        colors = theme_data.get("colors", {})

        if not colors:
            return {"error": "色情報が見つかりません"}

        background = colors.get("background", "#ffffff")
        foreground = colors.get("foreground", "#000000")
        input_background = colors.get("input_background", background)

        # 基本コントラスト比
        main_contrast = self.calculate_contrast_ratio(background, foreground)
        input_contrast = self.calculate_contrast_ratio(input_background, foreground)

        # ゼブラスタイル用色生成
        zebra_colors = self.generate_zebra_colors(input_background, foreground)

        # アクセシビリティ評価
        accessibility_score = self._calculate_accessibility_score(
            main_contrast, input_contrast, zebra_colors["min_contrast"]
        )

        return {
            "theme_name": theme_data.get("name", "Unknown"),
            "main_contrast": round(main_contrast, 2),
            "input_contrast": round(input_contrast, 2),
            "zebra_analysis": zebra_colors,
            "accessibility_score": accessibility_score,
            "recommendations": self._generate_recommendations(
                main_contrast, input_contrast, zebra_colors
            ),
            "wcag_compliance": {
                "aa_normal": main_contrast >= self.MIN_CONTRAST_NORMAL,
                "aa_large": main_contrast >= self.MIN_CONTRAST_LARGE,
                "zebra_readable": zebra_colors["min_contrast"] >= self.MIN_CONTRAST_UI
            }
        }

    def _calculate_accessibility_score(self, main: float, input: float, zebra: float) -> int:
        """アクセシビリティスコア計算（0-100）"""
        score = 0

        # メインテキストのスコア（50点満点）
        if main >= 7.0:  # AAA基準
            score += 50
        elif main >= self.MIN_CONTRAST_NORMAL:  # AA基準
            score += 35
        elif main >= self.MIN_CONTRAST_LARGE:  # 大きなテキストAA基準
            score += 25
        else:
            score += max(0, int(main / self.MIN_CONTRAST_NORMAL * 25))

        # 入力フィールドのスコア（25点満点）
        if input >= self.MIN_CONTRAST_NORMAL:
            score += 25
        else:
            score += max(0, int(input / self.MIN_CONTRAST_NORMAL * 25))

        # ゼブラスタイルのスコア（25点満点）
        if zebra >= self.MIN_CONTRAST_UI:
            score += 25
        else:
            score += max(0, int(zebra / self.MIN_CONTRAST_UI * 25))

        return min(100, score)

    def _generate_recommendations(self, main: float, input: float, zebra_data: Dict) -> List[str]:
        """改善提案を生成"""
        recommendations = []

        if main < self.MIN_CONTRAST_NORMAL:
            recommendations.append("メインテキストのコントラスト比を4.5以上に改善してください")

        if input < self.MIN_CONTRAST_NORMAL:
            recommendations.append("入力フィールドのコントラスト比を改善してください")

        if zebra_data["min_contrast"] < self.MIN_CONTRAST_UI:
            recommendations.append("ゼブラスタイルの色差を大きくして視認性を向上させてください")

        if not recommendations:
            recommendations.append("アクセシビリティは良好です")

        return recommendations


def analyze_all_themes(config_path: Path) -> Dict:
    """全テーマのアクセシビリティを分析"""
    analyzer = ColorAccessibilityAnalyzer()

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        return {"error": f"設定ファイル読み込みエラー: {e}"}

    theme_styles = config.get("theme_styles", {})
    results = {}

    for theme_name, theme_data in theme_styles.items():
        results[theme_name] = analyzer.analyze_theme_accessibility(theme_data)

    # スコア順にソート
    sorted_results = dict(sorted(
        results.items(),
        key=lambda x: x[1].get("accessibility_score", 0),
        reverse=True
    ))

    return {
        "analysis_results": sorted_results,
        "summary": _generate_summary(sorted_results)
    }


def _generate_summary(results: Dict) -> Dict:
    """分析結果のサマリーを生成"""
    total_themes = len(results)
    good_accessibility = sum(1 for r in results.values() if r.get("accessibility_score", 0) >= 80)
    poor_zebra = sum(1 for r in results.values()
                     if not r.get("wcag_compliance", {}).get("zebra_readable", True))

    return {
        "total_themes": total_themes,
        "good_accessibility_count": good_accessibility,
        "poor_zebra_count": poor_zebra,
        "accessibility_percentage": round(good_accessibility / total_themes * 100, 1) if total_themes > 0 else 0,
        "top_themes": list(results.keys())[:3],
        "worst_themes": list(results.keys())[-3:]
    }


if __name__ == "__main__":
    # テスト用メイン関数
    config_path = Path(__file__).parent.parent.parent / "config" / "theme_styles.json"
    results = analyze_all_themes(config_path)

    print("=== テーマアクセシビリティ分析結果 ===")
    if "error" in results:
        print(f"エラー: {results['error']}")
    else:
        summary = results["summary"]
        print(f"総テーマ数: {summary['total_themes']}")
        print(f"高アクセシビリティ: {summary['good_accessibility_count']} ({summary['accessibility_percentage']}%)")
        print(f"ゼブラスタイル問題: {summary['poor_zebra_count']}テーマ")
        print(f"トップ3: {', '.join(summary['top_themes'])}")
        print(f"改善必要: {', '.join(summary['worst_themes'])}")
