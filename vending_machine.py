class VendingMachine:
    """
    Main controller that connects all modules.
    """

    def __init__(self, money_handler, product_handler, admin_handler):
        self.money_handler = money_handler
        self.product_handler = product_handler
        self.admin_handler = admin_handler

    def insert_coin(self, coin):
        """Pass coin to MoneyHandler"""
        pass

    def select_product(self, slot):
        """Handle purchase flow"""
        pass

    def coin_return(self):
        """Return coins"""
        pass
