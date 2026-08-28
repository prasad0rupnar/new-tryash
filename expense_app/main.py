"""
Expense AI - Mobile App (Kivy)
A mobile-friendly rebuild of ass3.py. Same chatbot + features, touch UI.
No paid APIs or services are used anywhere in this app.
"""
import os

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.utils import platform

from logic import ExpenseStore, ExpenseManager, Chatbot

Window.clearcolor = (0.12, 0.12, 0.18, 1)


def get_data_dir():
    """Pick a writable, persistent storage folder on any platform."""
    try:
        from kivy.app import App as _App
        app = _App.get_running_app()
        if app is not None:
            return app.user_data_dir
    except Exception:
        pass
    return os.path.join(os.path.expanduser("~"), ".expense_ai")


class ChatBubble(Label):
    def __init__(self, text, sender, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.markup = False
        self.size_hint_y = None
        self.size_hint_x = 0.85
        self.pos_hint = {"right": 1} if sender == "user" else {"x": 0}
        self.halign = "left"
        self.valign = "middle"
        self.padding = (dp(12), dp(10))
        self.color = (1, 1, 1, 1)
        with self.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(*( (0.30, 0.69, 0.31, 1) if sender == "user" else (0.18, 0.19, 0.26, 1) ))
            self.bg = RoundedRectangle(radius=[dp(12)])
        self.bind(pos=self._update_bg, size=self._update_bg, texture_size=self._update_height)

    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def _update_height(self, *args):
        self.text_size = (self.width * 0.92, None)
        self.texture_update()
        self.height = self.texture_size[1] + dp(20)


class ConfirmPopup(Popup):
    def __init__(self, message, on_yes, **kwargs):
        super().__init__(title="Confirm", size_hint=(0.8, 0.35), **kwargs)
        layout = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        layout.add_widget(Label(text=message))
        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))

        def yes(_):
            on_yes()
            self.dismiss()

        btn_row.add_widget(Button(text="Yes", on_release=yes))
        btn_row.add_widget(Button(text="No", on_release=lambda _: self.dismiss()))
        layout.add_widget(btn_row)
        self.content = layout


