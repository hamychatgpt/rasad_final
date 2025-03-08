"""
اندپوینت‌های مدیریت سرویس‌ها.

این ماژول اندپوینت‌های مربوط به مدیریت سرویس‌های سیستم را فراهم می‌کند.
"""

import os
import psutil
import platform
import asyncio
import socket
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from app.db.session import get_db
from app.db.models import AppUser
from app.core.security import get_current_user, get_current_superuser
from app.config import settings

router = APIRouter(prefix="/services", tags=["services"])

# متغیرهای جهانی برای نگهداری وضعیت فرآیندها
service_processes = {
    "collector": None,
    "processor": None,
    "analyzer": None
}

# مسیرهای اسکریپت‌های سرویس‌ها
service_scripts = {
    "collector": "scripts/run_collector.py",
    "processor": "scripts/run_processor.py",
    "analyzer": "scripts/run_analyzer.py",
    "all": "scripts/run_all.py"
}


async def get_service_status(service_name: str) -> Dict[str, Any]:
    """
    دریافت وضعیت یک سرویس.
    
    Args:
        service_name (str): نام سرویس
        
    Returns:
        Dict[str, Any]: وضعیت سرویس
    """
    if service_name not in service_processes:
        return {
            "status": "unknown",
            "pid": None,
            "running": False,
            "memory_usage": None,
            "cpu_percent": None,
            "uptime": None
        }
    
    process = service_processes[service_name]
    
    if process is None or not process.is_running():
        return {
            "status": "stopped",
            "pid": None,
            "running": False,
            "memory_usage": None,
            "cpu_percent": None,
            "uptime": None
        }
    
    try:
        # دریافت اطلاعات فرآیند
        with process.oneshot():
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent(interval=0.1)
            create_time = datetime.fromtimestamp(process.create_time())
            uptime = (datetime.now() - create_time).total_seconds()
        
        return {
            "status": "running",
            "pid": process.pid,
            "running": True,
            "memory_usage": {
                "rss": memory_info.rss / (1024 * 1024),  # MB
                "vms": memory_info.vms / (1024 * 1024)   # MB
            },
            "cpu_percent": cpu_percent,
            "uptime": uptime,
            "uptime_human": str(timedelta(seconds=int(uptime)))
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return {
            "status": "error",
            "pid": process.pid if process else None,
            "running": False,
            "memory_usage": None,
            "cpu_percent": None,
            "uptime": None
        }


@router.get("/", response_model=Dict[str, Any])
async def get_services_status(
    current_user: AppUser = Depends(get_current_user)
):
    """
    دریافت وضعیت تمام سرویس‌ها.
    
    Args:
        current_user (AppUser): کاربر فعلی
    
    Returns:
        Dict[str, Any]: وضعیت سرویس‌ها
    """
    services_status = {}
    
    for service_name in service_processes.keys():
        services_status[service_name] = await get_service_status(service_name)
    
    # اطلاعات سیستم
    system_info = {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_total": psutil.virtual_memory().total / (1024 * 1024 * 1024),  # GB
        "memory_available": psutil.virtual_memory().available / (1024 * 1024 * 1024),  # GB
        "memory_percent": psutil.virtual_memory().percent
    }
    
    return {
        "services": services_status,
        "system_info": system_info,
        "timestamp": datetime.now().isoformat()
    }


async def start_service_task(service_name: str):
    """
    شروع یک سرویس به صورت غیرهمزمان.
    
    Args:
        service_name (str): نام سرویس
    """
    global service_processes
    
    if service_name not in service_scripts:
        return
    
    # بررسی وضعیت فعلی
    current_process = service_processes.get(service_name)
    if current_process is not None and current_process.is_running():
        try:
            current_process.terminate()
            current_process.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            pass
    
    # شروع فرآیند جدید
    script_path = service_scripts[service_name]
    
    try:
        # شروع فرآیند به صورت subprocess
        process = psutil.Popen(
            ["python", script_path],
            stdout=open(f"logs/{service_name}_output.log", "a"),
            stderr=open(f"logs/{service_name}_error.log", "a"),
            start_new_session=True
        )
        
        service_processes[service_name] = process
        
        # انتظار کوتاه برای اطمینان از شروع موفقیت‌آمیز
        await asyncio.sleep(2)
        
        if not process.is_running():
            raise Exception(f"فرآیند {service_name} خیلی زود متوقف شد")
            
    except Exception as e:
        raise Exception(f"خطا در شروع سرویس {service_name}: {str(e)}")


@router.post("/{service_name}/start", response_model=Dict[str, Any])
async def start_service(
    service_name: str,
    background_tasks: BackgroundTasks,
    current_user: AppUser = Depends(get_current_superuser)
):
    """
    شروع یک سرویس.
    
    Args:
        service_name (str): نام سرویس
        background_tasks (BackgroundTasks): تسک‌های پس‌زمینه
        current_user (AppUser): کاربر فعلی (باید مدیر سیستم باشد)
    
    Returns:
        Dict[str, Any]: وضعیت عملیات
    """
    if service_name not in service_scripts and service_name != "all":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"سرویس {service_name} نامعتبر است"
        )
    
    try:
        if service_name == "all":
            # شروع همه سرویس‌ها
            background_tasks.add_task(start_service_task, "all")
        else:
            # شروع یک سرویس خاص
            background_tasks.add_task(start_service_task, service_name)
        
        return {
            "status": "starting",
            "service": service_name,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در شروع سرویس: {str(e)}"
        )


