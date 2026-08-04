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
- `ESC` quit

## Gameplay

Fish actively chase food. Each pellet eaten scores 1 point and feeds the tank. The tank-wide hunger meter drains over time — keep feeding, or when it empties a fish dies and the meter refills. Six named AI fish of different colors and sizes swim on their own; bubbles rise, seaweed sways, and gravel lines the bottom.

> Make sure the terminal window is at least 30x12.
