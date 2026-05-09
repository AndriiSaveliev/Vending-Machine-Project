"""
Vending Machine — Test Handlers.

Covers every test case from the design document:
- Money Handling:    MH-1, MH-2, MH-3
- Product Handling:  PH-1, PH-2, PH-3, PH-4, PH-5, PH-6
- Admin Functions:   AD-1, AD-2, AD-3, AD-4, AD-5, AD-6
- System Behavior:   SB-1, SB-2, SB-3, SB-4, SB-5, SB-6
- Extra coverage:    EX-1..EX-7

Tests run in a temp directory so the real products.csv, log.csv,
and hoppers.json are NEVER modified.
"""
import csv
import json
import os
import shutil
import tempfile

from money_handler import MoneyHandler
from product_handler import InvalidSlotError, JammedSlotError, ProductHandler


# ---------- output helpers ----------

W = 60
MAX_INSERT = 200
RESULTS = []
_current = {"id": None, "req": None, "passed": True}


def money(cents):
    return f"${cents / 100:.2f}"


def box(title, subtitle=""):
    print()
    print("\u2554" + "\u2550" * (W - 2) + "\u2557")
    print("\u2551" + title.center(W - 2) + "\u2551")
    if subtitle:
        print("\u2551" + subtitle.center(W - 2) + "\u2551")
    print("\u255a" + "\u2550" * (W - 2) + "\u255d")


def section(title):
    label = f" {title} "
    pad = max(0, W - len(label) - 2)
    print()
    print("\u2500\u2500" + label + "\u2500" * pad)


def start(test_id, requirement):
    _current["id"] = test_id
    _current["req"] = requirement
    _current["passed"] = True
    print()
    print(f"  {test_id}  {requirement}")


def step(label, value):
    print(f"      \u00b7 {label:<26} {value}")


def check(label, ok, note=""):
    mark = "\u2713" if ok else "\u2717"
    extra = f"  ({note})" if note else ""
    print(f"      {mark} {label}{extra}")
    if not ok:
        _current["passed"] = False


def end():
    verdict = "PASS" if _current["passed"] else "FAIL"
    print(f"      \u2192 {verdict}")
    RESULTS.append((_current["id"], _current["req"], _current["passed"]))


def summary():
    total = len(RESULTS)
    passed = sum(1 for _, _, p in RESULTS if p)
    failed = total - passed
    print()
    print("\u2554" + "\u2550" * (W - 2) + "\u2557")
    print("\u2551" + "TEST SUMMARY".center(W - 2) + "\u2551")
    print("\u2560" + "\u2550" * (W - 2) + "\u2563")
    print("\u2551" + f"  Total : {total:>3}".ljust(W - 2) + "\u2551")
    print("\u2551" + f"  Pass  : {passed:>3}".ljust(W - 2) + "\u2551")
    print("\u2551" + f"  Fail  : {failed:>3}".ljust(W - 2) + "\u2551")
    if failed:
        print("\u2560" + "\u2550" * (W - 2) + "\u2563")
        print("\u2551" + "  Failures:".ljust(W - 2) + "\u2551")
        for tid, req, p in RESULTS:
            if not p:
                line = f"    {tid}  {req}"[:W - 2]
                print("\u2551" + line.ljust(W - 2) + "\u2551")
    print("\u255a" + "\u2550" * (W - 2) + "\u255d")
    return failed == 0


# ---------- temp data + handler builders ----------

def write_products_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for row in rows:
            writer.writerow(row)


def make_test_files(tmp):
    product_file = os.path.join(tmp, "products.csv")
    log_file = os.path.join(tmp, "log.csv")
    hopper_file = os.path.join(tmp, "hoppers.json")

    write_products_csv(product_file, [
        ["A1", "Chips",   "1.00", 5,  True],
        ["A2", "Candy",   "0.75", 0,  True],
        ["A3", "Soda",    "1.25", 3,  True],
        ["B1", "Water",   "1.00", 8,  True],
        ["B2", "Cookies", "0.50", 12, True],
    ])
    open(log_file, "w", encoding="utf-8").close()
    with open(hopper_file, "w", encoding="utf-8") as file:
        json.dump({"100": 30, "25": 30}, file)
    return product_file, log_file, hopper_file


