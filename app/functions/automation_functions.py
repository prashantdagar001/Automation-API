import os
import webbrowser
import psutil
import subprocess
import platform

# Application Control Functions
def open_chrome(url="https://www.google.com"):
    """Open Google Chrome with an optional URL."""
    webbrowser.open(url)
    return f"Chrome opened with URL: {url}"

def open_calculator():
    """Open the calculator application."""
    if platform.system() == "Windows":
        os.system("calc")
    elif platform.system() == "Darwin":  # macOS
        os.system("open -a Calculator")
    elif platform.system() == "Linux":
        os.system("gnome-calculator")
    return "Calculator opened"

def open_notepad(filename=None):
    """Open Notepad with an optional filename."""
    if platform.system() == "Windows":
        if filename:
            os.system(f"notepad {filename}")
        else:
            os.system("notepad")
    elif platform.system() == "Darwin":  # macOS
        if filename:
            os.system(f"open -a TextEdit {filename}")
        else:
            os.system("open -a TextEdit")
    elif platform.system() == "Linux":
        if filename:
            os.system(f"gedit {filename}")
        else:
            os.system("gedit")
    return f"Notepad opened{' with file: ' + filename if filename else ''}"

# System Monitoring Functions
def get_cpu_usage():
    """Get the current CPU usage percentage."""
    cpu_percent = psutil.cpu_percent(interval=1)
    return f"Current CPU usage: {cpu_percent}%"

def get_memory_usage():
    """Get the current RAM usage information."""
    memory = psutil.virtual_memory()
    return {
        "total": f"{memory.total / (1024**3):.2f} GB",
        "available": f"{memory.available / (1024**3):.2f} GB",
        "used": f"{memory.used / (1024**3):.2f} GB",
        "percent": f"{memory.percent}%"
    }

def get_disk_usage(path="/"):
    """Get disk usage for a specified path."""
    disk = psutil.disk_usage(path)
    return {
        "total": f"{disk.total / (1024**3):.2f} GB",
        "used": f"{disk.used / (1024**3):.2f} GB",
        "free": f"{disk.free / (1024**3):.2f} GB",
        "percent": f"{disk.percent}%"
    }

def list_running_processes(limit=10):
    """List the top running processes by memory usage."""
    processes = []
    for proc in sorted(psutil.process_iter(['pid', 'name', 'memory_percent']), 
                      key=lambda x: x.info['memory_percent'], 
                      reverse=True)[:limit]:
        processes.append({
            "pid": proc.info['pid'],
            "name": proc.info['name'],
            "memory_percent": f"{proc.info['memory_percent']:.2f}%"
        })
    return processes

# Command Execution Functions
def run_command(command):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(command, shell=True, check=True, 
                               capture_output=True, text=True)
        return {
            "success": True,
            "output": result.stdout,
            "command": command
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "error": e.stderr,
            "command": command
        }

def create_directory(path):
    """Create a directory at the specified path."""
    try:
        os.makedirs(path, exist_ok=True)
        return f"Directory created at: {path}"
    except Exception as e:
        return f"Failed to create directory: {str(e)}"

def list_directory_contents(path="."):
    """List contents of a directory."""
    try:
        files = os.listdir(path)
        return {
            "path": os.path.abspath(path),
            "items": files,
            "count": len(files)
        }
    except Exception as e:
        return f"Failed to list directory contents: {str(e)}" 