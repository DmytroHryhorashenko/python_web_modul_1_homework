import pickle
from collections import UserDict
from datetime import datetime, timedelta
from pathlib import Path
from abc import ABC, abstractmethod

file_path = Path("database.bin")




class View(ABC):

    @abstractmethod
    def show_message(self, message):
        pass

    @abstractmethod
    def show_contacts(self, contacts):
        pass

    @abstractmethod
    def show_birthdays(self, birthdays):
        pass

    @abstractmethod
    def show_help(self):
        pass


class ConsoleView(View):

    def show_message(self, message):
        print(message)

    def show_contacts(self, contacts):
        if not contacts:
            print("Address book is empty.")
            return

        for contact in contacts:
            print(str(contact))

    def show_birthdays(self, birthdays):
        if not birthdays:
            print("There are no upcoming birthdays.")
            return

        for day in birthdays:
            print(f"{day}")

    def show_help(self):
        print("""
Available commands:

hello
add NAME PHONE
change NAME OLD_PHONE NEW_PHONE
phone NAME
all
add-birthday NAME DD.MM.YYYY
show-birthday NAME
birthdays
help
exit
""")




class Field:

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):

    def __init__(self, value):
        self.__value = None
        self.value = value

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):

        value = value.strip()

        if len(value) == 10 and value.isdigit():
            self.__value = value
        else:
            raise ValueError("Phone must contain exactly 10 digits.")


class Birthday(Field):

    def __init__(self, value):

        try:
            self.date = datetime.strptime(value, "%d.%m.%Y").date()
            super().__init__(value)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:

    def __init__(self, name):

        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        self.phones = [p for p in self.phones if str(p) != phone]

    def edit_phone(self, old, new):

        for phone in self.phones:

            if str(phone) == old:
                phone.value = new
                return

        raise ValueError("Phone not found")

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):

        phones = "; ".join(p.value for p in self.phones)

        birthday = self.birthday.value if self.birthday else "-"

        return f"{self.name.value}: {phones} | Birthday: {birthday}"


class AddressBook(UserDict):

    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    @staticmethod
    def find_next_weekday(d, weekday):

        days_ahead = weekday - d.weekday()

        if days_ahead <= 0:
            days_ahead += 7

        return d + timedelta(days_ahead)

    def get_upcoming_birthdays(self, days=7):

        today = datetime.today().date()
        upcoming = []

        for user in self.data.values():

            if user.birthday is None:
                continue

            birthday = user.birthday.date.replace(year=today.year)

            if birthday < today:
                birthday = birthday.replace(year=today.year + 1)

            if 0 <= (birthday - today).days <= days:

                if birthday.weekday() >= 5:
                    birthday = self.find_next_weekday(birthday, 0)

                upcoming.append(
                    f"{user.name.value} - {birthday.strftime('%d.%m.%Y')}"
                )

        return upcoming



def input_error(func):

    def inner(*args, **kwargs):

        try:
            return func(*args, **kwargs)

        except KeyError:
            return "Name not found."

        except ValueError as e:
            return str(e)

        except IndexError:
            return "Enter correct data."

    return inner




@input_error
def add_contact(args, book):

    name, phone, *_ = args

    record = book.find(name)

    if record is None:

        record = Record(name)
        book.add_record(record)
        message = "Contact added."

    else:
        message = "Contact updated."

    record.add_phone(phone)

    return message


@input_error
def change_contact(args, book):

    name, old, new, *_ = args

    record = book.find(name)

    if record:

        record.edit_phone(old, new)
        return "Phone updated."

    raise KeyError


@input_error
def show_phone(args, book):

    name = args[0]

    record = book.find(name)

    if record:

        return "; ".join([str(p) for p in record.phones])

    raise KeyError


def show_all(book):
    return list(book.data.values())


@input_error
def add_birthday(args, book):

    name, birthday = args

    record = book.find(name)

    if record:

        record.add_birthday(birthday)
        return "Birthday added."

    raise KeyError


@input_error
def show_birthday(args, book):

    name = args[0]

    record = book.find(name)

    if record and record.birthday:

        return record.birthday.value

    raise KeyError




def parse_input(user_input):

    parts = user_input.split()

    if not parts:
        return "", []

    cmd = parts[0].lower()
    args = parts[1:]

    return cmd, args


def load_data():

    if file_path.exists():

        with open(file_path, "rb") as file:
            return pickle.load(file)

    return AddressBook()


def save_data(book):

    with open(file_path, "wb") as file:
        pickle.dump(book, file)




def main():

    book = load_data()
    view = ConsoleView()

    view.show_message("Welcome to the assistant bot!")

    while True:

        user_input = input("Enter command: ")

        command, args = parse_input(user_input)

        if command in ["close", "exit"]:

            save_data(book)
            view.show_message("Good bye!")
            break

        elif command == "hello":

            view.show_message("How can I help you?")

        elif command == "help":

            view.show_help()

        elif command == "add":

            view.show_message(add_contact(args, book))

        elif command == "change":

            view.show_message(change_contact(args, book))

        elif command == "phone":

            view.show_message(show_phone(args, book))

        elif command == "all":

            view.show_contacts(show_all(book))

        elif command == "add-birthday":

            view.show_message(add_birthday(args, book))

        elif command == "show-birthday":

            view.show_message(show_birthday(args, book))

        elif command == "birthdays":

            view.show_birthdays(book.get_upcoming_birthdays())

        else:

            view.show_message("Invalid command.")


if __name__ == "__main__":
    main()