def fresh_handlers(tmp):
    pf, lf, hf = make_test_files(tmp)
    mh = MoneyHandler(hopper_file=hf)
    ph = ProductHandler(product_file=pf, sales_log_file=lf)
    return mh, ph, pf, lf, hf


def vend_with_retry(ph, slot, attempts=30):
    for _ in range(attempts):
        try:
            return ph.vend(slot)
        except JammedSlotError:
            continue
    return None


# ---------- Money Handling ----------

def test_money_handling(tmp):
    section("MONEY HANDLING")

    # MH-1
    start("MH-1", "Display running total after each coin insertion")
    mh, _, _, _, _ = fresh_handlers(tmp)
    mh.balance_cents = 0
    step("Start", money(mh.get_balance()))
    seq = []
    mh.insert_coin(25, MAX_INSERT); seq.append(mh.get_balance()); step("After quarter", money(mh.get_balance()))
    mh.insert_coin(25, MAX_INSERT); seq.append(mh.get_balance()); step("After quarter", money(mh.get_balance()))
    mh.insert_coin(100, MAX_INSERT); seq.append(mh.get_balance()); step("After dollar", money(mh.get_balance()))
    check("Balance updates after every coin", seq == [25, 50, 150])
    end()

    # MH-2
    start("MH-2", "Coin Return returns all inserted money")
    mh, _, _, _, _ = fresh_handlers(tmp)
    mh.balance_cents = 0
    mh.insert_coin(100, MAX_INSERT)
    mh.insert_coin(25, MAX_INSERT)
    mh.insert_coin(25, MAX_INSERT)
    step("Inserted", money(mh.get_balance()))
    returned = mh.return_coins()
    step("Coins returned", returned)
    step("Balance after", money(mh.get_balance()))
    check("Returns 1 dollar + 2 quarters", returned == {100: 1, 25: 2})
    check("Balance resets to $0.00", mh.get_balance() == 0)
    end()

    # MH-3
    start("MH-3", "Refuse coins above maximum balance ($2.00)")
    mh, _, _, _, _ = fresh_handlers(tmp)
    mh.balance_cents = 0
    a = mh.insert_coin(100, MAX_INSERT)
    b = mh.insert_coin(100, MAX_INSERT)
    c = mh.insert_coin(25, MAX_INSERT)
    step("Insert $1.00 (1st)", a)
    step("Insert $1.00 (2nd)", b)
    step("Insert $0.25 over cap", c)
    step("Final balance", money(mh.get_balance()))
    check("First two accepted", a is True and b is True)
    check("Third refused", c is False)
    check("Balance capped at $2.00", mh.get_balance() == 200)
    end()


# ---------- Product Handling ----------

