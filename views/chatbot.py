import customtkinter as ctk
import threading
from datetime import datetime
from ai.assistant import ask_assistant, get_startup_nudges
from ai import chat_history
from assets.icon_loader import get_icon
import session

class ChatbotPage(ctk.CTkFrame):
    QUICK_ACTIONS = {"Quick Actions": None, "Check Balance": "check my balance", 
                     "Deposit Money": "I want to deposit money", "Withdraw Money": "I want to withdraw money",
                     "Transfer Money": "I want to transfer money", "View Transactions": "show my transactions",
                     "Apply for Loan": "I want a loan"}
    ACTION_TO_METHOD = {"balance": "show_dashboard", "deposit": "show_deposit", "withdraw": "show_withdraw",
                        "transfer": "show_transfer", "transactions": "show_transactions", "loan": "show_loans"}
    FAQ_CARDS = [{"label": "💰 Check Balance", "message": "check my balance"},
                 {"label": "💵 Deposit Money", "message": "I want to deposit money"},
                 {"label": "🔁 Transfer Money", "message": "I want to transfer money"},
                 {"label": "📈 Largest Transaction", "message": "what is my largest transaction"}]

    def __init__(self, master):
        super().__init__(master)
        self.configure(fg_color="transparent")
        self.grid_rowconfigure((0,1), weight=0); self.grid_rowconfigure(2, weight=1, minsize=120)
        self.grid_rowconfigure((3,4), weight=0); self.grid_columnconfigure(0, weight=1)
        
        # Title with Milo avatar
        title_row = ctk.CTkFrame(self, fg_color="transparent")
        title_row.grid(row=0, column=0, pady=20)
        robot_icon = get_icon("robot", size=36)
        (ctk.CTkLabel(title_row, image=robot_icon, text="").pack(side="left", padx=(0,10)) if robot_icon 
         else ctk.CTkLabel(title_row, text="🤖", font=("Arial", 28)).pack(side="left", padx=(0,10)))
        ctk.CTkLabel(title_row, text="SmartBank AI Assistant", font=("Arial", 28, "bold")).pack(side="left")
        
        # FAQ cards
        self.faq_wrap = ctk.CTkFrame(self, fg_color="transparent")
        self.faq_wrap.grid(row=1, column=0, sticky="ew", padx=15, pady=(0,10))
        self.faq_wrap.grid_columnconfigure((0,1), weight=1)
        for i, card in enumerate(self.FAQ_CARDS):
            ctk.CTkButton(self.faq_wrap, text=card["label"], height=44, corner_radius=12,
                         fg_color="#EEF2FF", text_color="#1E3A8A", hover_color="#E0E7FF",
                         font=("Arial", 13), command=lambda msg=card["message"]: self.send_message(preset_text=msg)
                         ).grid(row=i//2, column=i%2, padx=6, pady=6, sticky="ew")
        self._faq_visible = True
        
        # Chat Box
        self.chat_box = ctk.CTkTextbox(self, font=("Arial", 16), wrap="word")
        self.chat_box.grid(row=2, column=0, padx=15, pady=(5,5), sticky="nsew")
        for tag, color, justify in [("user", "#1E3A8A", "right"), ("milo", "#111827", "left"),
                                    ("timestamp_user", "#9CA3AF", "right"), ("timestamp_milo", "#9CA3AF", "left")]:
            self.chat_box.tag_config(tag, foreground=color, justify=justify)
        
        self._load_previous_conversation()
        self.chat_box.configure(state="disabled")
        if self._had_history: self._hide_faq_cards()
        
        # Typing indicator
        self.typing_label = ctk.CTkLabel(self, text="", font=("Arial", 13), text_color="#6B7280", anchor="w")
        self.typing_label.grid(row=3, column=0, padx=20, sticky="w")
        self._typing_after_id = self._typing_active = self._typing_dots = 0
        
        # Bottom Frame
        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=4, column=0, padx=20, pady=(5,25), sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.entry = ctk.CTkEntry(input_frame, placeholder_text="Ask Milo AI...")
        self.entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.entry.bind("<Return>", lambda e: self.send_message())
        
        self.quick_actions_var = ctk.StringVar(value="Quick Actions")
        self.quick_actions_menu = ctk.CTkOptionMenu(input_frame, values=list(self.QUICK_ACTIONS.keys()),
                                                    variable=self.quick_actions_var, command=self.handle_quick_action, width=170)
        self.quick_actions_menu.grid(row=0, column=1, padx=(0,10), pady=10)
        
        self.send_button = ctk.CTkButton(input_frame, text="Send", command=self.send_message)
        self.send_button.grid(row=0, column=2, padx=10)
        self.current_action = None

    def _load_previous_conversation(self):
        username = session.current_user[2] if session.current_user and len(session.current_user) > 2 else None
        history = chat_history.load_history(username) if username else []
        self._had_history = bool(history)
        
        if not history:
            self.chat_box.insert("end", "🤖 Milo AI:\nHello! I am Milo, your SmartBank AI Assistant.\nHow can I help you today?\n\n", "milo")
        else:
            for entry in history[-20:]:
                is_user = entry["role"] == "user"
                self.chat_box.insert("end", f"{'👤 You' if is_user else '🤖 Milo AI'}:\n{entry['text']}\n\n", "user" if is_user else "milo")
        
        for nudge in get_startup_nudges():
            self.chat_box.insert("end", f"🤖 Milo AI:\n{nudge}\n\n", "milo")
        self.chat_box.see("end")

    def add_message(self, message, tag="milo"):
        was_near_bottom = self._is_near_bottom()
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", message + "\n", tag)
        timestamp_tag = "timestamp_user" if tag == "user" else "timestamp_milo"
        self.chat_box.insert("end", f"{datetime.now().strftime('%I:%M %p')}\n\n", timestamp_tag)
        if tag == "user" or was_near_bottom: self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def _is_near_bottom(self):
        try: return self.chat_box.yview()[1] >= 0.98
        except: return True

    def _start_typing_indicator(self):
        self._typing_active = True
        self._typing_dots = 0
        self._animate_typing()

    def _animate_typing(self):
        if not self._typing_active: return
        self.typing_label.configure(text=f"🤖 Milo is typing{'.' * (self._typing_dots % 4)}")
        self._typing_dots += 1
        self._typing_after_id = self.after(400, self._animate_typing)

    def _stop_typing_indicator(self):
        self._typing_active = False
        if self._typing_after_id: self.after_cancel(self._typing_after_id)
        self._typing_after_id = None
        self.typing_label.configure(text="")

    def handle_quick_action(self, choice):
        message = self.QUICK_ACTIONS.get(choice)
        self.quick_actions_var.set("Quick Actions")
        if message: self.send_message(preset_text=message)

    def send_message(self, preset_text=None):
        message = preset_text if preset_text is not None else self.entry.get().strip()
        if not message: return
        if preset_text is None: self.entry.delete(0, "end")
        self._hide_faq_cards()
        self.add_message(f"👤 You:\n{message}", "user")
        self.send_button.configure(state="disabled")
        self._start_typing_indicator()
        threading.Thread(target=self.get_ai_response, args=(message,), daemon=True).start()

    def _hide_faq_cards(self):
        if self._faq_visible:
            self.faq_wrap.grid_remove()
            self._faq_visible = False

    def get_ai_response(self, message):
        try:
            response = ask_assistant(message)
            reply, action = response["reply"], response["action"]
        except Exception as e:
            print(f"[Assistant error] {type(e).__name__}: {e}")
            reply, action = "Sorry, something went wrong. Please try again.", None
        self.after(0, lambda: self.finish_response(reply, action))

    def finish_response(self, reply, action):
        self._stop_typing_indicator()
        self.add_message(f"🤖 Milo AI:\n{reply}", "milo")
        self.send_button.configure(state="normal")
        self.current_action = action
        if action:
            self.add_message("🤖 Milo AI:\nOpening that for you now...", "milo")
            self.after(500, self.perform_action)

    def perform_action(self):
        if not self.current_action: return
        method_name = self.ACTION_TO_METHOD.get(self.current_action)
        app_layout = getattr(getattr(self, "master", None), "master", None)
        if method_name and app_layout and hasattr(app_layout, method_name):
            getattr(app_layout, method_name)()
        else:
            print(f"Could not navigate for action: {self.current_action}")