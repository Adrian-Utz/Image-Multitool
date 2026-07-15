import tkinter as tk
import winsound
import random

#Beginning of the Easter Egg. Listens for the konami code and triggers a random codec message from Snake.
#Last Update: 5/22/2026
#Written by: AJ Utz 


class KonamiEasterEgg:
    def __init__(self, root, log_method, resource_path_method):
        self.root = root
        self.log = log_method
        self.resource_path = resource_path_method

        # Konami code easter egg state
        self.konami_sequence = ["up", "up", "down", "down", "left", "right", "left", "right", "b", "a"]
        self.konami_buffer = []
        self.konami_unlocked = False
        root.bind_all("<Key>", self._on_key)

    # Method to check the users key presses. If it matches the Konami code sequence, it triggers the easter egg.
    def _on_key(self, event):
        key = event.keysym.lower()
        # Accept both arrow key names and letters as Konami input
        if key in {"up", "down", "left", "right", "a", "b"}:
            self.konami_buffer.append(key)
            # maintain maximum buffer size
            if len(self.konami_buffer) > len(self.konami_sequence):
                self.konami_buffer.pop(0)
            if self.konami_buffer == self.konami_sequence:
                self._trigger_konami_reward()
        else:
            # maintain strict sequence; reset if wrong key pressed
            self.konami_buffer = []

    def check_konami_message(self, text):
        text_normalized = text.lower().replace("\r", " ").replace("\n", " ")
        pattern = "up up down down left right left right b a"
        return pattern in text_normalized

    def _trigger_konami_reward(self):
        if hasattr(self, 'konami_unlocked') and self.konami_unlocked:
            return
        self.konami_unlocked = True
        self.log("[EASTER EGG] Incoming CODEC Transmission...")
        self._show_snake_call()

    def _show_snake_call(self):
        try:
            sound_path = self.resource_path("assets/codec.wav")
            winsound.PlaySound(sound_path, winsound.SND_ASYNC)
        except:
            pass
        self.codec_messages = [
            "📡 Incoming CODEC...\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n"
            "Snake: You've caught me at a bad time.\n\n"
            "Snake: I'm trying to sneak out of the compound, but there are too many guards.\n\n"
            "Snake: Raiden, I need you to contact the diamond dogs to cause a distraction.\n\n"
            "Snake: They will know what to do.\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n",
            "📡 Incoming CODEC...\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n"
            "Snake: Kept you waiting huh?\n\n"
            "Snake: Your mission is to find Sokolov and escort him to the extraction point.\n\n"
            "Snake: I will meet you there.\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n",
            "📡 Incoming CODEC...\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n"
            "Snake: What's a Hind doing here?\n\n"
            "Snake: Careful Raiden, with the enemy patroling the skys, it would be wise to proceed with caution.\n\n"
            "Snake: Keep low, Raiden I'll call in air support.\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n",
            "📡 Incoming CODEC...\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n"
            "Snake: Disregard what I just said, Raiden.\n\n"
            "Snake: The most important thing you can do now is enjoy a mouth watering egg McMuffin sandwich from McDonald's.\n\n"
            "Snake: And always remember, Raiden...\n\n"
            "Snake: I'm loving it.\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n",
            "📡 Incoming CODEC...\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n"
            "Snake: Raiden, do you copy?\n\n"
            "Snake: The forest is crawling with enemy soldiers.\n\n"
            "Snake: Use your adaptive camo to blend in to your surroundings and avoid detection.\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n",
            "📡 Incoming CODEC...\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n"
            "Snake: I'm trying to sneak around...\n\n"
            "Snake: But I can't seem to find a opening. These guards are too good.\n\n"
            "Snake: Disregarding the stealthy approach may be necessary.\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n"
            "Snake: ...\n\n",
        ]
        codec = tk.Toplevel(self.root)
        codec.title("CODEC")
        codec.geometry("1000x600")
        codec.configure(bg="black")

        full_text = random.choice(self.codec_messages)

        label = tk.Label(
            codec,
            text="",
            fg="lime",
            bg="black",
            font=("Courier", 10),
            justify="left",
            anchor="nw"
        )
        label.pack(padx=15, pady=15, fill="both", expand=True)
        codec.after(1000, lambda l=label: self._typewriter_effect(label, full_text))
        self._blinking_cursor(label)

        btn = tk.Button(codec, text="...", command=codec.destroy, bg="gray", fg="white")
        btn.pack(pady=5)

    def _typewriter_effect(self, label, full_text, delay=50, line_pause=500, index=0):
        if not label.winfo_exists():
                return  # Widget was destroyed, stop recursion
        if index <= len(full_text):
            label.config(text=full_text[:index])
            current_delay = delay
            if index > 0 and full_text[index - 1] == "\n":
                current_delay += line_pause
            self.root.after(current_delay, self._typewriter_effect, label, full_text, delay, line_pause, index + 1)

    def _blinking_cursor(self, label, blink=True):
        if not label.winfo_exists():
            return  # Widget was destroyed, stop recursion
        base = label.cget("text").rstrip("_")
        label.config(text=base + ("_" if blink else ""))
        label.after(500, self._blinking_cursor, label, not blink)