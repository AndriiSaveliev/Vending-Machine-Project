"""
CLI for the vending machine (60-character layout, optional colorama).
Small motion: spinners / dot pulses on key actions (UI-only polish).
"""
import os
import re
import sys
import time

from admin_handler import AdminHandler
from money_handler import MoneyHandler
from product_handler import InvalidSlotError, JammedSlotError, ProductHandler

# Max balance for inserts matches VendingMachine default in repo (non-UI layer).
MAX_INSERT_CENTS = 300

try:
    from colorama import Fore, Style, init

    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = ""

    class Style:
        RESET_ALL = ""


WIDTH = 60
INNER = WIDTH - 2

ADMIN_PASSWORD = os.environ.get("VENDING_ADMIN_PASSWORD", "admin")


def fmt_money(cents):
    return f"${cents / 100:,.2f}"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def ok(msg):
    return (Fore.GREEN if HAS_COLOR else "") + msg + (Style.RESET_ALL if HAS_COLOR else "")


def err(msg):
    return (Fore.RED if HAS_COLOR else "") + msg + (Style.RESET_ALL if HAS_COLOR else "")


def hi(msg):
    """Muted / info line (pause hints, sublabels)."""
    return (Fore.CYAN if HAS_COLOR else "") + msg + (Style.RESET_ALL if HAS_COLOR else "")


def _flush():
    sys.stdout.flush()


def micro_sleep(sec):
    time.sleep(sec)


def spin_line(label, frames=10):
    """Inline spinner on one line, then clear it."""
    chars = "|/-\\"
    for i in range(frames):
        c = chars[i % len(chars)]
        line = f" {label} {c}".ljust(INNER)[:INNER]
        sys.stdout.write(f"\r{line}")
        _flush()
        micro_sleep(0.065)
    sys.stdout.write("\r" + " " * INNER + "\r")
    _flush()


def dot_line(prefix, steps=4):
    """Growing dots on one line (e.g. 'Checking...')."""
    for n in range(1, steps + 1):
        tail = "." * n
        line = f" {prefix}{tail}".ljust(INNER)[:INNER]
        sys.stdout.write(f"\r{line}")
        _flush()
        micro_sleep(0.1)
    sys.stdout.write("\r" + " " * INNER + "\r")
    _flush()


STAGGER = 0.032
TYPE_DELAY = 0.011


def typewrite(text, delay=TYPE_DELAY):
    """One line, characters appear left to right."""
    t = (text or "")[:INNER]
    buf = ""
    for ch in t:
        buf += ch
        sys.stdout.write(f"\r{buf.ljust(INNER)[:INNER]}")
        _flush()
        micro_sleep(delay)
    print()


def reveal_print_lines(lines, gap=STAGGER):
    """Print block lines one after another with a tiny beat."""
    for line in lines:
        print(line)
        _flush()
        micro_sleep(gap)


def mini_celebrate(frames=5):
    """Short sparkle on one line (success feedback)."""
    seq = ("  ·", " ✦", " ✓", " ✦", "  ·")
    for i in range(frames):
        s = seq[i % len(seq)]
        line = s.ljust(INNER)[:INNER]
        sys.stdout.write(f"\r{line}")
        _flush()
        micro_sleep(0.07)
    sys.stdout.write("\r" + " " * INNER + "\r")
    _flush()
    print()


def vend_product_dots(steps=5):
    """'Vending product..' stepping dots before the mechanical vend."""
    base = " Vending product"
    for n in range(1, steps + 1):
        tail = "." * (1 + (n % 3))
        line = f"{base}{tail}".ljust(INNER)[:INNER]
        sys.stdout.write(f"\r{line}")
        _flush()
        micro_sleep(0.12)
    sys.stdout.write("\r" + " " * INNER + "\r")
    _flush()


