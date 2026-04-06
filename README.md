# Vending Machine Project

## Team Roles
- Paul Renaud – Project Lead, Integration
- Andrii Saveliev – System Architect
- Gueswende Kafando – UI and Testing

---

## System Architecture

The system is divided into four main components:

### 1. VendingMachine (Controller)
Central controller that connects all parts of the system.

### 2. MoneyHandler
Handles:
- coin insertion
- balance tracking
- returning change
- coin supply (Exact Change Only mode)

### 3. ProductHandler
Handles:
- loading products from file
- price and quantity
- product availability
- vending items

### 4. AdminHandler
Handles:
- changing prices
- enabling/disabling slots
- restocking
- generating reports

---

## System Flow

1. Insert Coin  
User → VendingMachine → MoneyHandler  

2. Select Product  
User → VendingMachine  
→ ProductHandler (check product)  
→ MoneyHandler (check balance)  
→ Vend product + return change  

3. Coin Return  
User → VendingMachine → MoneyHandler  

4. Admin Actions  
User → VendingMachine → AdminHandler  

---

## Project Structure

main.py
vending_machine.py
money_handler.py
product_handler.py
admin_handler.py

---

## Data Storage

- products.csv → product data  
- coins.json → coin supply  
- logs.txt → logs and reports  

---

## Design Principles

- Modular design
- Separation of concerns
- Controller-based architecture
- File-based storage
