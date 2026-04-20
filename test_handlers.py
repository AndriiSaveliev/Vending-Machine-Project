from money_handler import MoneyHandler
from product_handler import ProductHandler, JammedSlotError, InvalidSlotError


def cents_to_dollars(cents):
    return f"${cents / 100:.2f}"


def print_section(title):
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


def test_money_handler():
    print_section("TESTING MONEY HANDLER")

    mh = MoneyHandler()

    # reset balance for clean test
    mh.balance_cents = 0

    print("\n1. Insert valid coins")
    print("Insert quarter:", mh.insert_coin(25, 200))
    print("Insert dollar:", mh.insert_coin(100, 200))
    print("Balance:", mh.get_balance(), cents_to_dollars(mh.get_balance()))

    print("\n2. Test max balance")
    mh.balance_cents = 0
    print("Insert $1:", mh.insert_coin(100, 200))
    print("Insert $1:", mh.insert_coin(100, 200))
    print("Insert $0.25 over limit:", mh.insert_coin(25, 200))  # should be False
    print("Balance should stay 200:", mh.get_balance(), cents_to_dollars(mh.get_balance()))

    print("\n3. Test return_coins")
    mh.balance_cents = 0
    mh.insert_coin(25, 200)
    mh.insert_coin(100, 200)
    returned = mh.return_coins()
    print("Returned coins:", returned)
    print("Balance after return:", mh.get_balance())

    print("\n4. Test make_change after purchase")
    mh.balance_cents = 0
    mh.insert_coin(100, 200)
    mh.insert_coin(25, 200)
    change = mh.make_change(100)   # inserted 125, price 100 -> should return 25
    print("Change after $1.00 purchase from $1.25:", change)
    print("Balance after change:", mh.get_balance())

    print("\n5. Hopper counts")
    print("Hoppers:", mh.get_hopper_counts())
    print("Needs exact change:", mh.needs_exact_change())


def test_product_handler():
    print_section("TESTING PRODUCT HANDLER")

    ph = ProductHandler()

    print("\n1. Load all products")
    print("All products:", ph.get_all_products())

    print("\n2. Get valid price")
    print("Price A1:", ph.get_price("A1"))

    print("\n3. Get invalid price")
    print("Price Z9:", ph.get_price("Z9"))   # should be None

    print("\n4. Test invalid slot vend")
    try:
        ph.vend("Z9")
    except Exception as e:
        print("Invalid slot error:", type(e).__name__, "-", e)

    print("\n5. Test sold out slot")
    try:
        ph.vend("A2")   # quantity is 0 in your file
    except Exception as e:
        print("Sold out error:", type(e).__name__, "-", e)

    print("\n6. Test disable/enable slot")
    try:
        ph.disable_slot("B1")
        print("B1 after disable:", ph.get_product("B1"))

        try:
            ph.vend("B1")
        except Exception as e:
            print("Disabled slot vend error:", type(e).__name__, "-", e)

        ph.enable_slot("B1")
        print("B1 after enable:", ph.get_product("B1"))
    except Exception as e:
        print("Enable/disable test error:", type(e).__name__, "-", e)

    print("\n7. Test valid price update")
    try:
        ph.set_price("A1", 150)
        print("A1 new price:", ph.get_price("A1"))
    except Exception as e:
        print("Set price error:", type(e).__name__, "-", e)

    print("\n8. Test invalid price update")
    try:
        ph.set_price("A1", 130)   # not divisible by 25
    except Exception as e:
        print("Invalid price error:", type(e).__name__, "-", e)

    print("\n9. Test restock / set_qty")
    try:
        ph.set_qty("A2", 10)
        print("A2 after restock:", ph.get_product("A2"))
    except Exception as e:
        print("Set qty error:", type(e).__name__, "-", e)

    print("\n10. Test successful vend")
    try:
        product = ph.vend("A1")
        print("Vended:", product)
        print("A1 after vend:", ph.get_product("A1"))
    except JammedSlotError as e:
        print("Jam occurred (this is possible and acceptable):", e)
    except Exception as e:
        print("Vend error:", type(e).__name__, "-", e)

    print("\n11. Check persistence by reloading")
    ph2 = ProductHandler()
    print("Reloaded products:", ph2.get_all_products())


if __name__ == "__main__":
    test_money_handler()
    test_product_handler()