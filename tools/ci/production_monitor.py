#!/usr/bin/env python3
"""
Production Monitoring System for CI Simulator

This module provides comprehensive monitoring and alerting capabilities
for production CI environments.

AI貢献者:
- Kiro: 本番監視システム設計・実装

作成者: Kiro AI統合システム
作成日: 2025年1月30日
"""

import json
import logging
import os
import smtplib
import sqlite3
import sys
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import psutil

try:
    from email.mime.multipart import MimeMultipart
    from email.mime.text import MimeText
except ImportError:
    # Fallback for older Python versions or missing email modules
    MimeText = None
    MimeMultipart = None


@dataclass
class MetricPoint:
    """メトリクスポイント"""

    timestamp: datetime
    name: str
    value: float
    unit: str
    tags: Dict[str, str] = None


@dataclass
class Alert:
    """アラート"""

    id: str
    name: str
    level: str  # INFO, WARNING, CRITICAL
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class MetricsCollector:
    """メトリクス収集器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.metrics_db = project_root / ".kiro" / "metrics.db"
        self.metrics_buue(maxlen=1000)
        self.collection_interval = 30  # seconds
        self.running = False
        self.collection_thread = None

        self._init_database()

    def _init_database(self) -> None:
        """データベースの初期化"""
        self.metrics_db.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(str(self.metrics_db)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT NOT NULL,
                    tags TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp
                ON metrics(timestamp)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_metrics_name
                ON metrics(name)
            """
            )

    def start_collection(self) -> None:
        """メトリクス収集開始"""
        if self.running:
            return

        self.running = True
        self.collection_thread = threading.Thread(target=self._collection_loop)
        self.collection_thread.daemon = True
        self.collection_thread.start()

    def stop_collection(self) -> None:
        """メトリクス収集停止"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)

    def _collection_loop(self) -> None:
        """メトリクス収集ループ"""
        while self.running:
            try:
                self._collect_system_metrics()
                self._collect_ci_metrics()
                self._flush_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                logging.error(f"Error in metrics collection: {e}")

    def _collect_system_metrics(self) -> None:
        """システムメトリクスの収集"""
        now = datetime.now()

        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics_buffer.append(
            MetricPoint(
                timestamp=now,
                name="system.cpu.usage_percent",
                value=cpu_percent,
                unit="percent",
            )
        )

        # Memory usage
        memory = psutil.virtual_memory()
        self.metrics_buffer.append(
            MetricPoint(
                timestamp=now,
                name="system.memory.usage_percent",
                value=memory.percent,
                unit="percent",
            )
        )

        self.metrics_buffer.append(
            MetricPoint(
                timestamp=now,
                name="system.memory.available_gb",
                value=memory.available / (1024**3),
                unit="gigabytes",
            )
        )

        # Disk usage
        disk = psutil.disk_usage(str(self.project_root))
        disk_percent = (disk.used / disk.total) * 100
        self.metrics_buffer.append(
            MetricPoint(
                timestamp=now,
                name="system.disk.usage_percent",
                value=disk_percent,
                unit="percent",
            )
        )

        self.metrics_buffer.append(
            MetricPoint(
                timestamp=now,
                name="system.disk.free_gb",
                value=disk.free / (1024**3),
                unit="gigabytes",
            )
        )

        # Load average (Unix-like systems only)
        if hasattr(os, "getloadavg"):
            load_avg = os.getloadavg()
            self.metrics_buffer.append(
                MetricPoint(
                    timestamp=now,
                    name="system.load.avg_1min",
                    value=load_avg[0],
                    unit="load",
                )
            )

    def _collect_ci_metrics(self) -> None:
        """CI関連メトリクスの収集"""
        now = datetime.now()

        # Check CI history directory size
        ci_history_dir = self.project_root / ".kiro" / "ci-history"
        if ci_history_dir.exists():
            total_size = sum(
                f.stat().st_size for f in ci_history_dir.rglob("*") if f.is_file()
            )
            self.metrics_buffer.append(
                MetricPoint(
                    timestamp=now,
                    name="ci.history.size_mb",
                    value=total_size / (1024**2),
                    unit="megabytes",
                )
            )

        # Check reports directory size
        reports_dir = self.project_root / "reports"
        if reports_dir.exists():
            total_size = sum(
                f.stat().st_size for f in reports_dir.rglob("*") if f.is_file()
            )
            self.metrics_buffer.append(
                MetricPoint(
                    timestamp=now,
                    name="ci.reports.size_mb",
                    value=total_size / (1024**2),
                    unit="megabytes",
                )
            )

        # Check logs directory size
        logs_dir = self.project_root / "logs"
        if logs_dir.exists():
            total_size = sum(
                f.stat().st_size for f in logs_dir.rglob("*.log") if f.is_file()
            )
            self.metrics_buffer.append(
                MetricPoint(
                    timestamp=now,
                    name="ci.logs.size_mb",
                    value=total_size / (1024**2),
                    unit="megabytes",
                )
            )

    def _flush_metrics(self) -> None:
        """メトリクスのデータベース保存"""
        if not self.metrics_buffer:
            return

        metrics_to_save = list(self.metrics_buffer)
        self.metrics_buffer.clear()

        with sqlite3.connect(str(self.metrics_db)) as conn:
            for metric in metrics_to_save:
                conn.execute(
                    """
                    INSERT INTO metrics (timestamp, name, value, unit, tags)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        metric.timestamp.isoformat(),
                        metric.name,
                        metric.value,
                        metric.unit,
                        json.dumps(metric.tags) if metric.tags else None,
                    ),
                )

    def get_metrics(self, name: str, hours: int = 24) -> List[MetricPoint]:
        """メトリクスの取得"""
        since = datetime.now() - timedelta(hours=hours)

        with sqlite3.connect(str(self.metrics_db)) as conn:
            cursor = conn.execute(
                """
                SELECT timestamp, name, value, unit, tags
                FROM metrics
                WHERE name = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """,
                (name, since.isoformat()),
            )

            metrics = []
            for row in cursor.fetchall():
                tags = json.loads(row[4]) if row[4] else None
                metrics.append(
                    MetricPoint(
                        timestamp=datetime.fromisoformat(row[0]),
                        name=row[1],
                        value=row[2],
                        unit=row[3],
                        tags=tags,
                    )
                )

            return metrics

    def cleanup_old_metrics(self, days: int = 30) -> None:
        """古いメトリクスのクリーンアップ"""
        cutoff = datetime.now() - timedelta(days=days)

        with sqlite3.connect(str(self.metrics_db)) as conn:
            cursor = conn.execute(
                """
                DELETE FROM metrics WHERE timestamp < ?
            """,
                (cutoff.isoformat(),),
            )

            deleted_count = cursor.rowcount
            logging.info(f"Cleaned up {deleted_count} old metric records")


