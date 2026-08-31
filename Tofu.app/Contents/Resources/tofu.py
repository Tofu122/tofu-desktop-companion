import sys, json, random
from datetime import datetime, date
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QPoint, QRectF
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QMouseEvent, QFont
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QInputDialog, QVBoxLayout, QHBoxLayout,
    QFrame, QDialog, QLabel, QTextEdit, QScrollArea
)

APP_DIR = Path(__file__).resolve().parent
ASSETS = APP_DIR / "assets"
DATA_DIR = Path.home() / "Library" / "Application Support" / "Tofu"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = DATA_DIR / "tofu_data.json"
LEGACY_DATA_FILE = APP_DIR / "pip_data.json"

DEFAULT = {
    "beans": 0,
    "friendship": 0,
    "water": 0,
    "water_today": 0,
    "water_date": "",
    "focus_sessions": 0,
    "focus_minutes": 0,
    "reminder_text": "",
    "reminder_minutes": 60,
    "diary": [],
    "achievements": [],
    "unlocked_items": [],
    "equipped_item": "",
    "days_seen": 0,
    "last_seen_date": "",
    "streak": 0,
    "longest_streak": 0,
    "random_events_seen": [],
}

SHOP_ITEMS = {
    "flower": {"name": "Flower", "icon": "🌼", "cost": 8},
    "leaf": {"name": "Leaf", "icon": "🍃", "cost": 10},
    "bow": {"name": "Bow", "icon": "🎀", "cost": 14},
    "glasses": {"name": "Glasses", "icon": "👓", "cost": 18},
    "bear": {"name": "Tiny bear", "icon": "🧸", "cost": 22},
    "crown": {"name": "Crown", "icon": "👑", "cost": 30},
}

SPECIAL_ITEMS = {
    "study_star": {"name": "Study star", "icon": "⭐"},
    "water_drop": {"name": "Water charm", "icon": "💧"},
    "moon": {"name": "Night moon", "icon": "🌙"},
    "friend_heart": {"name": "Friendship heart", "icon": "💛"},
    "streak_medal": {"name": "Seven-day charm", "icon": "🏅"},
}

ACHIEVEMENTS = {
    "first_focus": ("Study Buddy", "Finished your first focus session", "study_star"),
    "focus_10": ("Desk Friends", "Finished 10 focus sessions", None),
    "water_20": ("Hydrated Human", "Logged water 20 times", "water_drop"),
    "night_owl": ("Night Owl", "Finished a focus session late at night", "moon"),
    "friend_25": ("Getting Close", "Reached 25 friendship", "friend_heart"),
    "streak_7": ("Old Routine", "Spent 7 days in a row with Tofu", "streak_medal"),
    "days_30": ("Old Friends", "Had Tofu around on 30 different days", None),
}

AFFIRMATIONS = [
    "tiny progress still counts ✨",
    "one thing at a time.",
    "relax your shoulders. i’m here.",
    "small care is still care 💛",
    "you don't need a perfect day.",
]

RANDOM_EVENTS = [
    ("leaf", "i found a tiny leaf 🍃", 1),
    ("box", "important research: boxes are good.", 0),
    ("window", "i was staring at nothing. very busy.", 0),
    ("gift", "i found you a bean 🫘", 1),
    ("nap", "...five minute floor nap?", 0),
    ("zoom", "i briefly had zoomies.", 0),
]


def today_iso():
    return date.today().isoformat()


def load_data():
    source = DATA_FILE if DATA_FILE.exists() else LEGACY_DATA_FILE
    d = DEFAULT.copy()
    if source.exists():
        try:
            old = json.loads(source.read_text())
            d.update({k: v for k, v in old.items() if k in d})
            # Migrate the old coin system into useful beans. XP is intentionally discarded.
            if "beans" not in old and "coins" in old:
                d["beans"] = max(0, int(old.get("coins", 0)))
            if "water" in old:
                d["water"] = max(0, int(old.get("water", 0)))
        except Exception:
            pass
    for key in ("diary", "achievements", "unlocked_items", "random_events_seen"):
        if not isinstance(d.get(key), list):
            d[key] = []
    return d