@router.post("/{service_name}/stop", response_model=Dict[str, Any])
async def stop_service(
    service_name: str,
    current_user: AppUser = Depends(get_current_superuser)
):
    """
    توقف یک سرویس.
    
    Args:
        service_name (str): نام سرویس
        current_user (AppUser): کاربر فعلی (باید مدیر سیستم باشد)
    
    Returns:
        Dict[str, Any]: وضعیت عملیات
    """
    if service_name not in service_processes and service_name != "all":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"سرویس {service_name} نامعتبر است"
        )
    
    try:
        if service_name == "all":
            # توقف همه سرویس‌ها
            for name, process in service_processes.items():
                if process is not None and process.is_running():
                    process.terminate()
                    service_processes[name] = None
        else:
            # توقف یک سرویس خاص
            process = service_processes.get(service_name)
            if process is not None and process.is_running():
                process.terminate()
                service_processes[service_name] = None
        
        return {
            "status": "stopped",
            "service": service_name,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در توقف سرویس: {str(e)}"
        )


@router.get("/logs/{service_name}", response_model=Dict[str, Any])
async def get_service_logs(
    service_name: str,
    lines: int = 100,
    current_user: AppUser = Depends(get_current_user)
):
    """
    دریافت لاگ‌های یک سرویس.
    
    Args:
        service_name (str): نام سرویس
        lines (int): تعداد خطوط درخواستی
        current_user (AppUser): کاربر فعلی
    
    Returns:
        Dict[str, Any]: لاگ‌های سرویس
    """
    if service_name not in service_scripts and service_name != "all":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"سرویس {service_name} نامعتبر است"
        )
    
    try:
        # مسیرهای فایل‌های لاگ
        log_files = {}
        
        if service_name == "all":
            # لاگ‌های مشترک
            log_path = f"logs/rasad_{datetime.now().strftime('%Y%m%d')}.log"
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    # خواندن آخرین خطوط
                    log_lines = f.readlines()[-lines:] if lines > 0 else f.readlines()
                    log_files["all"] = "".join(log_lines)
        else:
            # لاگ‌های سرویس خاص
            output_log_path = f"logs/{service_name}_output.log"
            error_log_path = f"logs/{service_name}_error.log"
            service_log_path = f"logs/{service_name}_{datetime.now().strftime('%Y%m%d')}.log"
            
            if os.path.exists(output_log_path):
                with open(output_log_path, "r", encoding="utf-8") as f:
                    log_lines = f.readlines()[-lines:] if lines > 0 else f.readlines()
                    log_files["output"] = "".join(log_lines)
            
            if os.path.exists(error_log_path):
                with open(error_log_path, "r", encoding="utf-8") as f:
                    log_lines = f.readlines()[-lines:] if lines > 0 else f.readlines()
                    log_files["error"] = "".join(log_lines)
            
            if os.path.exists(service_log_path):
                with open(service_log_path, "r", encoding="utf-8") as f:
                    log_lines = f.readlines()[-lines:] if lines > 0 else f.readlines()
                    log_files["service"] = "".join(log_lines)
        
        return {
            "service": service_name,
            "logs": log_files,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در دریافت لاگ‌ها: {str(e)}"
        )