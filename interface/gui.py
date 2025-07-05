import customtkinter as ctk
import threading
from agent.graph import winora_agent, system_prompt
from langchain_core.messages import HumanMessage, SystemMessage
from speech import speak, listen


class WinoraGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Winora - Windows AI Assistant")
        self.root.geometry("900x600")
        self.waiting_for_reply = False

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.chat_display = ctk.CTkTextbox(
            master=root,
            height=450,
            width=850,
            font=("Consolas", 12),
            wrap="word",
            activate_scrollbars=True,
            state='disabled',
            fg_color="#1e1e2e",
            text_color="#e0e0e0"
        )
        self.chat_display.pack(padx=10, pady=(10, 5))

        input_frame = ctk.CTkFrame(root, fg_color="#2a2a3a")
        input_frame.pack(fill="x", padx=10, pady=(5, 0))

        self.user_input = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type your message...",
            width=580,
            text_color="#ffffff",
            fg_color="#3b3b5c",
        )
        self.user_input.pack(side="left", padx=(0, 10), pady=10)
        self.user_input.bind("<Return>", self.send_message)

        self.send_button = ctk.CTkButton(
            input_frame, text="➤", width=50, command=self.send_message
        )
        self.send_button.pack(side="left", padx=5)

        self.mic_button = ctk.CTkButton(
            input_frame, text="🎤", width=50, command=self.listen_and_send
        )
        self.mic_button.pack(side="left", padx=5)

        self.theme_toggle = ctk.CTkSwitch(
            root, text="Dark Mode", command=self.toggle_mode
        )
        self.theme_toggle.pack(anchor="e", padx=15, pady=(0, 10))
        self.theme_toggle.select()

        self.chat_history = []

    def toggle_mode(self):
        if self.theme_toggle.get() == 1:
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")

    def send_message(self, event=None):
        if self.waiting_for_reply:
            return

        user_text = self.user_input.get().strip()
        if not user_text:
            return

        self.waiting_for_reply = True
        self.append_chat("🧑 You", user_text, name_color="#89b4fa", msg_color="#ffffff")
        self.user_input.delete(0, "end")

        threading.Thread(target=self.get_response, args=(user_text,), daemon=True).start()

    def get_response(self, user_text):
        try:
            if not self.chat_history:
                self.chat_history.append(SystemMessage(content=system_prompt))

            self.chat_history.append(HumanMessage(content=user_text))
            state = {"messages": self.chat_history}
            result = winora_agent.invoke(state)

            latest_msg = result["messages"][-1]
            self.chat_history = result["messages"]
            response = latest_msg.content if hasattr(latest_msg, "content") else str(latest_msg)
        except Exception as e:
            response = f"[Error] {str(e)}"

        self.root.after(0, lambda: self.append_chat("🤖 Winora", response, name_color="#00d4aa", msg_color="#dddddd"))
        threading.Thread(target=speak, args=(response,), daemon=True).start()
        self.waiting_for_reply = False

    def append_chat(self, speaker, message, name_color, msg_color):
        self.chat_display.configure(state='normal')
        self.chat_display.insert("end", f"{speaker}:\n")
        self.chat_display.tag_add(f"{speaker}_name", "end-2l", "end-1l")
        self.chat_display.tag_config(f"{speaker}_name", foreground=name_color)
        self.chat_display.insert("end", f"{message}\n\n")
        self.chat_display.tag_add(f"{speaker}_msg", "end-3l", "end-1l")
        self.chat_display.tag_config(f"{speaker}_msg", foreground=msg_color)

        self.chat_display.configure(state='disabled')
        self.chat_display.yview("end")

    def listen_and_send(self):
        if self.waiting_for_reply:
            return

        def task():
            self.waiting_for_reply = True
            self.append_chat("🤖 Winora", "🎙️ Listening...", name_color="#00d4aa", msg_color="#aaaaaa")
            text = listen().strip()
            if text and text.lower() not in ["", "didn't catch that clearly.", "mic error.", "error recognizing speech."]:
                self.append_chat("🧑 You", text, name_color="#89b4fa", msg_color="#ffffff")
                self.user_input.delete(0, "end")
                threading.Thread(target=self.get_response, args=(text,), daemon=True).start()
            else:
                self.append_chat("🤖 Winora", "❌ Didn't hear you clearly. Please try again.",
                                 name_color="#00d4aa", msg_color="#aaaaaa")
                self.waiting_for_reply = False
        threading.Thread(target=task, daemon=True).start()


def launch_gui():
    root = ctk.CTk()
    app = WinoraGUI(root)
    root.mainloop()