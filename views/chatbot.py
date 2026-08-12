import customtkinter as ctk
import threading
from datetime import datetime

from ai.assistant import ask_assistant, get_startup_nudges
from ai import chat_history
from assets.icon_loader import get_icon
import session


class ChatbotPage(ctk.CTkFrame):

    QUICK_ACTIONS = {
        "Quick Actions": None,
        "Check Balance": "check my balance",
        "Deposit Money": "I want to deposit money",
        "Withdraw Money": "I want to withdraw money",
        "Transfer Money": "I want to transfer money",
        "View Transactions": "show my transactions",
        "Apply for Loan": "I want a loan",
    }

    ACTION_TO_METHOD = {
        "balance": "show_dashboard",
        "deposit": "show_deposit",
        "withdraw": "show_withdraw",
        "transfer": "show_transfer",
        "transactions": "show_transactions",
        "loan": "show_loans",
    }

    def __init__(self, master):
        super().__init__(master)

        self.configure(fg_color="transparent")

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1, minsize=120)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # =========================
        # Title with Milo avatar
        # =========================
        title_row = ctk.CTkFrame(self, fg_color="transparent")
        title_row.grid(row=0, column=0, pady=20)

        robot_icon = get_icon("robot", size=36)  # keep robot for Milo; bank_logo is used on Dashboard/Login/Register
        if robot_icon:
            ctk.CTkLabel(title_row, image=robot_icon, text="").pack(side="left", padx=(0, 10))
        else:
            ctk.CTkLabel(title_row, text="🤖", font=("Arial", 28)).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            title_row,
            text="SmartBank AI Assistant",
            font=("Arial", 28, "bold")
        ).pack(side="left")

        # Chat Box -- sticky="nsew" + row weight=1 lets this grow/shrink
        # with the window instead of staying a fixed size.
        self.chat_box = ctk.CTkTextbox(self, font=("Arial", 16), wrap="word")
        self.chat_box.grid(row=1, column=0, padx=15, pady=(5, 5), sticky="nsew")

        # Color-coded, aligned "bubbles": your messages lean right in
        # blue, Milo's lean left in dark gray, timestamps are small and
        # muted -- gives a real chat feel without rebuilding the widget.
        self.chat_box.tag_config("user", foreground="#1E3A8A", justify="right")
        self.chat_box.tag_config("milo", foreground="#111827", justify="left")
        self.chat_box.tag_config("timestamp_user", foreground="#9CA3AF", justify="right")
        self.chat_box.tag_config("timestamp_milo", foreground="#9CA3AF", justify="left")

        self._load_previous_conversation()

        self.chat_box.configure(state="disabled")

        # =========================
        # Typing indicator
        # =========================
        self.typing_label = ctk.CTkLabel(
            self,
            text="",
            font=("Arial", 13),
            text_color="#6B7280",
            anchor="w"
        )
        self.typing_label.grid(row=2, column=0, padx=20, sticky="w")
        self._typing_after_id = None
        self._typing_active = False
        self._typing_dots = 0

        # Bottom Frame -- lifted slightly off the very bottom edge via
        # the larger bottom pady, instead of sitting flush against it.
        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=3, column=0, padx=20, pady=(5, 25), sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(input_frame, placeholder_text="Ask Milo AI...")
        self.entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.entry.bind("<Return>", lambda event: self.send_message())

        self.quick_actions_var = ctk.StringVar(value="Quick Actions")
        self.quick_actions_menu = ctk.CTkOptionMenu(
            input_frame,
            values=list(self.QUICK_ACTIONS.keys()),
            variable=self.quick_actions_var,
            command=self.handle_quick_action,
            width=170
        )
        self.quick_actions_menu.grid(row=0, column=1, padx=(0, 10), pady=10)

        self.send_button = ctk.CTkButton(input_frame, text="Send", command=self.send_message)
        self.send_button.grid(row=0, column=2, padx=10)

        self.current_action = None

    # -----------------------------------
    # Load previous conversation (or show greeting if first time)
    # -----------------------------------
    def _load_previous_conversation(self):
        username = None
        try:
            username = session.current_user[2]
        except (TypeError, IndexError):
            pass

        history = chat_history.load_history(username) if username else []

        if not history:
            self.chat_box.insert(
                "end",
                "🤖 Milo AI:\n"
                "Hello! I am Milo, your SmartBank AI Assistant.\n"
                "How can I help you today?\n\n",
                "milo"
            )
        else:
            # Show the last 20 messages so the page doesn't get overwhelming
            for entry in history[-20:]:
                is_user = entry["role"] == "user"
                speaker = "👤 You" if is_user else "🤖 Milo AI"
                self.chat_box.insert(
                    "end",
                    f"{speaker}:\n{entry['text']}\n\n",
                    "user" if is_user else "milo"
                )

        for nudge in get_startup_nudges():
            self.chat_box.insert("end", f"🤖 Milo AI:\n{nudge}\n\n", "milo")

        # Always open with the most recent message in view.
        self.chat_box.see("end")

    # -----------------------------------
    # Add Message
    # -----------------------------------
    def add_message(self, message, tag="milo"):
        was_near_bottom = self._is_near_bottom()

        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", message + "\n", tag)

        timestamp = datetime.now().strftime("%I:%M %p")
        timestamp_tag = "timestamp_user" if tag == "user" else "timestamp_milo"
        self.chat_box.insert("end", f"{timestamp}\n\n", timestamp_tag)

        # Don't yank the view down if the person deliberately scrolled up
        # to reread something -- but always scroll for their own message
        # (that's the thing they just did) or if they were already
        # sitting at the bottom.
        if tag == "user" or was_near_bottom:
            self.chat_box.see("end")

        self.chat_box.configure(state="disabled")

    def _is_near_bottom(self):
        try:
            return self.chat_box.yview()[1] >= 0.98
        except Exception:
            return True

    # -----------------------------------
    # Typing indicator
    # -----------------------------------
    def _start_typing_indicator(self):
        self._typing_active = True
        self._typing_dots = 0
        self._animate_typing()

    def _animate_typing(self):
        if not self._typing_active:
            return
        dots = "." * (self._typing_dots % 4)
        self.typing_label.configure(text=f"🤖 Milo is typing{dots}")
        self._typing_dots += 1
        self._typing_after_id = self.after(400, self._animate_typing)

    def _stop_typing_indicator(self):
        self._typing_active = False
        if self._typing_after_id:
            self.after_cancel(self._typing_after_id)
            self._typing_after_id = None
        self.typing_label.configure(text="")

    # -----------------------------------
    # Quick Actions Dropdown Handler
    # -----------------------------------
    def handle_quick_action(self, choice):
        message = self.QUICK_ACTIONS.get(choice)
        self.quick_actions_var.set("Quick Actions")

        if not message:
            return

        self.send_message(preset_text=message)

    # -----------------------------------
    # Send Message
    # -----------------------------------
    def send_message(self, preset_text=None):
        message = preset_text if preset_text is not None else self.entry.get().strip()

        if not message:
            return

        if preset_text is None:
            self.entry.delete(0, "end")

        self.add_message(f"👤 You:\n{message}", "user")
        self.send_button.configure(state="disabled")
        self._start_typing_indicator()

        threading.Thread(
            target=self.get_ai_response,
            args=(message,),
            daemon=True
        ).start()

    # -----------------------------------
    # AI Response
    # -----------------------------------
    def get_ai_response(self, message):
        # Never let a failure here (a DB hiccup, an unexpected error deep
        # in the assistant, etc.) leave the thread dead and the Send
        # button permanently disabled -- always resolve to *something*.
        try:
            response = ask_assistant(message)
            reply = response["reply"]
            action = response["action"]
        except Exception as e:
            print(f"[Assistant error] {type(e).__name__}: {e}")
            reply = (
                "Sorry, something went wrong on my end processing that. "
                "Please try again in a moment."
            )
            action = None

        self.after(0, lambda: self.finish_response(reply, action))

    # -----------------------------------
    # Finish Response
    # -----------------------------------
    def finish_response(self, reply, action):
        self._stop_typing_indicator()
        self.add_message(f"🤖 Milo AI:\n{reply}", "milo")
        self.send_button.configure(state="normal")
        self.current_action = action

        if action:
            self.add_message("🤖 Milo AI:\nOpening that for you now...", "milo")
            self.after(500, self.perform_action)

    # -----------------------------------
    # Perform Action
    # -----------------------------------
    def perform_action(self):
        if not self.current_action:
            return

        method_name = self.ACTION_TO_METHOD.get(self.current_action)

        app_layout = getattr(self, "master", None)
        app_layout = getattr(app_layout, "master", None)

        if method_name and app_layout is not None and hasattr(app_layout, method_name):
            getattr(app_layout, method_name)()
        else:
            print(f"Could not navigate for action: {self.current_action}")