class AlertManager:
    """アラート管理器"""

    def __init__(self, project_root: Path, config: Dict[str, Any]):
        self.project_root = project_root
        self.config = config
        self.alerts_db = project_root / ".kiro" / "alerts.db"
        self.active_alerts = {}
        self.alert_handlers = []

        self._init_database()
        self._setup_handlers()

    def _init_database(self) -> None:
        """データベースの初期化"""
        self.alerts_db.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(str(self.alerts_db)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    resolved INTEGER DEFAULT 0,
                    resolved_at TEXT
                )
            """
            )

    def _setup_handlers(self) -> None:
        """アラートハンドラーのセットアップ"""
        # Console handler (always enabled)
        self.alert_handlers.append(self._console_handler)

        # Email handler (if configured)
        if self.config.get("email", {}).get("enabled", False):
            self.alert_handlers.append(self._email_handler)

        # File handler
        self.alert_handlers.append(self._file_handler)

    def check_thresholds(self, metrics_collector: MetricsCollector) -> None:
        """閾値チェック"""
        thresholds = self.config.get("alert_thresholds", {})

        for metric_name, threshold in thresholds.items():
            recent_metrics = metrics_collector.get_metrics(metric_name, hours=1)

            if not recent_metrics:
                continue

            latest_value = recent_metrics[0].value
            alert_id = f"{metric_name}_threshold"

            if latest_value > threshold:
                if alert_id not in self.active_alerts:
                    alert = Alert(
                        id=alert_id,
                        name=f"{metric_name} Threshold Exceeded",
                        level="WARNING",
                        message=f"{metric_name} is {latest_value:.2f}, exceeding threshold of {threshold}",
                        timestamp=datetime.now(),
                    )
                    self.trigger_alert(alert)
            else:
                if alert_id in self.active_alerts:
                    self.resolve_alert(alert_id)

    def trigger_alert(self, alert: Alert) -> None:
        """アラートの発火"""
        self.active_alerts[alert.id] = alert

        # Save to database
        with sqlite3.connect(str(self.alerts_db)) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO alerts
                (id, name, level, message, timestamp, resolved)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    alert.id,
                    alert.name,
                    alert.level,
                    alert.message,
                    alert.timestamp.isoformat(),
                    0,
                ),
            )

        # Trigger handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logging.error(f"Alert handler error: {e}")

    def resolve_alert(self, alert_id: str) -> None:
        """アラートの解決"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()

            # Update database
            with sqlite3.connect(str(self.alerts_db)) as conn:
                conn.execute(
                    """
                    UPDATE alerts
                    SET resolved = 1, resolved_at = ?
                    WHERE id = ?
                """,
                    (alert.resolved_at.isoformat(), alert_id),
                )

            # Remove from active alerts
            del self.active_alerts[alert_id]

            logging.info(f"Alert resolved: {alert.name}")

    def _console_handler(self, alert: Alert) -> None:
        """コンソールアラートハンドラー"""
        level_icons = {"INFO": "ℹ️", "WARNING": "⚠️", "CRITICAL": "🚨"}

        icon = level_icons.get(alert.level, "❗")
        print(f"{icon} [{alert.level}] {alert.name}: {alert.message}")

    def _file_handler(self, alert: Alert) -> None:
        """ファイルアラートハンドラー"""
        alerts_log = self.project_root / "logs" / "alerts.log"
        alerts_log.parent.mkdir(parents=True, exist_ok=True)

        with open(alerts_log, "a", encoding="utf-8") as f:
            f.write(
                f"{alert.timestamp.isoformat()} [{alert.level}] {alert.name}: {alert.message}\n"
            )

    def _email_handler(self, alert: Alert) -> None:
        """メールアラートハンドラー"""
        email_config = self.config.get("email", {})

        if not email_config.get("enabled", False):
            return

        if MimeText is None or MimeMultipart is None:
            logging.warning(
                "Email functionality not available (missing email.mime modules)"
            )
            return

        try:
            msg = MimeMultipart()
            msg["From"] = email_config.get("from_address", "ci@photogeoview.com")
            msg["To"] = ", ".join(email_config.get("to_addresses", []))
            msg["Subject"] = f"[PhotoGeoView CI] {alert.level}: {alert.name}"

            body = f"""
Alert Details:
- Name: {alert.name}
- Level: {alert.level}
- Message: {alert.message}
- Timestamp: {alert.timestamp}
- Alert ID: {alert.id}

This is an automated alert from the PhotoGeoView CI monitoring system.
"""

            msg.attach(MimeText(body, "plain"))

            server = smtplib.SMTP(
                email_config.get("smtp_server", "localhost"),
                email_config.get("smtp_port", 587),
            )

            if email_config.get("use_tls", True):
                server.starttls()

            if email_config.get("username") and email_config.get("password"):
                server.login(email_config["username"], email_config["password"])

            server.send_message(msg)
            server.quit()

            logging.info(f"Alert email sent: {alert.name}")

        except Exception as e:
            logging.error(f"Failed to send alert email: {e}")


