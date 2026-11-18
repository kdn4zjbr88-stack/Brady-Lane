# Brady

A cheeky adults-only life-management game for desktop. Pick your character (a penis or a vagina), choose skin and hair colour, then walk around town keeping them healthy, clean, happy and safe for 30 days.

## Run

```bash
pip install -r requirements.txt
python main.py
```

## Controls

| Key | Action |
| --- | --- |
| WASD / arrows | Walk |
| 1-5 or click | Pick a choice from the pop-up |
| E / Enter / Space | Pick the first available choice |
| P / Tab | Open the phone (Spark dating app) |
| Esc | Close phone or pop-up |

Walk up to a door, a piece of furniture or a person and choices pop up.

## The town

| Place | What you can do |
| --- | --- |
| Home | Sleep, shower, toilet, fridge snack, mirror (check your charm) |
| Diner | Eat a proper meal |
| Office | Work a shift for money |
| Pharmacy | Condoms, pregnancy tests, morning-after pill |
| Clinic | STI test and treatment |
| Ink & Steel | Buy piercings (raise charm, but keep them clean while they heal) |
| Club Velvet | Evening/night only: drink, dance, chat people up, go home with them |
| Apartments | Your date's bedroom, unlocked when someone is expecting you |

## Dating

Open the phone and swipe right or left (drag the card, use arrow keys, or press the buttons). Matches depend on your charm (hygiene, mood, piercings). Text a match in the evening to get invited over to the Apartments.

## Risk

Each encounter is a choice: condom, or no condom and then pull out or finish inside. Partners carry a hidden STI risk, and when pregnancy is possible each choice has a hidden pregnancy risk. A pregnancy shows up as a late period after a few days; a test can confirm it, and the morning-after pill only helps if taken within about a day. Left alone, it becomes the game's ending.

## Tests

```bash
python -m pytest
```
