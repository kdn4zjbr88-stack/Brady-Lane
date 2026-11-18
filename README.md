# Brady

A cheeky adults-only management game for desktop. Pick your character (a penis or a vagina), choose skin and hair colour, and keep them healthy, clean, happy and safe for 30 days.

## Run

```bash
pip install -r requirements.txt
python main.py
```

## How to play

Each day has four time slots (Morning, Afternoon, Evening, Night), and most actions use one.

| Action | Effect |
| --- | --- |
| Eat | $12, fills you up |
| Shower | Hygiene back to 100 |
| Sleep | Skip to next morning, full energy |
| Work | +$60, not at night |
| Party | $30, evening/night only, meet new people |
| Buy condoms | $15 for 3, takes no time |
| Clinic | $50, test and treat infections |
| Hook up | Pick someone you've met; with or without a condom |

Unprotected hookups risk STIs (which drain health until treated) and pregnancy scares. Low hygiene, hunger or energy hurt your health. Hit zero health and it's game over. Score rewards surviving, mood, health, money and safe sex.

## Tests

```bash
python -m pytest
```