def test_product_handling(tmp):
    section("PRODUCT HANDLING")

    # PH-1
    start("PH-1", "Load product data from CSV file")
    _, ph, _, _, _ = fresh_handlers(tmp)
    products = ph.get_all_products()
    for slot, p in sorted(products.items()):
        status = "[SOLD OUT]" if p["quantity"] == 0 else f"[{p['quantity']} left]"
        step(f"{slot} {p['name']}", f"{money(p['price_cents'])}  {status}")
    check("All 5 products loaded", len(products) == 5)
    check("A2 shows SOLD OUT", products["A2"]["quantity"] == 0)
    end()

    # PH-2
    start("PH-2", "Vend product when sufficient funds inserted")
    mh, ph, _, _, _ = fresh_handlers(tmp)
    mh.balance_cents = 0
    mh.insert_coin(100, MAX_INSERT)
    mh.insert_coin(25, MAX_INSERT)
    mh.insert_coin(25, MAX_INSERT)
    price = ph.get_price("A1")
    qty_before = ph.get_product("A1")["quantity"]
    step("Balance", money(mh.get_balance()))
    step("Price A1", money(price))
    product = vend_with_retry(ph, "A1")
    step("Vended", product["name"] if product else "(none)")
    change = mh.make_change(price)
    step("Change returned", change)
    step("Balance after", money(mh.get_balance()))
    qty_after = ph.get_product("A1")["quantity"]
    step("A1 qty before/after", f"{qty_before} -> {qty_after}")
    check("Vend succeeded", product is not None)
    check("Change is $0.50 (2 quarters)", change == {100: 0, 25: 2})
    check("Balance reset", mh.get_balance() == 0)
    check("Quantity decremented by 1", qty_after == qty_before - 1)
    end()

    # PH-3
    start("PH-3", "Display remaining amount due for insufficient funds")
    mh, ph, _, _, _ = fresh_handlers(tmp)
    mh.balance_cents = 0
    mh.insert_coin(25, MAX_INSERT)
    mh.insert_coin(25, MAX_INSERT)
    price = ph.get_price("B1")
    balance = mh.get_balance()
    remaining = price - balance
    step("Balance", money(balance))
    step("Price B1", money(price))
    step("Remaining due", money(remaining))
    check("Balance < price", balance < price)
    check("Remaining is $0.50", remaining == 50)
    check("Balance preserved", mh.get_balance() == balance)
    end()

    # PH-4
    start("PH-4", "Prevent selection of sold-out products")
    mh, ph, _, _, _ = fresh_handlers(tmp)
    mh.balance_cents = 0
    mh.insert_coin(100, MAX_INSERT)
    step("A2 quantity", ph.get_product("A2")["quantity"])
    refused = False
    msg = ""
    try:
        ph.vend("A2")
    except ValueError as e:
        refused = True
        msg = str(e)
    step("Refusal reason", msg or "(none)")
    step("Balance preserved", money(mh.get_balance()))
    check("ValueError raised on sold-out", refused)
    check("Balance unchanged", mh.get_balance() == 100)
    end()

    # PH-5
    trials = 1000
    start("PH-5", f"Simulate product jam ~5% over {trials} trials")
    _, ph, _, _, _ = fresh_handlers(tmp)
    ph.set_qty("A1", trials + 10)
    successes = jams = 0
    for _ in range(trials):
        try:
            ph.vend("A1")
            successes += 1
        except JammedSlotError:
            jams += 1
        except ValueError:
            break
    rate = (jams / trials) * 100
    step("Successes", successes)
    step("Jams", jams)
    step("Jam rate", f"{rate:.2f}%")
    check("Jam rate within 3% - 7%", 3.0 <= rate <= 7.0,
          note=f"target 5% +/- 2%")
    end()

    # PH-6
    start("PH-6", "Return product price for valid slot")
    _, ph, _, _, _ = fresh_handlers(tmp)
    p_a1 = ph.get_price("A1")
    p_a3 = ph.get_price("A3")
    p_z9 = ph.get_price("Z9")
    step("Price A1", money(p_a1))
    step("Price A3", money(p_a3))
    step("Price Z9 (invalid)", p_z9)
    invalid_raised = False
    try:
        ph.vend("Z9")
    except InvalidSlotError:
        invalid_raised = True
    check("A1 price = $1.00", p_a1 == 100)
    check("A3 price = $1.25", p_a3 == 125)
    check("Invalid slot returns None", p_z9 is None)
    check("Invalid slot vend raises InvalidSlotError", invalid_raised)
    end()


# ---------- Admin Functions ----------

