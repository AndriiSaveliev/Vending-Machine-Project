import json
import os


class MoneyHandler:
    """
    Tracks money in/out, coin hoppers, and exact change state.
    All money values are stored in cents.
    """

    def __init__(self, hopper_file="hoppers.json"):
        """
        Creates an instance of MoneyHandler.
        Loads coin hopper quantities from file.
        """
        self.hopper_file = hopper_file
        self.balance_cents = 0
        self.exact_change = False
        self.hoppers = {
            100: 10,   # dollar coins
            25: 20     # quarters
        }
        self.load_hoppers()

    def insert_coin(self, value_cents, max_value):
        """
        If not above max_value, add coin to total.
        Update coin hoppers.
        Returns True if accepted, False otherwise.
        """
        if value_cents not in (25, 100):
            return False

        if self.balance_cents + value_cents > max_value:
            return False

        self.balance_cents += value_cents
        self.hoppers[value_cents] = self.hoppers.get(value_cents, 0) + 1
        self.save_hoppers()

        if self._can_make_any_change():
            self.exact_change = False

        return True

    def get_balance(self):
        """
        Returns total inserted balance in cents.
        """
        return self.balance_cents

    def make_change(self, price_cents):
        """
        Calculates change due from balance minus price.
        Dispenses the fewest number of coins possible.
        Updates coin hoppers.
        Zeros out current balance.
        Returns a dict of coins returned, for example:
        {100: 1, 25: 2}
        """
        if price_cents > self.balance_cents:
            return {}

        change_due = self.balance_cents - price_cents
        coins_returned = {100: 0, 25: 0}

        remaining = change_due

        for coin_value in (100, 25):
            while remaining >= coin_value and self.hoppers.get(coin_value, 0) > 0:
                remaining -= coin_value
                self.hoppers[coin_value] -= 1
                coins_returned[coin_value] += 1

        # if exact change could not be made, restore hopper counts
        if remaining != 0:
            for coin_value, count in coins_returned.items():
                self.hoppers[coin_value] += count
            self.exact_change = True
            return {}

        self.balance_cents = 0
        self.save_hoppers()

        if not self._can_make_any_change():
            self.exact_change = True

        return coins_returned

    def return_coins(self):
        """
        Dispenses all inserted money back to the customer.
        Could just call make_change(0).
        """
        return self.make_change(0)

    def get_hopper_counts(self):
        """
        Returns hopper counts as a dict.
        """
        return dict(self.hoppers)

    def load_hoppers(self):
        """
        Loads coin quantities from file.
        """
        if not os.path.exists(self.hopper_file):
            self.save_hoppers()
            return

        try:
            with open(self.hopper_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                self.hoppers = {
                    int(k): int(v) for k, v in data.items()
                }
        except (json.JSONDecodeError, OSError, ValueError):
            self.hoppers = {100: 10, 25: 20}
            self.save_hoppers()

    def save_hoppers(self):
        """
        Saves coin quantities to file.
        """
        with open(self.hopper_file, "w", encoding="utf-8") as file:
            json.dump(self.hoppers, file, indent=4)

    def needs_exact_change(self):
        """
        Returns True if machine should operate in exact change mode.
        """
        return self.exact_change

    def set_exact_change(self, enabled):
        """
        Allows admin/manual toggle if VendingMachine wants it.
        """
        self.exact_change = bool(enabled)

    def _can_make_any_change(self):
        """
        Simple helper: determines whether machine has any change available.
        """
        return self.hoppers.get(25, 0) > 0 or self.hoppers.get(100, 0) > 0
