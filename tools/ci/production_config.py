#!/usr/bin/env python3
"""
Production Configuration Manager for CI Simulator

This module provides production-ready configuration management with
optimizations for large codebases and production environments.

AI貢献者:
- Kiro: 本番対応設定シス
成者: Kiro AI統合システム
作成日: 2025年1月30日
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging
import multiprocessing
import psutil
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass
class PerformanceConfig:
    """パフォーマンス設定"""
    max_parallel_jobs: int = 4
    memory_limit_mb: int = 2048
    timeout_seconds: int = 3600
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    incremental_checks: bool = True
    file_change_detection: bool = True


@dataclass
class ProductionLoggingConfig:
    """本番ログ設定"""
    level: str = "INFO"
    file_rotation: bool = True
    max_file_size_mb: int = 100
    backup_count: int = 5
    structured_logging: bool = True
    performance_metrics: bool = True
    error_tracking: bool = True
    log_retention_days: int = 30


@dataclass
class ScalabilityConfig:
    """スケーラビリティ設定"""
    large_codebase_mode: bool = False
    file_count_threshold: int = 10000
    line_count_threshold: int = 1000000
    batch_processing: bool = True
    batch_size: int = 100
    distributed_execution: bool = False
    worker_nodes: List[str] = None


@dataclass
class MonitoringConfig:
    """監視設定"""
    metrics_enabled: bool = True
    health_checks: bool = True
    performance_tracking: bool = True
    resource_monitoring: bool = True
    alert_thresholds: Dict[str, float] = None
    notification_channels: List[str] = None


@dataclass
class ProductionConfig:
    """本番設定"""
    environment: str = "production"
    performance: PerformanceConfig = None
    logging: ProductionLoggingConfig = None
    scalability: ScalabilityConfig = None
    monitoring: MonitoringConfig = None

    def __post_init__(self):
        if self.performance is None:
            self.performance = PerformanceConfig()
        if self.logging is None:
            self.logging = ProductionLoggingConfig()
        if self.scalability is None:
            self.scalability = ScalabilityConfig()
        if self.monitoring is None:
            self.monitoring = MonitoringConfig()


class ProductionConfigManager:
    """本番設定管理器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config_dir = project_root / ".kiro" / "settings"
        self.config_file = self.config_dir / "production_config.json"
        self.logger = self._setup_logger()

        # System information
        self.cpu_count = multiprocessing.cpu_count()
        self.memory_gb = psutil.virtual_memory().total / (1024**3)
        self.disk_space_gb = psutil.disk_usage(str(project_root)).free / (1024**3)

    def _setup_logger(self) -> logging.Logger:
        """ロガーのセットアップ"""
        logger = logging.getLogger('production_config')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def detect_codebase_characteristics(self) -> Dict[str, Any]:
        """コードベース特性の検出"""
        self.logger.info("Detecting codebase characteristics...")

        characteristics = {
            "total_files": 0,
            "python_files": 0,
            "total_lines": 0,
            "test_files": 0,
            "large_files": 0,
            "binary_files": 0,
            "directories": 0
        }

        try:
            for root, dirs, files in os.walk(self.project_root):
                # Skip common ignore directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                    '__pycache__', 'node_modules', 'venv', 'build', 'dist'
                ]]

                characteristics["directories"] += len(dirs)

                for file in files:
                    file_path = Path(root) / file

                    # Skip hidden files and common ignore patterns
                    if file.startswith('.') or file.endswith(('.pyc', '.pyo')):
                        continue

                    characteristics["total_files"] += 1

                    try:
                        file_size = file_path.stat().st_size

                        # Check if it's a binary file
                        if self._is_binary_file(file_path):
                            characteristics["binary_files"] += 1
                            continue

                        # Count Python files
                        if file.endswith('.py'):
                            characteristics["python_files"] += 1

                            # Count test files
                            if 'test' in file.lower() or 'test' in str(file_path).lower():
                                characteristics["test_files"] += 1

                        # Count lines for text files
                        if file_size < 10 * 1024 * 1024:  # Skip files larger than 10MB
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    lines = sum(1 for _ in f)
                                    characteristics["total_lines"] += lines

                                    if lines > 1000:
                                        characteristics["large_files"] += 1
                            except (UnicodeDecodeError, PermissionError):
                                pass
                        else:
                            characteristics["large_files"] += 1

                    except (OSError, PermissionError):
                        pass

        except Exception as e:
            self.logger.warning(f"Error detecting codebase characteristics: {e}")

        self.logger.info(f"Codebase characteristics: {characteristics}")
        return characteristics

    def _is_binary_file(self, file_path: Path) -> bool:
        """バイナリファイルの判定"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except (OSError, PermissionError):
            return True

    def generate_optimized_config(self) -> ProductionConfig:
        """最適化された設定の生成"""
        self.logger.info("Generating optimized production configuration...")

        # Detect codebase characteristics
        characteristics = self.detect_codebase_characteristics()

        # Determine if this is a large codebase
        is_large_codebase = (
            characteristics["total_files"] > 10000 or
            characteristics["total_lines"] > 1000000 or
            characteristics["python_files"] > 1000
        )

        # Performance configuration
        performance_config = PerformanceConfig(
            max_parallel_jobs=min(self.cpu_count, 8 if is_large_codebase else 4),
            memory_limit_mb=min(int(self.memory_gb * 1024 * 0.7), 4096),
            timeout_seconds=7200 if is_large_codebase else 3600,
            cache_enabled=True,
            cache_ttl_hours=48 if is_large_codebase else 24,
            incremental_checks=is_large_codebase,
            file_change_detection=True
        )

        # Logging configuration
        logging_config = ProductionLoggingConfig(
            level="INFO",
            file_rotation=True,
            max_file_size_mb=200 if is_large_codebase else 100,
            backup_count=10 if is_large_codebase else 5,
            structured_logging=True,
            performance_metrics=True,
            error_tracking=True,
            log_retention_days=60 if is_large_codebase else 30
        )

        # Scalability configuration
        scalability_config = ScalabilityConfig(
            large_codebase_mode=is_large_codebase,
            file_count_threshold=10000,
            line_count_threshold=1000000,
            batch_processing=is_large_codebase,
            batch_size=200 if is_large_codebase else 100,
            distributed_execution=False,  # Can be enabled for very large codebases
            worker_nodes=[]
        )

        # Monitoring configuration
        monitoring_config = MonitoringConfig(
            metrics_enabled=True,
            health_checks=True,
            performance_tracking=True,
            resource_monitoring=True,
            alert_thresholds={
                "memory_usage_percent": 80.0,
                "cpu_usage_percent": 90.0,
                "disk_usage_percent": 85.0,
                "execution_time_minutes": 60.0 if is_large_codebase else 30.0
            },
            notification_channels=[]
        )

        config = ProductionConfig(
            environment="production",
            performance=performance_config,
            logging=logging_config,
            scalability=scalability_config,
            monitoring=monitoring_config
        )

        self.logger.info(f"Generated configuration for {'large' if is_large_codebase else 'standard'} codebase")
        return config

    def save_config(self, config: ProductionConfig) -> bool:
        """設定の保存"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)

            config_dict = asdict(config)
            config_dict["generated_at"] = datetime.now().isoformat()
            config_dict["system_info"] = {
                "cpu_count": self.cpu_count,
                "memory_gb": round(self.memory_gb, 2),
                "disk_space_gb": round(self.disk_space_gb, 2),
                "platform": sys.platform
            }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Production configuration saved to: {self.config_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False

    def load_config(self) -> Optional[ProductionConfig]:
        """設定の読み込み"""
        if not self.config_file.exists():
            return None

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)

            # Remove metadata fields
            config_dict.pop("generated_at", None)
            config_dict.pop("system_info", None)

            # Convert nested dictionaries to dataclasses
            if "performance" in config_dict:
                config_dict["performance"] = PerformanceConfig(**config_dict["performance"])
            if "logging" in config_dict:
                config_dict["logging"] = ProductionLoggingConfig(**config_dict["logging"])
            if "scalability" in config_dict:
                config_dict["scalability"] = ScalabilityConfig(**config_dict["scalability"])
            if "monitoring" in config_dict:
                config_dict["monitoring"] = MonitoringConfig(**config_dict["monitoring"])

            config = ProductionConfig(**config_dict)
            self.logger.info("Production configuration loaded successfully")
            return config

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return None

    def update_ci_simulator_config(self, production_config: ProductionConfig) -> bool:
        """CI Simulator設定の更新"""
        try:
            ci_config_file = self.config_dir / "ci_simulator.json"

            # Load existing CI config
            ci_config = {}
            if ci_config_file.exists():
                with open(ci_config_file, 'r', encoding='utf-8') as f:
                    ci_config = json.load(f)

            # Update with production optimizations
            ci_config.update({
                "timeout": production_config.performance.timeout_seconds,
                "parallel_jobs": production_config.performance.max_parallel_jobs,
                "cache_enabled": production_config.performance.cache_enabled,
                "incremental_checks": production_config.performance.incremental_checks,
                "large_codebase_mode": production_config.scalability.large_codebase_mode,
                "batch_processing": production_config.scalability.batch_processing,
                "batch_size": production_config.scalability.batch_size,
                "memory_limit_mb": production_config.performance.memory_limit_mb,
                "logging": {
                    "level": production_config.logging.level,
                    "structured": production_config.logging.structured_logging,
                    "performance_metrics": production_config.logging.performance_metrics,
                    "file_rotation": production_config.logging.file_rotation,
                    "max_file_size_mb": production_config.logging.max_file_size_mb
                },
                "monitoring": {
                    "enabled": production_config.monitoring.metrics_enabled,
                    "resource_monitoring": production_config.monitoring.resource_monitoring,
                    "alert_thresholds": production_config.monitoring.alert_thresholds
                }
            })

            # Save updated CI config
            with open(ci_config_file, 'w', encoding='utf-8') as f:
                json.dump(ci_config, f, indent=2, ensure_ascii=False)

            self.logger.info("CI Simulator configuration updated with production settings")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update CI Simulator configuration: {e}")
            return False

    def validate_production_readiness(self) -> Dict[str, Any]:
        """本番対応度の検証"""
        self.logger.info("Validating production readiness...")

        validation_results = {
            "overall_ready": True,
            "checks": {},
            "recommendations": [],
            "warnings": [],
            "errors": []
        }

        # Check system resources
        if self.memory_gb < 4:
            validation_results["warnings"].append(
                f"Low memory: {self.memory_gb:.1f}GB (recommended: 4GB+)"
            )

        if self.disk_space_gb < 10:
            validation_results["errors"].append(
                f"Low disk space: {self.disk_space_gb:.1f}GB (required: 10GB+)"
            )
            validation_results["overall_ready"] = False

        # Check CPU cores
        if self.cpu_count < 2:
            validation_results["warnings"].append(
                f"Low CPU cores: {self.cpu_count} (recommended: 2+)"
            )

        # Check configuration file
        config = self.load_config()
        if config is None:
            validation_results["errors"].append("Production configuration not found")
            validation_results["overall_ready"] = False
        else:
            validation_results["checks"]["configuration"] = "✅ Found"

        # Check required directories
        required_dirs = [
            self.project_root / "logs",
            self.project_root / "reports",
            self.project_root / ".kiro" / "ci-history"
        ]

        for dir_path in required_dirs:
            if not dir_path.exists():
                validation_results["warnings"].append(f"Missing directory: {dir_path}")
            else:
                validation_results["checks"][f"directory_{dir_path.name}"] = "✅ Exists"

        # Check CI Simulator availability
        try:
            # Try different import paths
            try:
                from tools.ci.simulator import CISimulator
            except ImportError:
                # Try relative import
                import sys
                from pathlib import Path
                ci_path = Path(__file__).parent
                if str(ci_path) not in sys.path:
                    sys.path.insert(0, str(ci_path))
                from simulator import CISimulator

            validation_results["checks"]["ci_simulator"] = "✅ Available"
        except ImportError as e:
            validation_results["errors"].append(f"CI Simulator not available: {e}")
            validation_results["overall_ready"] = False

        # Generate recommendations
        characteristics = self.detect_codebase_characteristics()

        if characteristics["total_files"] > 5000:
            validation_results["recommendations"].append(
                "Consider enabling incremental checks for large codebase"
            )

        if characteristics["test_files"] < characteristics["python_files"] * 0.3:
            validation_results["recommendations"].append(
                "Consider increasing test coverage (current test file ratio is low)"
            )

        self.logger.info(f"Production readiness: {'✅ Ready' if validation_results['overall_ready'] else '❌ Not Ready'}")
        return validation_results

    def setup_production_environment(self) -> bool:
        """本番環境のセットアップ"""
        self.logger.info("Setting up production environment...")

        try:
            # Generate optimized configuration
            config = self.generate_optimized_config()

            # Save production configuration
            if not self.save_config(config):
                return False

            # Update CI Simulator configuration
            if not self.update_ci_simulator_config(config):
                return False

            # Create required directories
            directories = [
                self.project_root / "logs",
                self.project_root / "reports" / "production",
                self.project_root / ".kiro" / "ci-history",
                self.project_root / "temp" / "ci-production"
            ]

            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Created directory: {directory}")

            # Setup log rotation configuration
            self._setup_log_rotation(config.logging)

            # Setup monitoring configuration
            self._setup_monitoring(config.monitoring)

            self.logger.info("Production environment setup completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to setup production environment: {e}")
            return False

    def _setup_log_rotation(self, logging_config: ProductionLoggingConfig) -> None:
        """ログローテーション設定"""
        # This would typically integrate with system log rotation
        # For now, we'll create a configuration file that can be used by external tools

        logrotate_config = f"""
# PhotoGeoView CI Simulator log rotation
{self.project_root}/logs/*.log {{
    daily
    rotate {logging_config.backup_count}
    size {logging_config.max_file_size_mb}M
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}}
"""

        config_file = self.project_root / "logs" / "logrotate.conf"
        with open(config_file, 'w') as f:
            f.write(logrotate_config)

        self.logger.debug(f"Log rotation configuration created: {config_file}")

    def _setup_monitoring(self, monitoring_config: MonitoringConfig) -> None:
        """監視設定"""
        # Create monitoring configuration file
        monitoring_settings = {
            "enabled": monitoring_config.metrics_enabled,
            "health_checks": monitoring_config.health_checks,
            "performance_tracking": monitoring_config.performance_tracking,
            "resource_monitoring": monitoring_config.resource_monitoring,
            "alert_thresholds": monitoring_config.alert_thresholds,
            "notification_channels": monitoring_config.notification_channels or []
        }

        monitoring_file = self.config_dir / "monitoring.json"
        with open(monitoring_file, 'w', encoding='utf-8') as f:
            json.dump(monitoring_settings, f, indent=2, ensure_ascii=False)

        self.logger.debug(f"Monitoring configuration created: {monitoring_file}")