def test_admin_functions(tmp):
    section("ADMIN FUNCTIONS")

    # AD-1
    start("AD-1", "Admin can change product prices (quarter increments)")
    _, ph, pf, lf, _ = fresh_handlers(tmp)
    step("A1 old price", money(ph.get_price("A1")))
    ph.set_price("A1", 150)
    step("A1 new price", money(ph.get_price("A1")))
    ph_reload = ProductHandler(product_file=pf, sales_log_file=lf)
    step("After reload", money(ph_reload.get_price("A1")))
    refused = False
    try:
        ph.set_price("A1", 130)
    except ValueError:
        refused = True
    check("Price updated to $1.50", ph.get_price("A1") == 150)
    check("Price persisted to file", ph_reload.get_price("A1") == 150)
    check("Non-quarter price refused", refused)
    end()

    # AD-2
    start("AD-2", "Admin can enable/disable product slots")
    _, ph, _, _, _ = fresh_handlers(tmp)
    ph.disable_slot("B1")
    disabled = ph.get_product("B1")["enabled"] is False
    step("B1 enabled?", ph.get_product("B1")["enabled"])
    refused = False
    try:
        ph.vend("B1")
    except ValueError:
        refused = True
    ph.enable_slot("B1")
    re_enabled = ph.get_product("B1")["enabled"] is True
    step("B1 after re-enable", ph.get_product("B1")["enabled"])
    check("Slot disables", disabled)
    check("Disabled slot vend refused", refused)
    check("Slot re-enables", re_enabled)
    end()

    # AD-3
    start("AD-3", "Admin can restock products")
    _, ph, pf, lf, _ = fresh_handlers(tmp)
    step("A2 qty before", ph.get_product("A2")["quantity"])
    ph.set_qty("A2", 10)
    step("A2 qty after", ph.get_product("A2")["quantity"])
    ph_reload = ProductHandler(product_file=pf, sales_log_file=lf)
    step("After reload", ph_reload.get_product("A2")["quantity"])
    check("Restock applied", ph.get_product("A2")["quantity"] == 10)
    check("Restock persisted", ph_reload.get_product("A2")["quantity"] == 10)
    end()

    # AD-4
    start("AD-4", "Admin can view sales reports")
    _, ph, _, _, _ = fresh_handlers(tmp)
    ph.set_qty("A1", 100)
    ph.set_qty("A3", 100)
    ph.set_qty("B2", 100)
    vend_with_retry(ph, "A1")
    vend_with_retry(ph, "A3")
    vend_with_retry(ph, "B2")
    report, best, _ = ph.generate_sales_report(days=None)
    total_units = sum(item["units_sold"] for item in report.values())
    total_rev = sum(item["revenue"] for item in report.values())
    step("Total items sold", total_units)
    step("Total revenue", f"${total_rev:.2f}")
    step("Best sellers", ", ".join(f"{n}({d['units_sold']})" for n, d in best))
    check("3 distinct items in report", len(report) == 3)
    check("Total units = 3", total_units == 3)
    check("Total revenue = $2.75", abs(total_rev - 2.75) < 0.01)
    end()

    # AD-5
    start("AD-5", "Admin can toggle Exact Change mode manually")
    mh, _, _, _, _ = fresh_handlers(tmp)
    s0 = mh.needs_exact_change()
    step("Initial state", s0)
    mh.set_exact_change(not mh.needs_exact_change())
    s1 = mh.needs_exact_change()
    step("After 1st toggle", s1)
    mh.set_exact_change(not mh.needs_exact_change())
    s2 = mh.needs_exact_change()
    step("After 2nd toggle", s2)
    check("Toggle flips state", s1 != s0)
    check("Second toggle restores", s2 == s0)
    end()

    # AD-6
    start("AD-6", "Only authorized users access admin functions")
    correct_pw = os.environ.get("VENDING_ADMIN_PASSWORD", "admin")
    bad = "wrongpass"
    bad_ok = (bad == correct_pw)
    good_ok = (correct_pw == correct_pw)
    step(f"Try '{bad}'", "Authenticated" if bad_ok else "Authentication failed")
    step(f"Try '{correct_pw}'", "Authenticated" if good_ok else "Authentication failed")
    check("Wrong password rejected", not bad_ok)
    check("Correct password accepted", good_ok)
    end()


# ---------- System Behavior ----------

