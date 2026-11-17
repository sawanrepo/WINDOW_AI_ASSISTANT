#later it will be updated to take screenshot of background running app too . 
#currently it will take ss of chat window with assistant.
from PIL import ImageGrab
import os
from datetime import datetime
import tkinter as tk
import threading
import time

def flash_screen():
    try:
        root = tk.Tk()
        root.attributes("-fullscreen", True)
        root.attributes("-topmost", True)
        root.configure(background='white')
        root.attributes("-alpha", 0.3)
        # Safely schedule destroy on the Tkinter mainloop thread instead of a worker thread
        root.after(100, root.destroy)
        root.mainloop()
    except Exception:
        pass

def take_screenshot_tool():
    try:
        # Launch flash as a daemon thread so it never blocks process termination
        flash_thread = threading.Thread(target=flash_screen, daemon=True)
        flash_thread.start()
        time.sleep(0.15)

        user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
        screenshots_dir = os.path.join(user_profile, "OneDrive", "Pictures", "Screenshots")
        if not os.path.exists(screenshots_dir):
            screenshots_dir = os.path.join(user_profile, "Pictures", "Screenshots")

        try:
            os.makedirs(screenshots_dir, exist_ok=True)
        except Exception:
            # Fallback to local screenshots folder if user profile pictures is restricted
            screenshots_dir = os.path.join(os.getcwd(), "screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"Screenshot_{timestamp}.png"
        save_path = os.path.join(screenshots_dir, filename)
        screenshot = ImageGrab.grab()
        screenshot.save(save_path)

        return {
            "status": "success",
            "message": f"Screenshot saved to {save_path}",
            "file_path": save_path
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to take screenshot: {str(e)}",
            "file_path": None
        }
