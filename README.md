# Vending Machine Project

> A modular Python application simulating a real vending machine system.

**Team Purple | SDEV265**

---

## Team Members and Roles

| Name | Role |
|------|------|
| Paul Renaud | Project Lead and System Integration |
| Andrii Saveliev | System Architecture |
| Gueswende Kafando | UI Design and Testing |

---

## Project Overview

The Vending Machine Project is a modular Python application that simulates the full functionality of a real vending machine. Users can insert coins, purchase products, receive change, and interact with an administrator mode for inventory and pricing management.

The project was designed using modular software engineering principles and a controller-based architecture to cleanly separate responsibilities between system components.

---

## System Architecture

### 1. VendingMachine (Controller)
The central controller of the application. Connects all modules and manages system flow.
- User interaction
- Product selection
- Transaction coordination
- Admin menu access

### 2. MoneyHandler
Handles all money-related operations.
- Coin insertion and balance tracking
- Coin return
- Change calculation
- Exact Change Only mode
- Hopper tracking

### 3. ProductHandler
Manages the product inventory.
- Loading products from file
- Product lookup and validation
- Quantity tracking
- Price management
- Vending items
- Enabling/disabling slots

### 4. Admin Features
- Restocking inventory
- Changing prices
- Enabling/disabling slots
- Viewing reports and sales logs
- Viewing hopper counts

---

## System Flow

```
Insert Coin:      User → VendingMachine → MoneyHandler
Select Product:   User → VendingMachine → ProductHandler → MoneyHandler → vend + change
Coin Return:      User → VendingMachine → MoneyHandler
Admin Functions:  User → VendingMachine → Admin Features
```

---

## Project Structure

```
main.py
vending_machine.py
money_handler.py
product_handler.py
test_handlers.py
products.csv
hoppers.json
log.csv
.gitignore
README.md
```

---

## Data Storage

| File | Purpose |
|------|---------|
| `products.csv` | Stores products, prices, quantities, and enabled status |
| `hoppers.json` | Stores coin hopper supply information |
| `log.csv` | Stores transaction logs and reports |

---

## Design Principles

- Modular design with separation of concerns
- Reusable classes and methods
- Controller-based architecture
- File persistence and storage

---

## Installation and Setup

**Requirements:** Python 3.x (no external packages needed)

```bash
# Clone the repository
git clone https://github.com/AndriiSaveliev/Vending-Machine-Project.git

# Navigate to the project folder
cd Vending-Machine-Project

# Run the application
python3 main.py
```

---

## Testing

```bash
python3 test_handlers.py
```

Testing covers:
- Unit-style handler testing
- Vending flow validation
- Invalid slot and sold-out handling
- Exact Change mode
- File persistence

---

## Features Implemented

- Product purchasing
- Coin insertion and balance tracking
- Change return and coin return
- Exact Change Only mode
- Admin menu
- Product inventory management
- Sales logging
- File persistence
- CLI user interface

---

## Future Improvements

- GUI interface
- Database integration
- Card payment support
- Multi-user admin system
- Advanced analytics and reporting