def boot_tap():
    """Very short startup pulse (once per run)."""
    edge = "\u2554" + "\u2550" * 12 + "\u2557"
    print(edge.center(WIDTH))
    micro_sleep(0.08)
    print((" " + ok("\u25b6") + "  Vending Machine CLI").ljust(WIDTH)[:WIDTH])
    micro_sleep(0.15)
    spin_line("Loading", 8)
    print()


def horiz_double_top():
    return "\u2554" + "\u2550" * INNER + "\u2557"


def horiz_double_mid():
    return "\u2560" + "\u2550" * INNER + "\u2563"


def horiz_double_bot():
    return "\u255a" + "\u2550" * INNER + "\u255d"


def row_double(text):
    t = (text or "")[:INNER]
    return "\u2551" + t.ljust(INNER) + "\u2551"


def horiz_single_top():
    return "\u250c" + "\u2500" * INNER + "\u2510"


def horiz_single_mid():
    return "\u251c" + "\u2500" * INNER + "\u2524"


def horiz_single_bot():
    return "\u2514" + "\u2500" * INNER + "\u2518"


def row_single(text):
    t = (text or "")[:INNER]
    return "\u2502" + t.ljust(INNER) + "\u2502"


def draw_header(mh, stagger=False):
    lines = (
        horiz_double_top(),
        row_double("VENDING MACHINE v1.0".center(INNER)),
        horiz_double_mid(),
        row_double(f"  Balance: {fmt_money(mh.get_balance())}"),
        horiz_double_bot(),
    )
    if stagger:
        reveal_print_lines(lines)
    else:
        for line in lines:
            print(line)


def draw_exact_banner(mh, stagger=False):
    if not mh.needs_exact_change():
        return
    lines = (
        horiz_single_top(),
        row_single(" EXACT CHANGE ONLY - NO CHANGE AVAILABLE "),
        horiz_single_bot(),
    )
    if stagger:
        reveal_print_lines(lines)
    else:
        for line in lines:
            print(line)


def draw_products(ph, stagger_rows=False):
    head = (
        horiz_single_top(),
        row_single("AVAILABLE PRODUCTS"),
        horiz_single_mid(),
    )
    if stagger_rows:
        reveal_print_lines(head)
    else:
        for line in head:
            print(line)
    for slot in sorted(ph.get_all_products().keys()):
        p = ph.get_product(slot)
        name = (p.get("name") or "")[:16].ljust(16)
        dollars = f"${p['price_cents'] / 100:.2f}"
        if not p.get("enabled", True):
            status = "[DISABLED]"
        elif p.get("quantity", 0) <= 0:
            status = "[SOLD OUT]"
        else:
            status = f"[{p['quantity']} left]"
        line = f"  {slot}: {name}  {dollars}  {status}"
        print(row_single(line))
        if stagger_rows:
            _flush()
            micro_sleep(STAGGER * 0.85)
    print(horiz_single_bot())


def draw_main_screen(mh, ph):
    """One full customer frame with light motion."""
    draw_header(mh, stagger=True)
    draw_exact_banner(mh, stagger=True)
    draw_products(ph, stagger_rows=True)


def prompt_int(prompt, lo, hi, err_msg):
    while True:
        raw = input(prompt).strip()
        try:
            n = int(raw)
        except ValueError:
            print(err(err_msg))
            continue
        if lo <= n <= hi:
            return n
        print(err(err_msg))


def pause(msg=None):
    if msg:
        print(msg)
    print(hi("  ▸ Press Enter to continue..."))
    input()