class ExpenseApp(App):
    def build(self):
        self.title = "Expense AI"
        data_dir = get_data_dir()
        self.store = ExpenseStore(data_dir)
        self.mgr = ExpenseManager(self.store)
        self.bot = Chatbot(self.mgr)

        root = BoxLayout(orientation="vertical")

        # ---- Chat area ----
        self.chat_scroll = ScrollView(size_hint=(1, 1))
        self.chat_box = GridLayout(cols=1, size_hint_y=None, spacing=dp(6), padding=dp(10))
        self.chat_box.bind(minimum_height=self.chat_box.setter("height"))
        self.chat_scroll.add_widget(self.chat_box)
        root.add_widget(self.chat_scroll)

        # ---- Quick action buttons (scrollable row) ----
        actions_scroll = ScrollView(size_hint=(1, None), height=dp(56), do_scroll_y=False)
        actions = BoxLayout(size_hint=(None, 1), spacing=dp(6), padding=(dp(6), dp(6)))
        actions.bind(minimum_width=actions.setter("width"))

        buttons = [
            ("📋 Expenses", lambda: self.bot_say(self.mgr.show_expenses())),
            ("📊 Summary", lambda: self.bot_say(self.mgr.show_summary())),
            ("📅 Today", lambda: self.bot_say(self.mgr.filter_by_date("today"))),
            ("📆 Month", lambda: self.bot_say(self.mgr.filter_by_date("month"))),
            ("🎯 Budget", self.ask_budget),
            ("📈 Graph", self.show_graph),
            ("🗑 Clear All", self.confirm_clear),
        ]
        for label, cb in buttons:
            b = Button(text=label, size_hint=(None, 1), width=dp(120),
                       background_color=(0.23, 0.24, 0.36, 1))
            b.bind(on_release=lambda inst, cb=cb: cb())
            actions.add_widget(b)
        actions_scroll.add_widget(actions)
        root.add_widget(actions_scroll)

        # ---- Text input row ----
        input_row = BoxLayout(size_hint=(1, None), height=dp(56), padding=dp(8), spacing=dp(8))
        self.text_input = TextInput(hint_text="Type e.g. 'spent 200 on food'",
                                     multiline=False, size_hint=(0.8, 1))
        self.text_input.bind(on_text_validate=self.on_send)
        send_btn = Button(text="Send", size_hint=(0.2, 1),
                           background_color=(0.30, 0.69, 0.31, 1))
        send_btn.bind(on_release=self.on_send)
        input_row.add_widget(self.text_input)
        input_row.add_widget(send_btn)
        root.add_widget(input_row)

        # ---- Welcome messages ----
        self.bot_say("👋 Welcome! I'm your Expense Assistant.")
        self.bot_say("💡 Type 'help', or use the buttons above.")
        self.bot_say(self.mgr.daily_reminder())

        return root

    # ---------- Chat helpers ----------
    def user_say(self, text):
        self.chat_box.add_widget(ChatBubble(text, "user"))
        self._scroll_bottom()

    def bot_say(self, text):
        self.chat_box.add_widget(ChatBubble(text, "bot"))
        self._scroll_bottom()

    def _scroll_bottom(self, *args):
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: setattr(self.chat_scroll, "scroll_y", 0), 0.05)

    def on_send(self, *args):
        text = self.text_input.text.strip()
        if not text:
            return
        self.user_say(text)
        self.text_input.text = ""
        reply = self.bot.respond(text)

        if reply == "CONFIRM_CLEAR":
            self.confirm_clear()
        elif reply == "EXIT":
            self.bot_say("Goodbye! 👋 (Close the app to exit)")
        else:
            self.bot_say(reply)

    # ---------- Actions ----------
    def confirm_clear(self):
        def do_clear():
            self.bot_say(self.mgr.clear_all())
        ConfirmPopup("Are you sure you want to delete ALL expenses?", do_clear).open()

    def ask_budget(self):
        layout = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        inp = TextInput(hint_text="Enter monthly budget (₹)", input_filter="int",
                         multiline=False, size_hint_y=None, height=dp(44))
        layout.add_widget(Label(text="Set your monthly budget"))
        layout.add_widget(inp)
        popup = Popup(title="🎯 Set Budget", content=layout, size_hint=(0.8, 0.35))

        def save(_):
            if inp.text.strip():
                amount = int(inp.text.strip())
                if amount > 0:
                    self.store.save_budget(amount)
                    self.bot_say(f"🎯 Budget set to ₹{amount}! I'll alert you when you're close.")
                popup.dismiss()

        inp.bind(on_text_validate=save)
        btn = Button(text="Save", size_hint_y=None, height=dp(44))
        btn.bind(on_release=save)
        layout.add_widget(btn)
        popup.open()

    def show_graph(self):
        data = self.mgr.category_totals()
        if not data:
            self.bot_say("📊 No data for graph yet.")
            return

        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(5, 5))
        ax.pie(data.values(), labels=data.keys(), autopct="%1.1f%%")
        ax.set_title("Expense Distribution")
        img_path = os.path.join(get_data_dir(), "graph.png")
        fig.savefig(img_path, facecolor="white")
        plt.close(fig)

        content = BoxLayout(orientation="vertical")
        content.add_widget(Image(source=img_path))
        close_btn = Button(text="Close", size_hint_y=None, height=dp(44))
        content.add_widget(close_btn)
        popup = Popup(title="📈 Expense Graph", content=content, size_hint=(0.9, 0.9))
        close_btn.bind(on_release=popup.dismiss)
        popup.open()


if __name__ == "__main__":
    ExpenseApp().run()
