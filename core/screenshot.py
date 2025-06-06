#later it will be updated to take screenshot of background running app too . 
#currently it will take ss of chat window with assistant.
from PIL import ImageGrab
import os
from datetime import datetime
import tkinter as tk
import threading
import time

def flash_screen():
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.configure(background='white')
    root.attributes("-alpha", 0.3) 
    threading.Timer(0.1, root.destroy).start()
    root.mainloop()

def take_screenshot_tool():
    try:
        flash_thread = threading.Thread(target=flash_screen)
        flash_thread.start()
        time.sleep(0.15)
        user_profile = os.environ["USERPROFILE"]
        screenshots_dir = os.path.join(user_profile, "OneDrive", "Pictures", "Screenshots")
        if not os.path.exists(screenshots_dir):
            screenshots_dir = os.path.join(user_profile, "Pictures", "Screenshots")

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