def run_insert_coins(mh, ph):
    while True:
        clear_screen()
        draw_main_screen(mh, ph)
        print()
        typewrite(" INSERT COINS")
        reveal_print_lines(
            (
                " [1] Quarter ($0.25)",
                " [2] Dollar Coin ($1.00)",
                " [0] Done",
            )
        )
        choice = prompt_int(
            "\nEnter choice: ",
            0,
            2,
            "✗ Invalid choice - please enter 0, 1, or 2",
        )
        if choice == 0:
            break
        if choice == 1:
            spin_line("Taking coin", 7)
            if mh.insert_coin(25, MAX_INSERT_CENTS):
                print(f"Balance:{fmt_money(mh.get_balance())}")
                dot_line("Crediting", 3)
                print(ok("✓ Coin inserted: $0.25 added to balance"))
                mini_celebrate(4)
            else:
                print(err("✗ Maximum balance reached"))
        elif choice == 2:
            spin_line("Taking coin", 7)
            if mh.insert_coin(100, MAX_INSERT_CENTS):
                print(f"Balance:{fmt_money(mh.get_balance())}")
                dot_line("Crediting", 3)
                print(ok("✓ Coin inserted: $1.00 added to balance"))
                mini_celebrate(4)
            else:
                print(err("✗ Maximum balance reached"))
        pause()


def run_vend_flow(mh, ph, slot):
    """Same flow as VendingMachine.vend_product (repo version), called from UI only."""
    balance = mh.get_balance()
    price = ph.get_price(slot)
    if price is None:
        print("Invalid selection")
        return
    if balance >= price:
        vend_success = False
        vend_product_dots(6)
        try:
            ph.vend(slot)
            vend_success = True
        except JammedSlotError:
            spin_line("Jam", 5)
            print("Vend failed")
        except ValueError as e:
            print(str(e))
            return
        if vend_success:
            if balance > price:
                dot_line("Dispensing change", 3)
            change = mh.make_change(price)
            print(f"Change due:{change}")
            print("Thank you.")
            mini_celebrate(5)
    else:
        remaining = price - balance
        print(f"Deposit {fmt_money(remaining)} more.")


def run_select_product(mh, ph):
    clear_screen()
    draw_main_screen(mh, ph)
    slot = input("\nEnter product slot (e.g. A1): ").strip().upper()
    if not re.match(r"^[A-Z]\d+$", slot):
        print(err("✗ Invalid slot selection - format should be A1, B2, etc."))
        pause()
        return
    spin_line("Checking selection", 6)
    run_vend_flow(mh, ph, slot)
    pause()


def run_coin_return(mh, ph):
    clear_screen()
    draw_main_screen(mh, ph)
    spin_line("Opening coin return", 9)
    balance = mh.get_balance()
    print("Cancelling transaction.")
    dot_line("Counting coins", 3)
    print(f"Returning {fmt_money(balance)}")
    spin_line("Returning", 6)
    mh.return_coins()
    mini_celebrate(3)
    pause()


def parse_price_to_cents(text):
    return int(round(float(text.strip()) * 100))


