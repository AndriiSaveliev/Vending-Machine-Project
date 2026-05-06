import csv
import os
import random
import datetime


class JammedSlotError(Exception):
    """Raised when a product slot jams during vending."""
    pass


class InvalidSlotError(Exception):
    """Raised when a slot does not exist."""
    pass


class ProductHandler:
    """
    Tracks product slots, prices, quantities, and slot status.
    All prices are stored in cents.
    """
    max_value_cents = 200

    def __init__(self, product_file="products.csv", sales_log_file="log.csv"):
        """
        Creates an instance of ProductHandler.
        Loads product data from file.
        """
        self.product_file = product_file
        self.products = {}
        self.load_products()
        self.sales_log_file = sales_log_file

    def vend(self, slot):
        """
        If slot is valid and enabled, attempt to vend product.
        Simulates jam about 5% of the time.
        If vend succeeds, reduce quantity by 1 and save file.
        Raises:
            InvalidSlotError
            ValueError for disabled/sold out
            JammedSlotError
        Returns product dict if successful.
        """
        slot = slot.strip().upper()

        if slot not in self.products:
            raise InvalidSlotError(f"Invalid slot: {slot}")

        product = self.products[slot]

        if not product["enabled"]:
            raise ValueError("Slot is disabled")

        if product["quantity"] <= 0:
            raise ValueError("Product sold out")

        if random.random() < 0.05:
            raise JammedSlotError(f"Slot {slot} jammed")

        product["quantity"] -= 1
        self.save_products()
        self.save_sales(slot)
        return product

    def get_price(self, slot):
        """
        Returns price in cents.
        Returns None if slot invalid.
        """
        slot = slot.strip().upper()
        if slot not in self.products:
            return None
        return self.products[slot]["price_cents"]
    
    def get_name(self, slot):
        """
        Returns name of product at slot.
        Returns None if slot invalid.
        """
        slot = slot.strip().upper()
        if slot not in self.products:
            return None
        return self.products[slot]["name"]        

    def get_product(self, slot):
        """
        Helpful extra method for UI / VendingMachine.
        Returns product dict or None.
        """
        return self.products.get(slot.strip().upper())

    def get_all_products(self):
        """
        Returns all product data.
        Helpful extra method for UI display.
        """
        return self.products

    def set_price(self, slot, new_price_cents):
        """
        Sets price in cents at slot.
        Raises InvalidSlotError if slot invalid.
        Raises ValueError if price is not in quarter increments.
        """
        slot = slot.strip().upper()

        if slot not in self.products:
            raise InvalidSlotError(f"Invalid slot: {slot}")

        if new_price_cents <= 0 or new_price_cents % 25 != 0:
            raise ValueError("Price must be in quarter increments")

        self.products[slot]["price_cents"] = new_price_cents
        self.save_products()

    def enable_slot(self, slot):
        """
        Enables slot.
        """
        slot = slot.strip().upper()

        if slot not in self.products:
            raise InvalidSlotError(f"Invalid slot: {slot}")

        self.products[slot]["enabled"] = True
        self.save_products()

    def disable_slot(self, slot):
        """
        Disables slot without clearing slot info.
        """
        slot = slot.strip().upper()

        if slot not in self.products:
            raise InvalidSlotError(f"Invalid slot: {slot}")

        self.products[slot]["enabled"] = False
        self.save_products()

    def set_qty(self, slot, qty):
        """
        Sets quantity of product at slot.
        Raises InvalidSlotError if slot invalid.
        Raises ValueError if qty is negative.
        """
        slot = slot.strip().upper()

        if slot not in self.products:
            raise InvalidSlotError(f"Invalid slot: {slot}")

        if qty < 0:
            raise ValueError("Quantity cannot be negative")

        self.products[slot]["quantity"] = qty
        self.save_products()

    def set_name(self, slot, name):
        """
        Sets name of product at slot.
        Raises InvalidSlotError if slot invalid.
        If name is empty it does not change and returns.
        Name sliced at 20 chararacters.
        """
        slot = slot.strip().upper()

        if slot not in self.products:
            raise InvalidSlotError(f"Invalid slot: {slot}")

        if name == "":
            return

        self.products[slot]["name"] = name[:20]
        self.save_products()


    def load_products(self):
        """
        Loads product data from CSV file.
        Expected columns:
        slot,name,price,quantity,enabled(optional)
        Example:
        A1,Chips,1.00,5,True
        """
        self.products = {}

        if not os.path.exists(self.product_file):
            # default fallback to avoid crash
            self.products = {
                "A1": {
                    "slot": "A1",
                    "name": "Chips",
                    "price_cents": 100,
                    "quantity": 5,
                    "enabled": True,
                },
                "A2": {
                    "slot": "A2",
                    "name": "Candy",
                    "price_cents": 75,
                    "quantity": 0,
                    "enabled": True,
                },
                "B1": {
                    "slot": "B1",
                    "name": "Water",
                    "price_cents": 100,
                    "quantity": 8,
                    "enabled": True,
                },
            }
            self.max_value_cents = 100
            self.save_products()
            return

        with open(self.product_file, "r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) < 4:
                    continue

                slot = row[0].strip().upper()
                name = row[1].strip()
                price_cents = int(round(float(row[2]) * 100))
                if price_cents > self.max_value_cents:
                    self.max_value_cents = ((price_cents + 99) // 100) * 100
                quantity = int(row[3])

                enabled = True
                if len(row) >= 5:
                    enabled = row[4].strip().lower() == "true"

                self.products[slot] = {
                    "slot": slot,
                    "name": name,
                    "price_cents": price_cents,
                    "quantity": quantity,
                    "enabled": enabled,
                }

    def save_products(self):
        """
        Saves product data to CSV file.
        """
        with open(self.product_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            for product in self.products.values():
                writer.writerow([
                    product["slot"],
                    product["name"],
                    f"{product['price_cents'] / 100:.2f}",
                    product["quantity"],
                    product["enabled"],
                ])

    def save_sales(self, slot):
        """
        Saves sales data.
        """
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        item = self.products[slot]
        sales_info = [
            now,
            item["slot"],
            item["name"],
            f"{item['price_cents'] / 100:.2f}",
        ]

        with open(self.sales_log_file, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(sales_info)

    def generate_sales_report(self, days=None):
        """
        Returns recent sales data as a dictionary, along with best sellers
        and worst sellers over a recent time frame.
        Days can be left blank for all history, set to 7 for most recent week,
        or 30 for month, etc.
        """
        report = {}
        start_date = None

        if days is not None:
            start_date = datetime.datetime.now() - datetime.timedelta(days=days)

        with open(self.sales_log_file, newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                timestamp, slot, name, price = row
                dt = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

                # skip rows older than start_date
                if start_date and dt < start_date:
                    continue

                price = float(price)

                #create new item if not in report
                if name not in report:
                    report[name] = {
                        "units_sold": 0,
                        "revenue": 0.0,
                        "first_sale": dt,
                        "last_sale": dt
                    }

                # add to existing item
                report[name]["units_sold"] += 1
                report[name]["revenue"] += price

                #track date range for each item
                if dt < report[name]["first_sale"]:
                    report[name]["first_sale"] = dt
                if dt > report[name]["last_sale"]:
                    report[name]["last_sale"] = dt

        # After building the `report` dictionary:
        best_sellers = sorted(
            report.items(),
            key=lambda item: item[1]["units_sold"],
            reverse=True
        )[:3]
        worst_sellers = sorted(
            report.items(),
            key=lambda item: item[1]["units_sold"],
            reverse=False
        )[:3]

        return report, best_sellers, worst_sellers
