import tkinter as tk
from tkinter import scrolledtext
import threading

from agent.graph import winora_agent, system_prompt
from langchain_core.messages import HumanMessage, SystemMessage


class WinoraGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Winora - Windows AI Assistant")

        # Chat display area
        self.chat_display = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, height=25, width=80, state='disabled', font=("Consolas", 11)
        )
        self.chat_display.pack(padx=10, pady=10)

        # Input field
        self.user_input = tk.Entry(root, width=70, font=("Arial", 12))
        self.user_input.pack(side=tk.LEFT, padx=(10, 0), pady=(0, 10))
        self.user_input.bind("<Return>", self.send_message)

        # Send button
        self.send_button = tk.Button(root, text="Send", command=self.send_message, width=10)
        self.send_button.pack(side=tk.LEFT, padx=(5, 10), pady=(0, 10))

        self.chat_history = []  # To keep track of last N messages

    def send_message(self, event=None):
        user_text = self.user_input.get().strip()
        if not user_text:
            return
        self.append_chat("You", user_text)
        self.user_input.delete(0, tk.END)
        threading.Thread(target=self.get_response, args=(user_text,), daemon=True).start()

    def get_response(self, user_text):
        try:
            # Inject system message on first turn only
            if not self.chat_history:
                self.chat_history.append(SystemMessage(content=system_prompt))

            self.chat_history.append(HumanMessage(content=user_text))
            state = {"messages": self.chat_history}
            result = winora_agent.invoke(state)

            latest_msg = result["messages"][-1]
            self.chat_history = result["messages"]  # update memory

            response = latest_msg.content if hasattr(latest_msg, "content") else str(latest_msg)
        except Exception as e:
            response = f"[Error] {str(e)}"
        self.append_chat("Winora", response)

    def append_chat(self, speaker, message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{speaker}: {message}\n\n")
        self.chat_display.config(state='disabled')
        self.chat_display.yview(tk.END)


def launch_gui():
    root = tk.Tk()
    app = WinoraGUI(root)
    root.mainloop()