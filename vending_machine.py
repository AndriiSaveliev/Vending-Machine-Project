class VendingMachine:
    """
    Main controller that connects all modules.
    """
    admin_mode = False
    messages = []

    def to_money(self, cents):
        """Formats integer cents into string dollars E.g. 250 becomes $2.50"""
        dollars = cents / 100
        return f"${dollars:,.2f}"

    def __init__(self, money_handler, product_handler):
        self.money_handler = money_handler
        self.product_handler = product_handler
        self.max_price = 300  # hard coded for testing. Later will use max product price rounded up.
        self.admin_mode = False
    
    def insert_coin(self, cents):
        """Pass coin to MoneyHandler, along with max_price"""
        self.money_handler.insert_coin(cents, self.max_price)
        self.display(f"Balance:{self.to_money(self.money_handler.get_balance())}")

    def display(self, text):
        print(text)
        self.messages.append(text)
        if len(self.messages) > 50:  # limit to last 50 messages
            del self.messages[0]

    def get_messages(self):
        """For use with an external UI, returns list of all messages (up to limit)."""
        return self.messages
    
    def clear_messages(self):
        """For use with an external UI, clears list of messages."""
        self.messages = []
    
    def vend_product(self, slot):
        """Handle purchase flow"""
        
        # set aliases for less typing
        mh = self.money_handler
        ph = self.product_handler
        disp = self.display

        balance = mh.get_balance()
        price = ph.get_price(slot)
        if price == None:  # slot is empty or invalid
            disp("Invalid selection")            
        else:  # slot ok, check balance and attempt to vend
            if balance >= price:
                vend_success = False  # assume failure
                try:
                    ph.vend(slot)
                    vend_success = True  # if reaches this line, vend worked.
                except ph.JammedSlotError as e:  # handle jammed slot here
                    disp("Vend failed")
                if vend_success:
                    if balance > price:
                        disp("Dispensing change...")
                    change = mh.make_change(price)  # Zeros balance, returns dict of coins if any
                    disp(f"Change due:{change}")
                    disp("Thank you.")
                    self.update_sales_report(slot, "name", price)  # save to file
            else: # balance is not enough
                remaining = price - balance
                disp(f"Deposit {self.to_money(remaining)} more.")

    def coin_return(self):
        """Return coins"""
        balance = self.money_handler.get_balance()
        self.display("Cancelling transaction.")
        self.display(f"Returning {self.to_money(balance)}")
        self.money_handler.return_coins()

    def show_customer_ui(self):
        """Shows customer UI menu options and calls the other methods as needed."""
        pass
    
    def show_admin_ui(self):
        """Shows admin features menu options and calls other methods as needed."""
        pass
        
    def update_sales_report(self, slot, name, price_cents):
        """Saves vend to file."""
        pass
        
    def enter_admin_mode(self):
        self.admin_mode = True

    def exit_admin_mode(self):
        self.admin_mode = False

    def is_in_admin_mode(self):
        return self.admin_mode
    
    def get_price(self, slot):
        """Returns price at a slot."""
        return self.product_handler.get_price(slot)

    def set_price(self, slot, new_price_cents):
        """Set price at a slot."""
        try:
            self.product_handler.set_price(slot, new_price_cents)
        except InvalidSlotError:
            self.display("Slot invalid")
    
    def enable_slot(self, slot):
        try:
            self.product_handler.enable_slot(slot)
        except InvalidSlotError:
            self.display("Slot invalid")
    
    def disable_slot(self, slot):
        try:
            self.product_handler.diable_slot(slot)
        except InvalidSlotError:
            self.display("Slot invalid")
