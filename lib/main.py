import datetime
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Create the database engine
engine = create_engine('sqlite:///transaction.db', echo=True)

# Create a base class for declarative models
Base = declarative_base()

# Define the models for the tables
class Transaction(Base):
    __tablename__ = 'transaction'
    id = Column(Integer, primary_key=True)
    user = Column(String)
    description = Column(String)
    amount = Column(Integer)
    due_date = Column(Integer)
    extended_dates = relationship('ExtendedDate', back_populates='transaction')
    account_id = Column(Integer, ForeignKey('account.id'))
    account = relationship('Account', back_populates='transactions')
    overdue = relationship('Overdue', uselist=False, back_populates='transaction')
    priority = Column(Integer)
    completed = Column(Boolean, default=False)

    def extend_due_date(self, new_due_date):
        self.due_date = new_due_date
        self.extended_dates.append(ExtendedDate(transaction=self, extended_date=new_due_date))

class ExtendedDate(Base):
    __tablename__ = 'extended_date'
    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transaction.id'))
    transaction = relationship('Transaction', back_populates='extended_dates')
    extended_date = Column(Integer)

class Account(Base):
    __tablename__ = 'account'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    transactions = relationship('Transaction', back_populates='account')

class Overdue(Base):
    __tablename__ = 'overdue'
    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transaction.id'))
    past_date = Column(Integer)
    transaction = relationship('Transaction', back_populates='overdue')

# Create the tables in the database
Base.metadata.create_all(engine)

# Create a session to interact with the database
Session = sessionmaker(bind=engine)
session = Session()

# Define CLI commands
def populate_overdue_table():
    # Populates the overdue table with transactions that are overdue
    today = datetime.datetime.now().date()
    transactions = session.query(Transaction).filter(Transaction.due_date < today, Transaction.completed == False).all()
    for transaction in transactions:
        if not transaction.overdue:
            transaction.overdue = True
            session.add(Overdue(transaction=transaction))
    session.commit()

def add_transaction():
    user = input('Enter user: ')
    description = input('Enter transaction description: ')
    amount = input('Enter transaction amount: ')
    due_date_str = input('Enter due date (YYYY-MM-DD): ')
    due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d').date()
    priority = input('Enter transaction priority: ')

    account_name = input('Enter account name: ')
    account = session.query(Account).filter_by(name=account_name).first()
    if not account:
        account = Account(name=account_name)
        session.add(account)

    transaction = Transaction(user=user,description=description, amount=amount, due_date=due_date, priority=priority, account=account)
    session.add(transaction)
    session.commit()

def update_transaction():
    transaction_id = input('Enter transaction ID: ')
    transaction = session.query(Transaction).get(transaction_id)
    if not transaction:
        print('Transaction not found!')
        return

    new_user = input('Enter new user (leave empty to keep the current user): ')
    if new_user:
        transaction.user = new_user

    new_description = input('Enter new description (leave empty to keep the current description): ')
    if new_description:
        transaction.description = new_description

    new_amount = input('Enter new amount (leave empty to keep the current amount): ')
    if new_amount:
        transaction.amount = new_amount

    new_due_date_str = input('Enter new due date (YYYY-MM-DD, leave empty to keep the current due date): ')
    if new_due_date_str:
        new_due_date = datetime.datetime.strptime(new_due_date_str, '%Y-%m-%d').date()
        transaction.due_date = new_due_date

    new_priority = input('Enter new priority (leave empty to keep the current priority): ')
    if new_priority:
        transaction.priority = new_priority

    session.commit()

def delete_transaction():
    transaction_id = input('Enter transaction ID: ')
    transaction = session.query(Transaction).get(transaction_id)
    if not transaction:
        print('Transaction not found!')
        return

    session.delete(transaction)
    session.commit()

def mark_as_complete():
    transaction_id = input('Enter transaction ID: ')
    transaction = session.query(Transaction).get(transaction_id)
    if not transaction:
        print('Transaction not found!')
        return

    transaction.completed = True
    session.commit()

def generate_reports():
    pending_transactions = session.query(Transaction).filter_by(completed=False).all()
    overdue_transactions = session.query(Transaction).join(Overdue).filter(Transaction.completed == False).all()
    completed_transactions = session.query(Transaction).filter_by(completed=True).all()

    print('Pending Transactions:')
    for transaction in pending_transactions:
        print(f'Transaction ID: {transaction.id}')
        print(f'User: {transaction.user}')
        print(f'Description: {transaction.description}')
        print(f'Transaction amount: {transaction.amount}')
        print(f'Due Date: {transaction.due_date}')
        print(f'Priority: {transaction.priority}')
        print('---')

    print('\nOverdue Transactions:')
    for transaction in overdue_transactions:
        print(f'Transaction ID: {transaction.id}')
        print(f'User: {transaction.user}')
        print(f'Description: {transaction.description}')
        print(f'Transaction amount: {transaction.amount}')
        print(f'Due Date: {transaction.due_date}')
        print(f'Priority: {transaction.priority}')
        print('---')

    print('\nCompleted Transactions:')
    for transaction in completed_transactions:
        print(f'Transaction ID: {transaction.id}')
        print(f'User: {transaction.user}')
        print(f'Description: {transaction.description}')
        print(f'Transaction amount: {transaction.amount}')
        print(f'Due Date: {transaction.due_date}')
        print(f'Priority: {transaction.priority}')
        print('---')

# Run the CLI
while True:
    print('----------Transaction Management System----------')
    print('1. Add Transaction')
    print('2. Update Transaction')
    print('3. Delete Transaction')
    print('4. Mark as Complete')
    print('5. Generate Reports')
    print('0. Exit')
    choice = input('Enter your choice: ')

    if choice == '1':
        add_transaction()
    elif choice == '2':
        update_transaction()
    elif choice == '3':
        delete_transaction()
    elif choice == '4':
        mark_as_complete()
    elif choice == '5':
        generate_reports()
    elif choice == '0':
        break
    else:
        print('Invalid choice!')

session.close()