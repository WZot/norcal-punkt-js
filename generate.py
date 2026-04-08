#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["jinja2"]
# ///
"""Generate a static Norwegian calendar page styled with Punkt CSS."""

import argparse
import math
from datetime import date, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# -- Norwegian locale constants ------------------------------------------------

MONTHS_NO = [
    "Januar", "Februar", "Mars", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Desember",
]

DAYS_NO = ["Ma", "Ti", "On", "To", "Fr", "Lø", "Sø"]

MABBR_NO = ["jan", "feb", "mar", "apr", "mai", "jun",
             "jul", "aug", "sep", "okt", "nov", "des"]


# -- Date helpers --------------------------------------------------------------

def easter(year: int) -> date:
    """Easter Sunday via the Anonymous Gregorian algorithm (Computus)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def nth_wday(year: int, month: int, wday: int, n: int) -> date:
    """N-th occurrence of a weekday (1=Mon..7=Sun) in a given month."""
    first = date(year, month, 1)
    return first + timedelta(days=(wday - first.isoweekday()) % 7 + (n - 1) * 7)


def last_wday(year: int, month: int, wday: int) -> date:
    """Last occurrence of a weekday in a given month."""
    if month == 12:
        last = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last = date(year, month + 1, 1) - timedelta(days=1)
    return last - timedelta(days=(last.isoweekday() - wday) % 7)


# -- Norwegian holidays -------------------------------------------------------

def red_days(year: int) -> dict[date, str]:
    """Public holidays (røde dager) — official days off."""
    e = easter(year)
    return {
        date(year, 1, 1):   "Første nyttårsdag",
        e - timedelta(3):   "Skjærtorsdag",
        e - timedelta(2):   "Langfredag",
        e:                   "1. påskedag",
        e + timedelta(1):   "2. påskedag",
        date(year, 5, 1):   "Arbeidernes dag",
        e + timedelta(39):  "Kristi himmelfartsdag",
        date(year, 5, 17):  "Grunnlovsdagen",
        e + timedelta(49):  "1. pinsedag",
        e + timedelta(50):  "2. pinsedag",
        date(year, 12, 25): "1. juledag",
        date(year, 12, 26): "2. juledag",
    }


def half_days(year: int) -> dict[date, str]:
    """Half days (fri fra kl. 12) per HTA for stat/KS-kommune.

    Pinseaften (easter+48) is always a Saturday so irrelevant for day workers.
    """
    e = easter(year)
    return {
        e - timedelta(4):   "Onsdag før skjærtorsdag",
        date(year, 12, 24): "Julaften",
        date(year, 12, 31): "Nyttårsaften",
    }


def notable_dates(year: int) -> list[tuple[date, str, bool, bool]]:
    """Notable dates: (date, description, show_date_in_red?, is_half_day?)."""
    e = easter(year)
    holidays = red_days(year)
    halfs = half_days(year)

    morsdag = nth_wday(year, 2, 7, 2)
    farsdag = nth_wday(year, 11, 7, 2)
    sommer_start = last_wday(year, 3, 7)
    sommer_slutt = last_wday(year, 10, 7)
    fastelavn = e - timedelta(49)
    botsdag = last_wday(year, 10, 7)
    nov27 = date(year, 11, 27)
    advent1 = nov27 + timedelta(days=(7 - nov27.isoweekday()) % 7)

    notable_names = {
        e + timedelta(39): "Kristi himmelfartsdag",
        date(year, 5, 17): "Grunnlovsdagen 1814",
    }

    entries = [(d, notable_names.get(d, name), True, d in halfs)
               for d, name in holidays.items()]

    # Red-in-list but not a public holiday
    entries.append((e - timedelta(7), "Palmesøndag", True, False))

    # Non-red notable dates
    non_red = [
        (date(year, 1, 21),  f"Prinsesse Ingrid Alexandra, {year - 2004} år"),
        (date(year, 2, 6),   "Samefolkets dag"),
        (morsdag,             "Morsdag"),
        (date(year, 2, 14),  "Valentinsdag"),
        (fastelavn,           "Fastelavn"),
        (date(year, 2, 21),  f"Kong Harald, {year - 1937} år"),
        (date(year, 3, 8),   "Kvinnedagen"),
        (date(year, 3, 20),  "Vårjevndøgn"),
        (sommer_start,        "Sommertid start"),
        (e - timedelta(4),   "Onsdag før skjærtorsdag"),
        (e - timedelta(1),   "Påskeaften"),
        (date(year, 5, 8),   "Frigjøringsdagen 1945"),
        (e + timedelta(48),  "Pinseaften"),
        (date(year, 6, 7),   "Unionsoppløsning 1905"),
        (date(year, 6, 21),  "Sommersolverv"),
        (date(year, 6, 23),  "Sankthansaften"),
        (date(year, 7, 4),   f"Dronning Sonja, {year - 1937} år"),
        (date(year, 7, 20),  f"Kronprins Haakon, {year - 1973} år"),
        (date(year, 7, 29),  "Olsokdagen"),
        (date(year, 8, 19),  f"Kronprinsesse Mette-Marit, {year - 1973} år"),
        (date(year, 9, 23),  "Høstjevndøgn"),
        (botsdag,             "Bots- og bededag"),
        (sommer_slutt,        "Sommertid slutt"),
        (date(year, 10, 31), "Halloween"),
        (date(year, 11, 1),  "Allehelgensdag"),
        (farsdag,             "Farsdag"),
        (advent1,             "1. søndag i advent"),
        (advent1 + timedelta(7),  "2. søndag i advent"),
        (date(year, 12, 13), "Luciadagen"),
        (advent1 + timedelta(14), "3. søndag i advent"),
        (advent1 + timedelta(21), "4. søndag i advent"),
        (date(year, 12, 21), "Vintersolverv"),
        (date(year, 12, 24), "Julaften"),
        (date(year, 12, 31), "Nyttårsaften"),
    ]
    entries.extend((d, name, False, d in halfs) for d, name in non_red)

    # Merge entries that fall on the same date
    merged: dict[date, tuple[list[str], bool, bool]] = {}
    for d, name, is_red, is_half in sorted(entries, key=lambda x: x[0]):
        if d in merged:
            merged[d][0].append(name)
            merged[d] = (merged[d][0], merged[d][1] or is_red, merged[d][2] or is_half)
        else:
            merged[d] = ([name], is_red, is_half)

    return [(d, " / ".join(names), is_red, is_half)
            for d, (names, is_red, is_half) in merged.items()]


# -- Calendar grid builder ----------------------------------------------------

def build_month(year: int, month: int, holidays: dict[date, str],
                notable: dict[date, str], halfs: dict[date, str],
                today: date):
    """Build a month's data for the template."""
    first = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    # Start from Monday of the first week
    monday = first - timedelta(days=first.isoweekday() - 1)

    weeks = []
    cur = monday
    while cur <= last_day:
        week = {"number": cur.isocalendar()[1], "days": []}
        for i in range(7):
            day = cur + timedelta(days=i)
            if day.month == month and day.year == year:
                is_red = day.isoweekday() == 7 or day in holidays
                is_sat = day.isoweekday() == 6 and day not in holidays
                is_half = day in halfs
                is_today = day == today
                tooltip = holidays.get(day) or notable.get(day) or ""
                if is_half:
                    tooltip = f"{tooltip} (halv dag)" if tooltip else "Halv dag"
                week["days"].append({
                    "day": day.day,
                    "is_red": is_red,
                    "is_sat": is_sat,
                    "is_half": is_half,
                    "is_today": is_today,
                    "tooltip": tooltip,
                })
            else:
                week["days"].append(None)
        weeks.append(week)
        cur += timedelta(days=7)

    # Pad to 6 weeks for uniform height
    while len(weeks) < 6:
        weeks.append({"number": "", "days": [None] * 7})

    return {
        "name": MONTHS_NO[month - 1],
        "weeks": weeks,
    }


def build_calendar(year: int):
    """Build all data needed for the template."""
    holidays = red_days(year)
    halfs = half_days(year)
    today = date.today()
    all_notable = notable_dates(year)
    notable_lookup = {d: name for d, name, _, _ in all_notable}
    months = [build_month(year, m + 1, holidays, notable_lookup, halfs, today)
              for m in range(12)]

    third = max(math.ceil(len(all_notable) / 3), 1)
    notable_columns = [all_notable[i:i + third] for i in range(0, len(all_notable), third)]

    return {
        "year": year,
        "months": months,
        "days_no": DAYS_NO,
        "mabbr_no": MABBR_NO,
        "notable_columns": notable_columns,
        "today": today,
    }


# -- Main ---------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate Norwegian calendar HTML")
    parser.add_argument("year", nargs="?", type=int, default=date.today().year)
    parser.add_argument("-o", "--output", default="dist/index.html")
    args = parser.parse_args()

    env = Environment(
        loader=FileSystemLoader(Path(__file__).parent / "templates"),
        autoescape=True,
    )
    template = env.get_template("calendar.html")

    data = build_calendar(args.year)
    html = template.render(**data)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Generated {out} for {args.year}")


if __name__ == "__main__":
    main()