class ProductionMonitor:
    """本番監視システム"""

    def __init__(self, project_root: Path, config_file: Optional[Path] = None):
        self.project_root = project_root
        self.config = self._load_config(config_file)
        self.metrics_collector = MetricsCollector(project_root)
        self.alert_manager = AlertManager(project_root, self.config)
        self.monitoring_thread = None
        self.running = False

    def _load_config(self, config_file: Optional[Path]) -> Dict[str, Any]:
        """設定の読み込み"""
        if config_file is None:
            config_file = self.project_root / ".kiro" / "settings" / "monitoring.json"

        if not config_file.exists():
            return self._default_config()

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Failed to load monitoring config: {e}")
            return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """デフォルト設定"""
        return {
            "enabled": True,
            "collection_interval": 30,
            "alert_thresholds": {
                "system.cpu.usage_percent": 90.0,
                "system.memory.usage_percent": 85.0,
                "system.disk.usage_percent": 90.0,
                "ci.logs.size_mb": 1000.0,
            },
            "email": {
                "enabled": False,
                "smtp_server": "localhost",
                "smtp_port": 587,
                "use_tls": True,
                "from_address": "ci@photogeoview.com",
                "to_addresses": [],
            },
            "retention_days": 30,
        }

    def start(self) -> None:
        """監視開始"""
        if not self.config.get("enabled", True):
            logging.info("Monitoring is disabled")
            return

        if self.running:
            return

        logging.info("Starting production monitoring...")

        self.running = True
        self.metrics_collector.start_collection()

        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

    def stop(self) -> None:
        """監視停止"""
        logging.info("Stopping production monitoring...")

        self.running = False
        self.metrics_collector.stop_collection()

        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)

    def _monitoring_loop(self) -> None:
        """監視ループ"""
        while self.running:
            try:
                # Check alert thresholds
                self.alert_manager.check_thresholds(self.metrics_collector)

                # Cleanup old data
                if datetime.now().hour == 2:  # Daily cleanup at 2 AM
                    retention_days = self.config.get("retention_days", 30)
                    self.metrics_collector.cleanup_old_metrics(retention_days)

                time.sleep(60)  # Check every minute

            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")

    def get_health_status(self) -> Dict[str, Any]:
        """ヘルスステータスの取得"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "components": {},
            "active_alerts": len(self.alert_manager.active_alerts),
            "metrics": {},
        }

        # System metrics
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(str(self.project_root))

            status["components"]["system"] = {
                "status": "healthy",
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "disk_usage": (disk.used / disk.total) * 100,
            }

            # Check if any system metrics are critical
            thresholds = self.config.get("alert_thresholds", {})
            if (
                cpu_percent > thresholds.get("system.cpu.usage_percent", 90)
                or memory.percent > thresholds.get("system.memory.usage_percent", 85)
                or (disk.used / disk.total) * 100
                > thresholds.get("system.disk.usage_percent", 90)
            ):
                status["components"]["system"]["status"] = "warning"
                status["overall_status"] = "warning"

        except Exception as e:
            status["components"]["system"] = {"status": "error", "error": str(e)}
            status["overall_status"] = "error"

        # CI Simulator status
        try:
            from tools.ci.simulator import CISimulator

            status["components"]["ci_simulator"] = {"status": "available"}
        except ImportError:
            status["components"]["ci_simulator"] = {"status": "unavailable"}
            status["overall_status"] = "warning"

        # Active alerts
        if self.alert_manager.active_alerts:
            status["active_alerts_details"] = [
                {
                    "id": alert.id,
                    "name": alert.name,
                    "level": alert.level,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                }
                for alert in self.alert_manager.active_alerts.values()
            ]

            # Check if any critical alerts
            if any(
                alert.level == "CRITICAL"
                for alert in self.alert_manager.active_alerts.values()
            ):
                status["overall_status"] = "critical"

        return status

    def generate_report(self, hours: int = 24) -> Dict[str, Any]:
        """監視レポートの生成"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "period_hours": hours,
            "summary": {},
            "metrics": {},
            "alerts": {},
            "recommendations": [],
        }

        # Collect metrics summary
        metric_names = [
            "system.cpu.usage_percent",
            "system.memory.usage_percent",
            "system.disk.usage_percent",
            "ci.logs.size_mb",
        ]

        for metric_name in metric_names:
            metrics = self.metrics_collector.get_metrics(metric_name, hours)
            if metrics:
                values = [m.value for m in metrics]
                report["metrics"][metric_name] = {
                    "current": values[0] if values else 0,
                    "average": sum(values) / len(values),
                    "max": max(values),
                    "min": min(values),
                    "count": len(values),
                }

        # Alert summary
        with sqlite3.connect(str(self.alert_manager.alerts_db)) as conn:
            since = datetime.now() - timedelta(hours=hours)
            cursor = conn.execute(
                """
                SELECT level, COUNT(*) as count
                FROM alerts
                WHERE timestamp >= ?
                GROUP BY level
            """,
                (since.isoformat(),),
            )

            alert_counts = dict(cursor.fetchall())
            report["alerts"]["counts"] = alert_counts
            report["alerts"]["total"] = sum(alert_counts.values())

        # Generate recommendations
        if report["metrics"].get("system.cpu.usage_percent", {}).get("average", 0) > 70:
            report["recommendations"].append(
                "Consider reducing parallel jobs to lower CPU usage"
            )

        if report["metrics"].get("ci.logs.size_mb", {}).get("current", 0) > 500:
            report["recommendations"].append(
                "Consider enabling log rotation or cleanup"
            )

        return report


def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="Production Monitoring System")
    parser.add_argument("--project-root", type=Path, help="Project root path")
    parser.add_argument("--start", action="store_true", help="Start monitoring daemon")
    parser.add_argument("--status", action="store_true", help="Show health status")
    parser.add_argument("--report", type=int, help="Generate report for N hours")
    parser.add_argument("--config", type=Path, help="Configuration file path")

    args = parser.parse_args()

    project_root = args.project_root or Path(__file__).parent.parent.parent
    monitor = ProductionMonitor(project_root, args.config)

    if args.start:
        try:
            monitor.start()
            print("Production monitoring started. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop()
            print("Monitoring stopped.")

    elif args.status:
        status = monitor.get_health_status()
        print(json.dumps(status, indent=2))

    elif args.report:
        report = monitor.generate_report(args.report)
        print(json.dumps(report, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
