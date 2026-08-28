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
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.utils import platform
from kivy.graphics import Color, Ellipse
from kivy.uix.widget import Widget

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


class PieChart(Widget):
    """Draws a simple pie chart using Kivy's canvas graphics only (no matplotlib)."""

    PALETTE = [
        (0.30, 0.69, 0.31, 1), (0.20, 0.60, 0.86, 1), (0.90, 0.49, 0.13, 1),
        (0.61, 0.35, 0.71, 1), (0.90, 0.22, 0.21, 1), (0.95, 0.77, 0.06, 1),
        (0.10, 0.74, 0.61, 1), (0.55, 0.34, 0.29, 1), (0.40, 0.40, 0.40, 1),
    ]

    def __init__(self, data, **kwargs):
        super().__init__(**kwargs)
        self.data = data  # dict: category -> amount
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        self.canvas.clear()
        if not self.data:
            return
        total = sum(self.data.values())
        if total <= 0:
            return

        size = min(self.width, self.height) * 0.8
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2

        with self.canvas:
            start_angle = 0
            for i, (cat, amount) in enumerate(self.data.items()):
                fraction = amount / total
                sweep = fraction * 360
                Color(*self.PALETTE[i % len(self.PALETTE)])
                Ellipse(pos=(cx - size / 2, cy - size / 2), size=(size, size),
                         angle_start=start_angle, angle_end=start_angle + sweep)
                start_angle += sweep


class PieLegend(BoxLayout):
    """Simple color-swatch + label legend under the pie chart."""

    def __init__(self, data, **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None, spacing=dp(4), **kwargs)
        self.bind(minimum_height=self.setter("height"))
        total = sum(data.values()) or 1
        for i, (cat, amount) in enumerate(data.items()):
            row = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(8))
            color = PieChart.PALETTE[i % len(PieChart.PALETTE)]
            swatch = Widget(size_hint_x=None, width=dp(18))

            def make_updater(widget, col):
                def _update(*_):
                    widget.canvas.clear()
                    with widget.canvas:
                        Color(*col)
                        Ellipse(pos=widget.pos, size=(dp(18), dp(18)))
                return _update

            updater = make_updater(swatch, color)
            swatch.bind(pos=updater, size=updater)
            updater()

            pct = amount / total * 100
            label = Label(text=f"{cat} — {pct:.1f}%", color=(1, 1, 1, 1),
                           halign="left", valign="middle", size_hint_x=1)
            label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
            row.add_widget(swatch)
            row.add_widget(label)
            self.add_widget(row)


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

        content = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        chart = PieChart(data, size_hint=(1, 0.65))
        legend_scroll = ScrollView(size_hint=(1, 0.35))
        legend_scroll.add_widget(PieLegend(data))
        close_btn = Button(text="Close", size_hint_y=None, height=dp(44))

        content.add_widget(chart)
        content.add_widget(legend_scroll)
        content.add_widget(close_btn)

        popup = Popup(title="📈 Expense Distribution", content=content, size_hint=(0.9, 0.9))
        close_btn.bind(on_release=popup.dismiss)
        popup.open()


if __name__ == "__main__":
    ExpenseApp().run()
