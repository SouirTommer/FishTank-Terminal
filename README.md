# Terminal Fish Tank

<img width="1080" height="557" alt="image" src="https://github.com/user-attachments/assets/05d00440-fd28-4b70-be88-5333f4641738" />

An interactive fish-feeding game in your terminal (cmd / Windows Terminal / macOS Terminal). Pure Python stdlib, zero dependencies.

## Run

```
python fish.py
```

## Controls

- `SPACE` drop food
- `N` toggle fish names
- `C` toggle bubbles
- `+` / `-` add / remove fish
- `T` cycle color theme
- `V` watch mode (auto-feed, fish never die)
- `ESC` quit

## Gameplay

Fish actively chase food, each with its own speed and appetite. Each pellet eaten scores 1 point and feeds the tank. The tank-wide hunger meter drains over time — keep feeding, or when it empties a fish dies and the meter refills. Named AI fish of different colors and sizes swim on their own, leaving faint trails; bubbles rise, seaweed sways, and gravel lines the bottom. Watch mode (`V`) auto-feeds the tank so you can just sit back and watch.

> Make sure the terminal window is at least 30x12.

## Troubleshooting

- **Keys stop working after switching to a Chinese IME** — the game reads raw console keys, so a Chinese-mode IME swallows them for text composition (Space commits the composition, letters are pinyin). Switch the IME back to English/ASCII mode (e.g. `Ctrl+Space` or the `中/英` toggle) before playing; if a stuck composition persists, press `Ctrl+Space` or click into the window once.
