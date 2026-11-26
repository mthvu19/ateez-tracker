"""Gui Discord (neu co secret DISCORD_WEBHOOK): tin chinh thuc moi + nhac deadline trong 24 gio."""
import os

from .common import VN, parse_iso

def _vn(s):
    d = parse_iso(s)
    return d.astimezone(VN).strftime("%H:%M %d/%m") if d else ""


def build_lines(new_items, reminders):
    lines = []
    important = [i for i in new_items if i.get("tier") == "official" or i.get("category") in ("tour", "charts")]
    if important:
        lines.append(f"🆕 **{len(important)} new updates**")
        for i in important[:15]:
            t = i.get("title_en") or i.get("title")
            lines.append(f"• [{i.get('category_label', '')}] {t} — {i.get('account')} · <{i['url']}>")
    if reminders:
        lines += ["", "⏰ **Due within 24h** (VN time)"]
        for e in reminders:
            lines.append(f"• **{_vn(e['when'])}** — {e['label']} ({e['title']}) · <{e['url']}>")
    return lines


def send(lines, http, log=print):
    hook = os.environ.get("DISCORD_WEBHOOK", "").strip()
    if not hook or not lines:
        log("[discord] bo qua (khong co webhook hoac khong co gi moi)")
        return
    page = os.environ.get("PAGE_URL", "")
    if page:
        lines = lines + ["", f"Tracker: {page}"]
    chunk = ""
    for line in lines:
        if len(chunk) + len(line) > 1800:
            http.post(hook, json={"username": "ATEEZ Tracker", "content": chunk}, timeout=30).raise_for_status()
            chunk = ""
        chunk += line + "\n"
    http.post(hook, json={"username": "ATEEZ Tracker", "content": chunk}, timeout=30).raise_for_status()
    log(f"[discord] da gui {len(lines)} dong")