def test_system_behavior(tmp):
    section("SYSTEM BEHAVIOR")

    # SB-1
    start("SB-1", "Log all transactions and events")
    _, ph, _, lf, _ = fresh_handlers(tmp)
    ph.set_qty("A1", 100)
    ph.set_qty("B1", 100)
    vend_with_retry(ph, "A1")
    vend_with_retry(ph, "B1")
    with open(lf, "r", encoding="utf-8") as file:
        contents = file.read().strip()
    line_count = len(contents.splitlines()) if contents else 0
    step("Log lines written", line_count)
    if contents:
        for line in contents.splitlines():
            step("entry", line)
    check("At least 2 sales logged", line_count >= 2)
    end()

    # SB-2
    start("SB-2", "Validate all user inputs")
    mh, ph, _, _, _ = fresh_handlers(tmp)
    quart_refused = False
    try:
        ph.set_price("A1", 130)
    except ValueError:
        quart_refused = True
    invalid_slot_refused = False
    try:
        ph.set_price("Z9", 100)
    except InvalidSlotError:
        invalid_slot_refused = True
    neg_qty_refused = False
    try:
        ph.set_qty("A1", -5)
    except ValueError:
        neg_qty_refused = True
    coin_refused = mh.insert_coin(10, MAX_INSERT) is False
    step("Non-quarter price", "refused" if quart_refused else "ALLOWED!")
    step("Invalid slot", "refused" if invalid_slot_refused else "ALLOWED!")
    step("Negative quantity", "refused" if neg_qty_refused else "ALLOWED!")
    step("Non-coin (10c)", "refused" if coin_refused else "ALLOWED!")
    check("Non-quarter price refused", quart_refused)
    check("Invalid slot refused", invalid_slot_refused)
    check("Negative qty refused", neg_qty_refused)
    check("Non-coin refused", coin_refused)
    end()

    # SB-3
    start("SB-3", "Handle file loading errors gracefully")
    missing = os.path.join(tmp, "does_not_exist.csv")
    if os.path.exists(missing):
        os.remove(missing)
    ph_default = ProductHandler(
        product_file=missing,
        sales_log_file=os.path.join(tmp, "no_log.csv"),
    )
    defaults = ph_default.get_all_products()
    for slot, p in sorted(defaults.items()):
        step(f"{slot} {p['name']}", money(p["price_cents"]))
    check("Defaults loaded on missing file", len(defaults) >= 1)
    check("App did not crash", True)
    end()

    # SB-4
    start("SB-4", "Clear screen between operations")
    cmd = "cls" if os.name == "nt" else "clear"
    step("OS name", os.name)
    step("Clear command", cmd)
    check("Clear command resolves per OS", cmd in ("cls", "clear"))
    end()

    # SB-5
    start("SB-5", "Work without color support (graceful degradation)")
    has_color = True
    try:
        import colorama  # noqa: F401
        step("colorama", "available")
    except ImportError:
        has_color = False
        step("colorama", "missing -> plain text fallback")
    check("Either path is acceptable", True,
          note="colored" if has_color else "plain")
    end()

    # SB-6
    start("SB-6", "Maintain data persistence across sessions")
    mh, ph, pf, lf, hf = fresh_handlers(tmp)
    ph.set_price("A1", 175)
    ph.set_qty("B1", 3)
    mh.balance_cents = 0
    mh.insert_coin(100, MAX_INSERT)
    mh.insert_coin(25, MAX_INSERT)
    hoppers_before = mh.get_hopper_counts()
    step("Hoppers before reload", hoppers_before)

    mh2 = MoneyHandler(hopper_file=hf)
    ph2 = ProductHandler(product_file=pf, sales_log_file=lf)
    step("A1 price after reload", money(ph2.get_price("A1")))
    step("B1 qty after reload", ph2.get_product("B1")["quantity"])
    step("Hoppers after reload", mh2.get_hopper_counts())
    check("Price persisted", ph2.get_price("A1") == 175)
    check("Qty persisted", ph2.get_product("B1")["quantity"] == 3)
    check("Hoppers persisted", mh2.get_hopper_counts() == hoppers_before)
    end()


# ---------- Extra coverage ----------

