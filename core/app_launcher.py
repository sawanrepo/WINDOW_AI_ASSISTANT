import os
import subprocess
import re

def get_uwp_apps():
    """Fetch installed UWP apps (Name, AppID) dynamically."""
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-StartApps | Format-Table -HideTableHeaders -Property Name,AppID"],
            capture_output=True, text=True, check=True
        )
        lines = result.stdout.strip().splitlines()
        apps = []
        for line in lines:
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) >= 2:
                name = parts[0].strip()
                appid = parts[1].strip()
                apps.append((name, appid))
        return apps
    except Exception as e:
        print(f"Failed to fetch UWP apps: {e}")
        return []

def name_matches(filename: str, app_name: str) -> bool:
    """Stricter matching to avoid false positives."""
    base = os.path.splitext(filename)[0].lower()
    app_name = app_name.lower()

    if base == app_name:
        return True
    if base.startswith(app_name + " "):
        return True
    pattern = r'\b' + re.escape(app_name) + r'\b'
    return re.search(pattern, base) is not None

def launch_uwp_app(app_name):
    apps = get_uwp_apps()
    app_name_lower = app_name.lower()
    for name, appid in apps:
        if app_name_lower in name.lower():
            try:
                subprocess.run(f'start shell:AppsFolder\\{appid}', shell=True, check=True)
                return {"status": "success", "message": f"Launched UWP app: {name}"}
            except Exception as e:
                if "permission" in str(e).lower():
                    return {"status": "permission_denied", "message": "This app requires administrator permissions."}
                return {"status": "error", "message": f"Failed to launch UWP app: {e}"}
    return {"status": "not_found", "message": "No matching UWP app found."}

def launch_app(app_name: str) -> dict:
    result = launch_uwp_app(app_name)
    if result["status"] == "success" or result["status"] == "permission_denied":
        return result
    start_menu_paths = [
        os.path.join(os.environ.get("PROGRAMDATA", ""), "Microsoft\\Windows\\Start Menu\\Programs"),
        os.path.join(os.environ.get("APPDATA", ""), "Microsoft\\Windows\\Start Menu\\Programs")
    ]
    for path in start_menu_paths:
        if not path or not os.path.isdir(path):
            continue
        for root, _, files in os.walk(path):
            for file in files:
                if file.lower().endswith(".lnk") and app_name.lower() in file.lower():
                    full_path = os.path.join(root, file)
                    try:
                        os.startfile(full_path)
                        return {"status": "success", "message": f"Launched shortcut: {file.replace('.lnk','')}"}
                    except PermissionError:
                        return {"status": "permission_denied", "message": "This app requires administrator permissions."}
                    except Exception:
                        continue
    path_dirs = os.environ.get('PATH', '').split(os.pathsep)
    pathext_str = os.environ.get('PATHEXT', '.EXE;.COM;.BAT;.CMD')
    exts = [ext.lower() for ext in pathext_str.split(os.pathsep) if ext.strip()]
    if not exts:
        exts = ['.exe', '.com', '.bat', '.cmd']

    for dir in path_dirs:
        dir = dir.strip()
        if not dir or not os.path.isdir(dir):
            continue
        exact_path = os.path.join(dir, app_name)
        if os.path.isfile(exact_path):
            try:
                os.startfile(exact_path)
                return {"status": "success", "message": f"Launched executable from PATH: {app_name}"}
            except PermissionError:
                return {"status": "permission_denied", "message": "This app requires administrator permissions."}
            except Exception:
                pass
        if '.' not in app_name:
            for ext in exts:
                full_path = os.path.join(dir, app_name + ext)
                if os.path.isfile(full_path) and name_matches(os.path.basename(full_path), app_name):
                    try:
                        os.startfile(full_path)
                        return {"status": "success", "message": f"Launched executable from PATH: {full_path}"}
                    except PermissionError:
                        return {"status": "permission_denied", "message": "This app requires administrator permissions."}
                    except Exception:
                        continue
    program_dirs = [
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        os.environ.get("LOCALAPPDATA", "")
    ]
    for base_dir in program_dirs:
        if not base_dir or not os.path.isdir(base_dir):
            continue
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.lower().endswith(".exe") and name_matches(file, app_name):
                    full_path = os.path.join(root, file)
                    try:
                        os.startfile(full_path)
                        return {"status": "success", "message": f"Launched executable from Program Folders: {full_path}"}
                    except PermissionError:
                        return {"status": "permission_denied", "message": "This app requires administrator permissions."}
                    except Exception:
                        continue
    return {"status": "not_found", "message": "App not found. It might be in a custom folder or not installed."}

if __name__ == "__main__":
    app_to_launch = input("Enter app name: ")
    result = launch_app(app_to_launch)
    print(result["message"])