def save_data(d):
    try:
        DATA_FILE.write_text(json.dumps(d, indent=2, ensure_ascii=False))
    except Exception:
        pass


def add_diary(d, text):
    stamp = datetime.now().strftime("%b %d · %I:%M %p")
    d.setdefault("diary", []).append({"time": stamp, "text": text})
    d["diary"] = d["diary"][-80:]


def friendship_label(value):
    if value < 10:
        return "new roommates"
    if value < 25:
        return "getting familiar"
    if value < 50:
        return "desk buddies"
    if value < 80:
        return "close friends"
    return "inseparable"


class Speech(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.text = ""
        self.resize(158, 54)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)

    def say(self, text, pet_rect, ms=4200):
        self.text = text
        area = (QApplication.screenAt(pet_rect.center()) or QApplication.primaryScreen()).availableGeometry()
        x = pet_rect.center().x() - self.width() // 2
        y = pet_rect.top() - self.height() - 6
        x = max(area.left() + 8, min(x, area.right() - self.width() - 8))
        if y < area.top() + 8:
            y = pet_rect.bottom() + 6
        self.move(x, y)
        self.show(); self.raise_(); self.update(); self.timer.start(ms)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor("#4a4a4a"), 1.0))
        p.setBrush(QColor(255, 255, 255, 246))
        r = QRectF(2, 2, self.width() - 4, self.height() - 6)
        p.drawRoundedRect(r, 13, 13)
        p.setPen(QColor("#151515"))
        font = p.font(); font.setPointSizeF(8.0); p.setFont(font)
        p.drawText(r.adjusted(8, 5, -8, -5), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.text)


class DropDownMenu(QWidget):
    def __init__(self, pet):
        super().__init__()
        self.pet = pet
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        panel = QFrame(self); panel.setObjectName("panel")
        layout = QVBoxLayout(panel); layout.setContentsMargins(5,5,5,5); layout.setSpacing(1)
        items = [
            ("🎧  Focus", pet.start_focus),
            ("💧  Water", pet.log_water),
            ("⏰  Reminder", pet.set_reminder),
            ("💬  Talk to Tofu", pet.talk),
            ("🫘  Tofu's stuff", pet.show_stuff),
            ("📖  Our diary", pet.show_diary),
            ("🏆  Achievements", pet.show_achievements),
            ("✕  Quit", pet.quit_app),
        ]
        for text, callback in items:
            b = QPushButton(text); b.setCursor(Qt.CursorShape.PointingHandCursor); b.clicked.connect(callback); layout.addWidget(b)
        self.setStyleSheet("""
            QFrame#panel { background: rgba(255,255,255,248); border:1px solid #555; border-radius:10px; }
            QPushButton { background:transparent; border:none; border-radius:6px; min-width:118px; min-height:23px;
                          padding:2px 7px; text-align:left; font-size:10px; color:#171717; }
            QPushButton:hover { background:#eeeeee; }
        """)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0); outer.addWidget(panel); self.adjustSize()


class InfoDialog(QDialog):
    def __init__(self, title, width=330, height=360):
        super().__init__()
        self.setWindowTitle(title)
        self.resize(width, height)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(14,14,14,14)
        self.layout.setSpacing(9)
        self.setStyleSheet("""
            QDialog { background:#fbfbfb; }
            QLabel { color:#202020; font-size:12px; }
            QPushButton { min-height:28px; border:1px solid #b9b9b9; border-radius:7px; background:white; padding:3px 8px; }
            QPushButton:hover { background:#f0f0f0; }
            QTextEdit { background:white; border:1px solid #c7c7c7; border-radius:8px; padding:6px; font-size:11px; }
        """)


