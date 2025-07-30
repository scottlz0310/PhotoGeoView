"""
Resource Manager for CI Simulation Tool

This module provides comprehensive resource management and cleanup functionality
for the CI simulation system, including temporary file management, resource
monitoring, and graceful shutdown procedures.

Author: Kiro (AI Integration and Quality Assurance)
"""

import atexit
import logging
import os
import shutil
import signal
import sys
import tempfile
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

import psutil

try:
    from .models import CheckStatus
    from .utils import ensure_directory_exists, formuration, get_project_root
except ImportError:
    from models import CheckStatus

    from utils import ensure_directory_exists, format_duration, get_project_root


@dataclass
class ResourceUsage:
    """Represents current resource usage statistics."""

    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_available_gb: float
    cpu_percent: float
    process_count: int
    open_files: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TempResource:
    """Represents a temporary resource that needs cleanup."""

    path: str
    resource_type: str  # 'file', 'directory', 'process', 'socket'
    created_at: datetime
    size_bytes: int = 0
    cleanup_function: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResourceManager:
    """
    Comprehensive resource manager for CI simulation.

    This class handles temporary file cleanup, resource monitoring,
    and graceful shutdown procedures to ensure the CI simulation
    doesn't leave behind artifacts or consume excessive resources.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the resource manager.

        Args:
            config: Configuration dictionary for resource management
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Resource tracking
        self.temp_resources: Dict[str, TempResource] = {}
        self.active_processes: Set[int] = set()
        self.resource_locks: Dict[str, threading.Lock] = {}

        # Configuration
        self.max_memory_percent = self.config.get("max_memory_percent", 80.0)
        self.max_disk_percent = self.config.get("max_disk_percent", 90.0)
        self.cleanup_interval = self.config.get("cleanup_interval", 300)  # 5 minutes
        self.temp_file_max_age = self.config.get("temp_file_max_age", 3600)  # 1 hour
        self.monitoring_enabled = self.config.get("monitoring_enabled", True)

        # Monitoring thread
        self._monitoring_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        self._resource_history: List[ResourceUsage] = []

        # Cleanup directories
        self.project_root = get_project_root()
        self.temp_dirs = [
            self.project_root / "temp",
            self.project_root / ".pytest_cache",
            self.project_root / "__pycache__",
            self.project_root / "logs" / "temp",
            self.project_root / "reports" / "temp",
        ]

        # Register cleanup handlers
        atexit.register(self.cleanup_all)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # Start monitoring if enabled
        if self.monitoring_enabled:
            self.start_monitoring()

    def start_monitoring(self) -> None:
        """Start resource monitoring thread."""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            return

        self._shutdown_event.clear()
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True, name="ResourceMonitor"
        )
        self._monitoring_thread.start()
        self.logger.info("Resource monitoring started")

    def stop_monitoring(self) -> None:
        """Stop resource monitoring thread."""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._shutdown_event.set()
            self._monitoring_thread.join(timeout=5.0)
            self.logger.info("Resource monitoring stopped")

    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while not self._shutdown_event.is_set():
            try:
                # Collect resource usage
                usage = self.get_resource_usage()
                self._resource_history.append(usage)

                # Keep only recent history (last 24 hours)
                cutoff_time = datetime.now() - timedelta(hours=24)
                self._resource_history = [
                    u for u in self._resource_history if u.timestamp > cutoff_time
                ]

                # Check for resource issues
                self._check_resource_limits(usage)

                # Periodic cleanup
                self._periodic_cleanup()

            except Exception as e:
                self.logger.error(f"Error in resource monitoring: {e}")

            # Wait for next check
            self._shutdown_event.wait(self.cleanup_interval)

    def get_resource_usage(self) -> ResourceUsage:
        """Get current resource usage statistics."""
        try:
            # Memory information
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)

            # Disk information
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            disk_used_gb = disk.used / (1024 * 1024 * 1024)
            disk_available_gb = disk.free / (1024 * 1024 * 1024)

            # CPU information
            cpu_percent = psutil.cpu_percent(interval=1)

            # Process information
            current_process = psutil.Process()
            process_count = len(current_process.children(recursive=True)) + 1

            try:
                open_files = len(current_process.open_files())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                open_files = 0

            return ResourceUsage(
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_percent=disk_percent,
                disk_used_gb=disk_used_gb,
                disk_available_gb=disk_available_gb,
                cpu_percent=cpu_percent,
                process_count=process_count,
                open_files=open_files,
            )

        except Exception as e:
            self.logger.error(f"Error getting resource usage: {e}")
            return ResourceUsage(
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_percent=0.0,
                disk_used_gb=0.0,
                disk_available_gb=0.0,
                cpu_percent=0.0,
                process_count=0,
                open_files=0,
            )

    def _check_resource_limits(self, usage: ResourceUsage) -> None:
        """Check if resource usage exceeds limits and take action."""

        # Memory limit check
        if usage.memory_percent > self.max_memory_percent:
            self.logger.warning(
                f"Memory usage high: {usage.memory_percent:.1f}% "
                f"(limit: {self.max_memory_percent}%)"
            )
            self._handle_high_memory_usage()

        # Disk limit check
        if usage.disk_percent > self.max_disk_percent:
            self.logger.warning(
                f"Disk usage high: {usage.disk_percent:.1f}% "
                f"(limit: {self.max_disk_percent}%)"
            )
            self._handle_high_disk_usage()

    def _handle_high_memory_usage(self) -> None:
        """Handle high memory usage situation."""
        self.logger.info("Attempting to reduce memory usage...")

        # Force garbage collection
        import gc

        gc.collect()

        # Clean up old temporary files
        self.cleanup_temp_files(max_age_seconds=300)  # 5 minutes

        # Log current resource usage
        usage = self.get_resource_usage()
        self.logger.info(f"Memory usage after cleanup: {usage.memory_percent:.1f}%")

    def _handle_high_disk_usage(self) -> None:
        """Handle high disk usage situation."""
        self.logger.info("Attempting to reduce disk usage...")

        # Clean up temporary files
        self.cleanup_temp_files()

        # Clean up old log files
        self._cleanup_old_logs()

        # Clean up old reports
        self._cleanup_old_reports()

        # Log current resource usage
        usage = self.get_resource_usage()
        self.logger.info(f"Disk usage after cleanup: {usage.disk_percent:.1f}%")

    def _periodic_cleanup(self) -> None:
        """Perform periodic cleanup tasks."""
        try:
            # Clean up old temporary files
            self.cleanup_temp_files()

            # Clean up completed processes
            self._cleanup_completed_processes()

            # Clean up old resource history
            cutoff_time = datetime.now() - timedelta(hours=24)
            self._resource_history = [
                u for u in self._resource_history if u.timestamp > cutoff_time
            ]

        except Exception as e:
            self.logger.error(f"Error in periodic cleanup: {e}")

    def register_temp_resource(
        self,
        path: str,
        resource_type: str = "file",
        cleanup_function: Optional[Callable] = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Register a temporary resource for cleanup.

        Args:
            path: Path to the resource
            resource_type: Type of resource ('file', 'directory', 'process')
            cleanup_function: Custom cleanup function
            metadata: Additional metadata

        Returns:
            Resource ID for tracking
        """
        resource_id = f"{resource_type}_{len(self.temp_resources)}_{int(time.time())}"

        # Get file size if it's a file/directory
        size_bytes = 0
        try:
            if os.path.exists(path):
                if os.path.isfile(path):
                    size_bytes = os.path.getsize(path)
                elif os.path.isdir(path):
                    size_bytes = sum(
                        os.path.getsize(os.path.join(dirpath, filename))
                        for dirpath, dirnames, filenames in os.walk(path)
                        for filename in filenames
                    )
        except (OSError, IOError):
            pass

        resource = TempResource(
            path=path,
            resource_type=resource_type,
            created_at=datetime.now(),
            size_bytes=size_bytes,
            cleanup_function=cleanup_function,
            metadata=metadata or {},
        )

        self.temp_resources[resource_id] = resource
        self.logger.debug(f"Registered temp resource: {resource_id} -> {path}")

        return resource_id

    def unregister_temp_resource(self, resource_id: str) -> bool:
        """
        Unregister a temporary resource.

        Args:
            resource_id: Resource ID to unregister

        Returns:
            True if resource was found and unregistered
        """
        if resource_id in self.temp_resources:
            del self.temp_resources[resource_id]
            self.logger.debug(f"Unregistered temp resource: {resource_id}")
            return True
        return False

    @contextmanager
    def temp_directory(self, prefix: str = "ci_sim_", suffix: str = ""):
        """
        Context manager for temporary directory.

        Args:
            prefix: Directory name prefix
            suffix: Directory name suffix

        Yields:
            Path to temporary directory
        """
        temp_dir = tempfile.mkdtemp(prefix=prefix, suffix=suffix)
        resource_id = self.register_temp_resource(temp_dir, "directory")

        try:
            yield temp_dir
        finally:
            self.cleanup_resource(resource_id)

    @contextmanager
    def temp_file(self, prefix: str = "ci_sim_", suffix: str = "", mode: str = "w"):
        """
        Context manager for temporary file.

        Args:
            prefix: File name prefix
            suffix: File name suffix
            mode: File open mode

        Yields:
            File object
        """
        fd, temp_path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
        resource_id = self.register_temp_resource(temp_path, "file")

        try:
            with os.fdopen(fd, mode) as f:
                yield f
        finally:
            self.cleanup_resource(resource_id)

    def cleanup_resource(self, resource_id: str) -> bool:
        """
        Clean up a specific resource.

        Args:
            resource_id: Resource ID to clean up

        Returns:
            True if cleanup was successful
        """
        if resource_id not in self.temp_resources:
            return False

        resource = self.temp_resources[resource_id]
        success = False

        try:
            if resource.cleanup_function:
                # Use custom cleanup function
                resource.cleanup_function()
                success = True
            else:
                # Default cleanup based on resource type
                if resource.resource_type == "file":
                    if os.path.exists(resource.path):
                        os.remove(resource.path)
                        success = True
                elif resource.resource_type == "directory":
                    if os.path.exists(resource.path):
                        shutil.rmtree(resource.path)
                        success = True
                elif resource.resource_type == "process":
                    # Process cleanup would be handled by custom function
                    success = True

            if success:
                self.logger.debug(
                    f"Cleaned up resource: {resource_id} -> {resource.path}"
                )

        except Exception as e:
            self.logger.error(f"Error cleaning up resource {resource_id}: {e}")

        # Remove from tracking regardless of success
        self.unregister_temp_resource(resource_id)
        return success

    def cleanup_temp_files(self, max_age_seconds: Optional[int] = None) -> int:
        """
        Clean up temporary files based on age.

        Args:
            max_age_seconds: Maximum age in seconds (defaults to config value)

        Returns:
            Number of files cleaned up
        """
        if max_age_seconds is None:
            max_age_seconds = self.temp_file_max_age

        cutoff_time = datetime.now() - timedelta(seconds=max_age_seconds)
        cleaned_count = 0

        # Clean up registered temporary resources
        resources_to_cleanup = []
        for resource_id, resource in self.temp_resources.items():
            if resource.created_at < cutoff_time:
                resources_to_cleanup.append(resource_id)

        for resource_id in resources_to_cleanup:
            if self.cleanup_resource(resource_id):
                cleaned_count += 1

        # Clean up unregistered temporary files in known directories
        for temp_dir in self.temp_dirs:
            if temp_dir.exists():
                cleaned_count += self._cleanup_directory_by_age(temp_dir, cutoff_time)

        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} temporary files")

        return cleaned_count

    def _cleanup_directory_by_age(self, directory: Path, cutoff_time: datetime) -> int:
        """Clean up files in directory older than cutoff time."""
        cleaned_count = 0

        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    try:
                        # Check file modification time
                        mtime = datetime.fromtimestamp(item.stat().st_mtime)
                        if mtime < cutoff_time:
                            item.unlink()
                            cleaned_count += 1
                    except (OSError, IOError) as e:
                        self.logger.debug(f"Could not clean up {item}: {e}")

                elif item.is_dir() and not any(item.iterdir()):
                    # Remove empty directories
                    try:
                        item.rmdir()
                        cleaned_count += 1
                    except (OSError, IOError):
                        pass

        except Exception as e:
            self.logger.error(f"Error cleaning directory {directory}: {e}")

        return cleaned_count

    def _cleanup_old_logs(self, max_age_days: int = 7) -> None:
        """Clean up old log files."""
        logs_dir = self.project_root / "logs"
        if not logs_dir.exists():
            return

        cutoff_time = datetime.now() - timedelta(days=max_age_days)

        for log_file in logs_dir.glob("*.log*"):
            try:
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime < cutoff_time:
                    log_file.unlink()
                    self.logger.debug(f"Cleaned up old log file: {log_file}")
            except (OSError, IOError):
                pass

    def _cleanup_old_reports(self, max_age_days: int = 30) -> None:
        """Clean up old report files."""
        reports_dir = self.project_root / "reports"
        if not reports_dir.exists():
            return

        cutoff_time = datetime.now() - timedelta(days=max_age_days)

        # Clean up timestamped report directories
        for report_dir in reports_dir.glob("*/20*"):  # Matches YYYY-MM-DD patterns
            try:
                mtime = datetime.fromtimestamp(report_dir.stat().st_mtime)
                if mtime < cutoff_time:
                    shutil.rmtree(report_dir)
                    self.logger.debug(f"Cleaned up old report directory: {report_dir}")
            except (OSError, IOError):
                pass

    def _cleanup_completed_processes(self) -> None:
        """Clean up tracking for completed processes."""
        completed_pids = []

        for pid in self.active_processes:
            try:
                process = psutil.Process(pid)
                if not process.is_running():
                    completed_pids.append(pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                completed_pids.append(pid)

        for pid in completed_pids:
            self.active_processes.discard(pid)

    def register_process(self, pid: int) -> None:
        """Register a process for tracking."""
        self.active_processes.add(pid)
        self.logger.debug(f"Registered process: {pid}")

    def terminate_processes(self, timeout: float = 10.0) -> int:
        """
        Terminate all tracked processes.

        Args:
            timeout: Timeout for graceful termination

        Returns:
            Number of processes terminated
        """
        terminated_count = 0

        for pid in list(self.active_processes):
            try:
                process = psutil.Process(pid)
                if process.is_running():
                    # Try graceful termination first
                    process.terminate()

                    try:
                        process.wait(timeout=timeout)
                        terminated_count += 1
                        self.logger.debug(f"Gracefully terminated process: {pid}")
                    except psutil.TimeoutExpired:
                        # Force kill if graceful termination fails
                        process.kill()
                        terminated_count += 1
                        self.logger.warning(f"Force killed process: {pid}")

                self.active_processes.discard(pid)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.active_processes.discard(pid)

        if terminated_count > 0:
            self.logger.info(f"Terminated {terminated_count} processes")

        return terminated_count

    def cleanup_all(self) -> None:
        """Perform complete cleanup of all resources."""
        self.logger.info("Starting complete resource cleanup...")

        # Stop monitoring
        self.stop_monitoring()

        # Clean up all registered temporary resources
        resource_ids = list(self.temp_resources.keys())
        cleaned_resources = 0

        for resource_id in resource_ids:
            if self.cleanup_resource(resource_id):
                cleaned_resources += 1

        # Clean up temporary files
        cleaned_files = self.cleanup_temp_files()

        # Terminate processes
        terminated_processes = self.terminate_processes()

        self.logger.info(
            f"Cleanup complete: {cleaned_resources} resources, "
            f"{cleaned_files} temp files, {terminated_processes} processes"
        )

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, initiating cleanup...")
        self.cleanup_all()
        sys.exit(0)

    def get_resource_statistics(self) -> Dict[str, Any]:
        """Get resource usage statistics."""
        current_usage = self.get_resource_usage()

        stats = {
            "current_usage": {
                "memory_percent": current_usage.memory_percent,
                "memory_used_mb": current_usage.memory_used_mb,
                "disk_percent": current_usage.disk_percent,
                "disk_used_gb": current_usage.disk_used_gb,
                "cpu_percent": current_usage.cpu_percent,
                "process_count": current_usage.process_count,
                "open_files": current_usage.open_files,
            },
            "tracked_resources": {
                "temp_resources": len(self.temp_resources),
                "active_processes": len(self.active_processes),
                "total_temp_size_mb": sum(
                    r.size_bytes for r in self.temp_resources.values()
                )
                / (1024 * 1024),
            },
            "limits": {
                "max_memory_percent": self.max_memory_percent,
                "max_disk_percent": self.max_disk_percent,
            },
        }

        # Add historical data if available
        if self._resource_history:
            recent_history = self._resource_history[-10:]  # Last 10 measurements
            stats["history"] = {
                "avg_memory_percent": sum(u.memory_percent for u in recent_history)
                / len(recent_history),
                "avg_cpu_percent": sum(u.cpu_percent for u in recent_history)
                / len(recent_history),
                "measurements": len(self._resource_history),
            }

        return stats

    def generate_resource_report(self) -> str:
        """Generate a detailed resource usage report."""
        stats = self.get_resource_statistics()
        current = stats["current_usage"]
        tracked = stats["tracked_resources"]

        report_lines = [
            "# Resource Usage Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Current Resource Usage",
            f"- Memory: {current['memory_percent']:.1f}% ({current['memory_used_mb']:.1f} MB used)",
            f"- Disk: {current['disk_percent']:.1f}% ({current['disk_used_gb']:.1f} GB used)",
            f"- CPU: {current['cpu_percent']:.1f}%",
            f"- Processes: {current['process_count']}",
            f"- Open Files: {current['open_files']}",
            "",
            "## Tracked Resources",
            f"- Temporary Resources: {tracked['temp_resources']}",
            f"- Active Processes: {tracked['active_processes']}",
            f"- Total Temp Size: {tracked['total_temp_size_mb']:.1f} MB",
            "",
            "## Resource Limits",
            f"- Max Memory: {stats['limits']['max_memory_percent']}%",
            f"- Max Disk: {stats['limits']['max_disk_percent']}%",
        ]

        # Add historical data if available
        if "history" in stats:
            history = stats["history"]
            report_lines.extend(
                [
                    "",
                    "## Historical Averages",
                    f"- Average Memory: {history['avg_memory_percent']:.1f}%",
                    f"- Average CPU: {history['avg_cpu_percent']:.1f}%",
                    f"- Measurements: {history['measurements']}",
                ]
            )

        # Add temporary resource details
        if self.temp_resources:
            report_lines.extend(
                [
                    "",
                    "## Temporary Resources Details",
                ]
            )

            for resource_id, resource in self.temp_resources.items():
                age = datetime.now() - resource.created_at
                size_mb = resource.size_bytes / (1024 * 1024)
                report_lines.append(
                    f"- {resource_id}: {resource.resource_type} "
                    f"({size_mb:.1f} MB, age: {format_duration(age.total_seconds())})"
                )

        return "\n".join(report_lines)

    def save_resource_report(self, filepath: str) -> None:
        """Save resource report to file."""
        ensure_directory_exists(os.path.dirname(filepath))

        report = self.generate_resource_report()

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)

        self.logger.info(f"Resource report saved to: {filepath}")


# Global resource manager instance
_resource_manager: Optional[ResourceManager] = None


def get_resource_manager(config: Dict[str, Any] = None) -> ResourceManager:
    """Get or create the global resource manager instance."""
    global _resource_manager

    if _resource_manager is None:
        _resource_manager = ResourceManager(config)

    return _resource_manager


def cleanup_on_exit():
    """Cleanup function to be called on exit."""
    global _resource_manager

    if _resource_manager is not None:
        _resource_manager.cleanup_all()


# Register cleanup on module import
atexit.register(cleanup_on_exit)