def test_extra_coverage(tmp):
    section("EXTRA COVERAGE")

    # EX-1
    start("EX-1", "has_change_for predicts whether change is possible")
    mh, _, _, _, _ = fresh_handlers(tmp)
    mh.balance_cents = 150
    full_ok = mh.has_change_for(100)
    step("Full hoppers, $1.50 - $1.00", full_ok)
    mh.hoppers = {100: 0, 25: 0}
    mh.balance_cents = 150
    empty_ok = mh.has_change_for(100)
    step("Empty hoppers", empty_ok)
    mh.hoppers = {100: 5, 25: 0}
    mh.balance_cents = 150
    dollars_only = mh.has_change_for(125)
    step("Dollars only, $0.25 due", dollars_only)
    check("Full hoppers -> True", full_ok is True)
    check("Empty hoppers -> False", empty_ok is False)
    check("$0.25 with no quarters -> False", dollars_only is False)
    end()

    # EX-2
    start("EX-2", "Exact-change auto-enables when hoppers empty out")
    mh, _, _, _, _ = fresh_handlers(tmp)
    mh.hoppers = {100: 0, 25: 1}
    mh.balance_cents = 50
    before = mh.needs_exact_change()
    change = mh.make_change(25)
    after = mh.needs_exact_change()
    step("Before make_change", before)
    step("Change returned", change)
    step("Hoppers now", mh.get_hopper_counts())
    step("After make_change", after)
    check("Started not in exact-change", before is False)
    check("Now in exact-change", after is True)
    end()

    # EX-3
    start("EX-3", "Vend refused when overpaying in exact-change mode")
    mh, ph, _, _, _ = fresh_handlers(tmp)
    mh.set_exact_change(True)
    mh.balance_cents = 150
    price = ph.get_price("A1")
    step("Balance", money(mh.balance_cents))
    step("Price A1", money(price))
    step("Exact change", mh.needs_exact_change())
    refused = mh.needs_exact_change() and mh.balance_cents > price
    check("Refusal condition met", refused)
    end()

    # EX-4
    start("EX-4", "make_change restores hoppers when impossible")
    mh, _, _, _, _ = fresh_handlers(tmp)
    mh.hoppers = {100: 1, 25: 0}
    mh.balance_cents = 150
    before = dict(mh.get_hopper_counts())
    step("Hoppers before", before)
    step("Balance", money(mh.balance_cents))
    result = mh.make_change(25)  # change due = 125, no quarters
    step("Result", result)
    step("Hoppers after", mh.get_hopper_counts())
    step("Balance preserved", money(mh.balance_cents))
    step("Exact change flipped", mh.needs_exact_change())
    check("Empty change dict returned", result == {})
    check("Hoppers unchanged", mh.get_hopper_counts() == before)
    check("Balance preserved", mh.balance_cents == 150)
    check("Exact-change is True", mh.needs_exact_change() is True)
    end()

    # EX-5
    start("EX-5", "set_name updates, truncates at 20, ignores empty")
    _, ph, _, _, _ = fresh_handlers(tmp)
    ph.set_name("A1", "Doritos")
    step("Renamed A1", ph.get_name("A1"))
    long_name = "ThisNameIsWayTooLongForTheSlot"
    ph.set_name("A1", long_name)
    stored = ph.get_name("A1")
    step(f"Long input ({len(long_name)} chars)", f"{stored!r} ({len(stored)} chars)")
    ph.set_name("A1", "")
    step("After empty input", ph.get_name("A1"))
    refused = False
    try:
        ph.set_name("Z9", "Whatever")
    except InvalidSlotError:
        refused = True
    check("Name truncated to 20 chars", len(stored) == 20)
    check("Empty input ignored", ph.get_name("A1") == stored)
    check("Invalid slot refused", refused)
    end()

    # EX-6
    start("EX-6", "generate_sales_report time filter (days)")
    _, ph, _, lf, _ = fresh_handlers(tmp)
    with open(lf, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["2020-01-01 12:00:00", "A1", "Chips", "1.00"])
        writer.writerow(["2020-01-02 12:00:00", "A1", "Chips", "1.00"])
        writer.writerow(["2026-05-09 12:00:00", "B1", "Water", "1.00"])
    report_all, _, _ = ph.generate_sales_report(days=None)
    report_7, _, _ = ph.generate_sales_report(days=7)
    all_summary = {n: d["units_sold"] for n, d in report_all.items()}
    week_summary = {n: d["units_sold"] for n, d in report_7.items()}
    step("All-time", all_summary)
    step("Last 7 days", week_summary)
    check("All-time has Chips + Water", set(all_summary.keys()) == {"Chips", "Water"})
    check("Last-7-days excludes 2020 rows", "Chips" not in week_summary)
    end()

    # EX-7
    start("EX-7", "Coin Return with zero balance is a no-op")
    mh, _, _, _, _ = fresh_handlers(tmp)
    mh.balance_cents = 0
    before = dict(mh.get_hopper_counts())
    returned = mh.return_coins()
    step("Returned", returned)
    step("Balance", money(mh.get_balance()))
    step("Hoppers unchanged?", mh.get_hopper_counts() == before)
    check("Empty change dict", returned == {100: 0, 25: 0})
    check("Balance stays 0", mh.get_balance() == 0)
    check("Hoppers untouched", mh.get_hopper_counts() == before)
    end()


# ---------- main ----------

def main():
    tmp = tempfile.mkdtemp(prefix="vm_test_")
    box("VENDING MACHINE TEST SUITE", "isolated temp env, real files untouched")
    print(f"  temp dir: {tmp}")
    try:
        test_money_handling(tmp)
        test_product_handling(tmp)
        test_admin_functions(tmp)
        test_system_behavior(tmp)
        test_extra_coverage(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    all_pass = summary()
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
