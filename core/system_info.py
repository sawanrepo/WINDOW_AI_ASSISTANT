import psutil

def get_system_status(requested: list[str]) -> dict:
    
    result = {}

    if "cpu" in requested:
        cpu_info = {
            "logical_cpus": psutil.cpu_count(logical=True),
            "physical_cpus": psutil.cpu_count(logical=False),
            "cpu_usage_percent": psutil.cpu_percent(interval=1),
        }
        result["cpu"] = cpu_info

    if "ram" in requested:
        virtual_mem = psutil.virtual_memory()
        ram_info = {
            "total_gb": round(virtual_mem.total / (1024 ** 3), 2),
            "used_gb": round(virtual_mem.used / (1024 ** 3), 2),
            "available_gb": round(virtual_mem.available / (1024 ** 3), 2),
            "ram_usage_percent": virtual_mem.percent,
        }
        result["ram"] = ram_info

    if "battery" in requested:
        battery = psutil.sensors_battery()
        if battery:
            battery_info = {
                "battery_percent": battery.percent,
                "charging": battery.power_plugged,
                "secs_left": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None,
            }
            result["battery"] = battery_info
        else:
            result["battery"] = None

    return result