class Tofu(QWidget):
    def __init__(self):
        super().__init__()
        self.data = load_data()
        self.setWindowTitle("Tofu")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.resize(92,108)
        self.poses = [QPixmap(str(ASSETS / "pose_a.png")), QPixmap(str(ASSETS / "pose_b.png"))]
        self.pose_index = 0; self.direction = 1; self.dragging = False; self.drag_offset = QPoint()
        self.menu_open = False; self.focus_active = False; self.focus_total = 0; self.focus_seconds = 0; self.pause_ticks = 0

        self.speech = Speech(); self.menu = DropDownMenu(self); self.menu.hide()
        self.anim = QTimer(self); self.anim.timeout.connect(self.tick); self.anim.start(170)
        self.focus_timer = QTimer(self); self.focus_timer.timeout.connect(self.focus_tick)
        self.reminder_timer = QTimer(self); self.reminder_timer.timeout.connect(self.fire_reminder); self.restore_reminder()
        self.event_timer = QTimer(self); self.event_timer.timeout.connect(self.maybe_random_event); self.event_timer.start(95_000)

        area = QApplication.primaryScreen().availableGeometry()
        self.move(area.right()-self.width()-30, area.bottom()-self.height()-25)
        self.register_daily_visit()
        self.check_achievements(silent=True)
        QTimer.singleShot(700, lambda: self.say(self.greeting()))

    def register_daily_visit(self):
        today = today_iso(); last = self.data.get("last_seen_date", "")
        if last == today:
            return
        if last:
            try:
                delta = (date.fromisoformat(today) - date.fromisoformat(last)).days
            except Exception:
                delta = 99
            self.data["streak"] = self.data.get("streak",0) + 1 if delta == 1 else 1
        else:
            self.data["streak"] = 1
        self.data["longest_streak"] = max(self.data.get("longest_streak",0), self.data["streak"])
        self.data["days_seen"] = self.data.get("days_seen",0) + 1
        self.data["last_seen_date"] = today
        self.data["friendship"] = min(100, self.data.get("friendship",0) + 1)
        self.data["water_today"] = 0; self.data["water_date"] = today
        add_diary(self.data, "Tofu showed up for another day on your desktop.")
        save_data(self.data)

    def greeting(self):
        h = datetime.now().hour; f = self.data.get("friendship",0)
        if 5 <= h < 11:
            pool = ["morning. i'm awake-ish ☀️", "good morning. tiny start?"]
        elif 11 <= h < 17:
            pool = ["hi. i'm supervising.", "afternoon patrol underway."]
        elif 17 <= h < 23:
            pool = ["evening desk shift ✨", "i'm still hanging around."]
        else:
            pool = ["it's late... i'm not judging 🌙", "night shift together?"]
        if f >= 50:
            pool.append("oh, you're here 💛")
        elif f < 10:
            pool.append("double-click me if you need me.")
        return random.choice(pool)

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if self.direction < 0:
            p.translate(self.width(),0); p.scale(-1,1)
        pix = self.poses[self.pose_index]; yoff = -1 if self.pose_index else 0
        p.drawPixmap(QRectF(6,4+yoff,self.width()-12,self.height()-8), pix, QRectF(pix.rect()))
        item = self.data.get("equipped_item", "")
        meta = SHOP_ITEMS.get(item) or SPECIAL_ITEMS.get(item)
        if meta:
            # Small symbolic accessory, deliberately kept away from the cat artwork itself.
            p.save()
            if self.direction < 0:
                p.scale(-1,1); p.translate(-self.width(),0)
            font = QFont(); font.setPointSizeF(14); p.setFont(font); p.setPen(QColor("#222"))
            p.drawText(QRectF(self.width()-30, 2, 27, 25), Qt.AlignmentFlag.AlignCenter, meta["icon"])
            p.restore()

    def tick(self):
        if self.pause_ticks > 0: self.pause_ticks -= 1; return
        if self.dragging or self.menu_open: return
        self.pose_index = 1-self.pose_index; self.move_horizontal(); self.update()

    def move_horizontal(self):
        area = (QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()).availableGeometry()
        speed = 2 if not self.focus_active else 3; x = self.x()+self.direction*speed
        if x <= area.left(): x=area.left(); self.direction=1
        elif x+self.width() >= area.right(): x=area.right()-self.width(); self.direction=-1
        self.move(int(x), self.y())

    def say(self, text, ms=4200):
        self.pause_ticks = 18; self.speech.say(text, self.frameGeometry(), ms)

    def mouseDoubleClickEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton: self.toggle_menu()
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.dragging=True; self.drag_offset=e.globalPosition().toPoint()-self.frameGeometry().topLeft()
    def mouseMoveEvent(self, e):
        if self.dragging:
            self.move(e.globalPosition().toPoint()-self.drag_offset)
            if self.menu_open: self.position_menu()
    def mouseReleaseEvent(self, e): self.dragging=False

    def toggle_menu(self):
        if self.menu_open: self.close_menu(); return
        self.menu_open=True; self.speech.hide(); self.position_menu(); self.menu.show(); self.menu.raise_()
    def close_menu(self): self.menu_open=False; self.menu.hide()
    def position_menu(self):
        g=self.frameGeometry(); area=(QApplication.screenAt(g.center()) or QApplication.primaryScreen()).availableGeometry(); self.menu.adjustSize()
        x=g.center().x()-self.menu.width()//2; y=g.bottom()+4
        if y+self.menu.height()>area.bottom()-5: y=g.top()-self.menu.height()-4
        x=max(area.left()+5,min(x,area.right()-self.menu.width()-5)); y=max(area.top()+5,min(y,area.bottom()-self.menu.height()-5)); self.menu.move(x,y)

    def add_friendship(self, amount):
        old=self.data.get("friendship",0); self.data["friendship"] = min(100, old+amount)
        if self.data["friendship"] != old: self.check_achievements(silent=True)

    def earn_beans(self, amount):
        self.data["beans"] = max(0, self.data.get("beans",0)+amount)

    def start_focus(self):
        self.close_menu()
        mins,ok=QInputDialog.getInt(self,"Focus with Tofu","How many minutes?",25,5,180,5)
        if not ok:return
        self.focus_active=True; self.focus_total=self.focus_seconds=mins*60; self.focus_timer.start(1000)
        self.say(f"{mins} min together 🎧")

    def focus_tick(self):
        if not self.focus_active:return
        self.focus_seconds-=1; elapsed=self.focus_total-self.focus_seconds
        if elapsed>0 and elapsed%(20*60)==0:self.say("stretch break? 🙆")
        elif elapsed>0 and elapsed%(10*60)==0:self.say("shoulders down ✨")
        elif elapsed>0 and elapsed%(7*60)==0:self.say("tiny water check 💧")
        if self.focus_seconds<=0:
            self.focus_active=False; self.focus_timer.stop(); mins=max(1,self.focus_total//60)
            beans=max(2,min(12,mins//10+1)); self.earn_beans(beans); self.add_friendship(2)
            self.data["focus_sessions"]+=1; self.data["focus_minutes"]+=mins
            add_diary(self.data,f"You and Tofu focused together for {mins} minutes. Tofu found {beans} beans.")
            self.check_achievements(silent=False); save_data(self.data)
            self.say(f"we did it 🎉  +{beans} 🫘",6000)

    def log_water(self):
        self.close_menu(); today=today_iso()
        if self.data.get("water_date")!=today: self.data["water_date"]=today; self.data["water_today"]=0
        self.data["water"]+=1; self.data["water_today"]+=1
        rewarded=self.data["water_today"]<=8
        if rewarded:self.earn_beans(1)
        if self.data["water_today"]<=5:self.add_friendship(1)
        add_diary(self.data,"You logged a glass of water." + (" Tofu found 1 bean." if rewarded else ""))
        self.check_achievements(silent=False); save_data(self.data)
        self.say("hydration +1 💧  +1 🫘" if rewarded else "hydration +1 💧")

    def talk(self):
        self.close_menu(); h=datetime.now().hour; f=self.data.get("friendship",0)
        pool=list(AFFIRMATIONS)
        if h>=23 or h<5: pool += ["we should probably sleep soon 🌙","late-night desk club."]
        if 5<=h<10: pool += ["morning counts even if slow.","start tiny. that's enough."]
        if f>=25: pool += ["i like our little routine.","i'll keep you company."]
        if f>=50: pool += ["you again. good 💛","i saved you the good desk spot."]
        self.say(random.choice(pool),5000)

    def set_reminder(self):
        self.close_menu()
        text,ok=QInputDialog.getText(self,"Tofu reminder","What should I remind you about?",text=self.data.get("reminder_text","Drink water"))
        if not ok or not text.strip():return
        mins,ok=QInputDialog.getInt(self,"Reminder interval","Repeat every how many minutes?",int(self.data.get("reminder_minutes",60)),5,1440,5)
        if not ok:return
        self.data["reminder_text"]=text.strip(); self.data["reminder_minutes"]=mins; self.restore_reminder()
        add_diary(self.data,f"Tofu started a repeating reminder: “{text.strip()}” every {mins} minutes.")
        save_data(self.data); self.say(f"got it ⏰ every {mins} min")

    def restore_reminder(self):
        self.reminder_timer.stop(); t=self.data.get("reminder_text","").strip()
        if t:self.reminder_timer.start(int(self.data.get("reminder_minutes",60))*60*1000)
    def fire_reminder(self):
        t=self.data.get("reminder_text","").strip()
        if t:self.say(f"little reminder 💭\n{t}",6000)

    def maybe_random_event(self):
        if self.menu_open or self.dragging or self.focus_active or random.random()>0.18:return
        key,text,beans=random.choice(RANDOM_EVENTS)
        if beans:self.earn_beans(beans)
        if key not in self.data["random_events_seen"]:
            self.data["random_events_seen"].append(key); add_diary(self.data,f"Random Tofu moment: {text}" + (f" (+{beans} bean)" if beans else ""))
        save_data(self.data); self.say(text,5000)

    def show_stuff(self):
        self.close_menu(); dlg=InfoDialog("Tofu's stuff",360,430)
        header=QLabel(); header.setWordWrap(True); dlg.layout.addWidget(header)
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        body=QWidget(); v=QVBoxLayout(body); v.setContentsMargins(0,0,0,0); v.setSpacing(6)

        def refresh_header():
            eq=self.data.get("equipped_item",""); meta=SHOP_ITEMS.get(eq) or SPECIAL_ITEMS.get(eq)
            current=(meta["icon"]+" "+meta["name"]) if meta else "nothing"
            header.setText(f"🫘 {self.data.get('beans',0)} beans     💛 {self.data.get('friendship',0)}/100\nWearing: {current}")

        def equip(item_id):
            self.data["equipped_item"] = "" if self.data.get("equipped_item")==item_id else item_id
            save_data(self.data); self.update(); refresh_header(); dlg.close(); self.say("new look ✨")

        def buy(item_id):
            meta=SHOP_ITEMS[item_id]; cost=meta["cost"]
            if self.data.get("beans",0)<cost:
                self.say("not enough beans yet 🫘"); return
            self.data["beans"]-=cost; self.data["unlocked_items"].append(item_id)
            add_diary(self.data,f"You bought {meta['name']} for Tofu for {cost} beans.")
            save_data(self.data); dlg.close(); self.show_stuff()

        all_items={**SHOP_ITEMS, **SPECIAL_ITEMS}
        for item_id,meta in all_items.items():
            row=QFrame(); h=QHBoxLayout(row); h.setContentsMargins(4,3,4,3)
            special=item_id in SPECIAL_ITEMS; unlocked=item_id in self.data.get("unlocked_items",[])
            lab=QLabel(f"{meta['icon']}  {meta['name']}" + ("  · achievement" if special else f"  · {meta['cost']} 🫘")); h.addWidget(lab,1)
            b=QPushButton("Unequip" if self.data.get("equipped_item")==item_id else ("Equip" if unlocked else ("Locked" if special else "Buy")))
            if special and not unlocked:b.setEnabled(False)
            elif unlocked:b.clicked.connect(lambda _,i=item_id:equip(i))
            else:b.clicked.connect(lambda _,i=item_id:buy(i))
            h.addWidget(b); v.addWidget(row)
        clear=QPushButton("Wear nothing"); clear.clicked.connect(lambda: equip("")); v.addWidget(clear)
        scroll.setWidget(body); dlg.layout.addWidget(scroll); refresh_header(); dlg.exec()

    def show_diary(self):
        self.close_menu(); dlg=InfoDialog("Our diary",370,430)
        summary=QLabel(
            f"💛 {friendship_label(self.data.get('friendship',0))} · {self.data.get('friendship',0)}/100\n"
            f"🫘 {self.data.get('beans',0)} beans   ·   🔥 {self.data.get('streak',0)} day streak\n"
            f"🎧 {self.data.get('focus_sessions',0)} sessions / {self.data.get('focus_minutes',0)} min   ·   💧 {self.data.get('water',0)} waters"
        ); summary.setWordWrap(True); dlg.layout.addWidget(summary)
        text=QTextEdit(); text.setReadOnly(True)
        entries=self.data.get("diary",[])[-35:]
        text.setPlainText("\n\n".join(f"{e.get('time','')}\n{e.get('text','')}" for e in reversed(entries)) or "The diary is empty. Go make a tiny memory with Tofu.")
        dlg.layout.addWidget(text); dlg.exec()

    def show_achievements(self):
        self.close_menu(); dlg=InfoDialog("Achievements",350,390)
        got=set(self.data.get("achievements",[])); dlg.layout.addWidget(QLabel(f"🏆 {len(got)} / {len(ACHIEVEMENTS)} discovered"))
        text=QTextEdit(); text.setReadOnly(True); lines=[]
        for aid,(name,desc,item) in ACHIEVEMENTS.items():
            if aid in got:
                bonus=""; meta=SPECIAL_ITEMS.get(item) if item else None
                if meta: bonus=f"\nUnlocked: {meta['icon']} {meta['name']}"
                lines.append(f"✓ {name}\n{desc}{bonus}")
            else:
                lines.append(f"? ???\nKeep spending time with Tofu to discover this.")
        text.setPlainText("\n\n".join(lines)); dlg.layout.addWidget(text); dlg.exec()

    def check_achievements(self, silent=False):
        tests={
            "first_focus": self.data.get("focus_sessions",0)>=1,
            "focus_10": self.data.get("focus_sessions",0)>=10,
            "water_20": self.data.get("water",0)>=20,
            "night_owl": self.data.get("focus_sessions",0)>=1 and (datetime.now().hour>=23 or datetime.now().hour<5),
            "friend_25": self.data.get("friendship",0)>=25,
            "streak_7": self.data.get("streak",0)>=7,
            "days_30": self.data.get("days_seen",0)>=30,
        }
        newly=[]
        for aid,met in tests.items():
            if met and aid not in self.data["achievements"]:
                self.data["achievements"].append(aid); name,desc,item=ACHIEVEMENTS[aid]; newly.append(name)
                if item and item not in self.data["unlocked_items"]: self.data["unlocked_items"].append(item)
                self.earn_beans(3); add_diary(self.data,f"Achievement unlocked: {name}. Tofu celebrated with 3 beans.")
        save_data(self.data)
        if newly and not silent:
            self.say(f"achievement! 🏆\n{newly[0]}  +3 🫘",6500)

    def quit_app(self):
        save_data(self.data); QApplication.quit()


if __name__ == "__main__":
    app=QApplication(sys.argv); app.setApplicationName("Tofu")
    # Tofu is a desktop companion: closing a temporary dialog must not quit the app.
    app.setQuitOnLastWindowClosed(False)
    tofu=Tofu(); tofu.show(); sys.exit(app.exec())