def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="Production Configuration Manager")
    parser.add_argument("--project-root", type=Path, help="Project root path")
    parser.add_argument("--setup", action="store_true", help="Setup production environment")
    parser.add_argument("--validate", action="store_true", help="Validate production readiness")
    parser.add_argument("--generate-config", action="store_true", help="Generate optimized configuration")

    args = parser.parse_args()

    project_root = args.project_root or Path(__file__).parent.parent.parent
    manager = ProductionConfigManager(project_root)

    if args.setup:
        success = manager.setup_production_environment()
        print(f"Production environment setup: {'✅ Success' if success else '❌ Failed'}")
        sys.exit(0 if success else 1)

    elif args.validate:
        results = manager.validate_production_readiness()

        print("Production Readiness Validation")
        print("=" * 40)
        print(f"Overall Status: {'✅ Ready' if results['overall_ready'] else '❌ Not Ready'}")

        if results["checks"]:
            print("\nChecks:")
            for check, status in results["checks"].items():
                print(f"  {check}: {status}")

        if results["warnings"]:
            print("\nWarnings:")
            for warning in results["warnings"]:
                print(f"  ⚠️ {warning}")

        if results["errors"]:
            print("\nErrors:")
            for error in results["errors"]:
                print(f"  ❌ {error}")

        if results["recommendations"]:
            print("\nRecommendations:")
            for rec in results["recommendations"]:
                print(f"  💡 {rec}")

        sys.exit(0 if results["overall_ready"] else 1)

    elif args.generate_config:
        config = manager.generate_optimized_config()
        success = manager.save_config(config)
        print(f"Configuration generation: {'✅ Success' if success else '❌ Failed'}")
        sys.exit(0 if success else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