def run_admin(mh, ph):
    dot_line("Auth", 3)
    pw = input("Admin password: ").strip()
    if pw != ADMIN_PASSWORD:
        spin_line("Denied", 6)
        print(err("✗ Authentication failed"))
        pause()
        return
    spin_line("Welcome admin", 8)
    admin = AdminHandler()
    while True:
        clear_screen()
        draw_header(mh, stagger=True)
        draw_exact_banner(mh, stagger=True)
        print()
        typewrite(" ADMIN MENU")
        reveal_print_lines(
            (
                " [1] Change Product Price",
                " [2] Enable/Disable Slot",
                " [3] Restock Product",
                " [4] View Reports",
                " [5] Toggle Exact Change Mode",
                " [0] Exit Admin Mode",
            )
        )
        choice = prompt_int(
            "\nEnter choice: ",
            0,
            5,
            "✗ Invalid choice - please enter a number between 0 and 5",
        )
        if choice == 0:
            break
        if choice == 1:
            slot = input("Slot (e.g. A1): ").strip().upper()
            if not re.match(r"^[A-Z]\d+$", slot):
                print(err("✗ Invalid slot selection - format should be A1, B2, etc."))
                pause()
                continue
            raw_price = input("New price in dollars (quarter increments, e.g. 1.50): ").strip()
            try:
                new_cents = parse_price_to_cents(raw_price)
            except ValueError:
                print(err("✗ Price must be a valid decimal number"))
                pause()
                continue
            old = ph.get_price(slot)
            if old is None:
                print(err("✗ Invalid slot selection"))
                pause()
                continue
            try:
                ph.set_price(slot, new_cents)
            except InvalidSlotError:
                print(err("✗ Invalid slot selection"))
                pause()
                continue
            except ValueError:
                print(
                    err(
                        "✗ Price must be in quarter increments ($0.25, $0.50, $0.75, etc.)"
                    )
                )
                pause()
                continue
            dot_line("Saving price", 3)
            print(ok("✓ Price updated successfully"))
            mini_celebrate(3)
            pause()
        elif choice == 2:
            slot = input("Slot to toggle (e.g. B1): ").strip().upper()
            if not re.match(r"^[A-Z]\d+$", slot):
                print(err("✗ Invalid slot selection"))
                pause()
                continue
            prod = ph.get_product(slot)
            if prod is None:
                print(err("✗ Invalid slot selection"))
                pause()
                continue
            if prod.get("enabled", True):
                ph.disable_slot(slot)
            else:
                ph.enable_slot(slot)
            spin_line("Updating slot", 7)
            print(ok("✓ Slot status updated"))
            mini_celebrate(3)
            pause()
        elif choice == 3:
            slot = input("Slot to restock (e.g. A1): ").strip().upper()
            if not re.match(r"^[A-Z]\d+$", slot):
                print(err("✗ Invalid slot selection"))
                pause()
                continue
            if ph.get_product(slot) is None:
                print(err("✗ Invalid slot selection"))
                pause()
                continue
            try:
                qty = int(input("New quantity: ").strip())
            except ValueError:
                print(err("✗ Invalid quantity"))
                pause()
                continue
            try:
                ph.set_qty(slot, qty)
            except ValueError as e:
                print(err(f"✗ {e}"))
                pause()
                continue
            dot_line("Restocking", 3)
            print(ok("✓ Product restocked successfully"))
            mini_celebrate(3)
            pause()
        elif choice == 4:
            clear_screen()
            spin_line("Crunching numbers", 10)
            report = admin.generate_report()
            if report:
                print(report)
            else:
                print(
                    hi(
                        " (No report text yet — AdminHandler.generate_report is a stub.) "
                    )
                )
            pause()
        elif choice == 5:
            spin_line("Toggling mode", 7)
            mh.set_exact_change(not mh.needs_exact_change())
            print(ok("✓ Exact change mode toggled"))
            mini_celebrate(3)
            pause()


def console_ui():
    if not HAS_COLOR:
        print(
            "Install 'colorama' for colored output: pip install colorama\n"
        )

    try:
        ph = ProductHandler()
    except OSError:
        print(err("✗ Product file not found - please contact administrator"))
        sys.exit(1)
    except Exception:
        print(err("✗ Error loading product data - using default configuration"))
        ph = ProductHandler()

    mh = MoneyHandler()

    clear_screen()
    boot_tap()

    while True:
        clear_screen()
        draw_main_screen(mh, ph)
        print()
        typewrite(" MAIN MENU")
        reveal_print_lines(
            (
                " [1] Insert Coin",
                " [2] Select Product",
                " [3] Coin Return",
                " [4] Admin Login",
                " [0] Exit",
            )
        )
        choice = prompt_int(
            "\nEnter choice: ",
            0,
            4,
            "✗ Invalid choice - please enter a number between 0 and 4",
        )
        if choice == 0:
            clear_screen()
            dot_line("Shutting down", 3)
            spin_line("Bye", 6)
            print(ok(" Goodbye — thanks for visiting. "))
            micro_sleep(0.35)
            break
        if choice == 1:
            run_insert_coins(mh, ph)
        elif choice == 2:
            run_select_product(mh, ph)
        elif choice == 3:
            run_coin_return(mh, ph)
        elif choice == 4:
            run_admin(mh, ph)


def main():
    console_ui()


if __name__ == "__main__":
    main()
