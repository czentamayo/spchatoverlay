import hashlib
import getpass


def hash_password(password):
    h = hashlib.sha256()
    h.update(password.encode())
    return h.hexdigest()


file_name = "theaccounts.txt"

username = input("Enter new username:")

with open(file_name, "r") as f:
    for line in f:
        account, _ = line.strip().split("::")
        if account == username:
            print("Exit: Username already exists")
            exit()

with open(file_name, "a") as f:
    hashed_password = hash_password(getpass.getpass("Enter password for this user:"))
    f.write(f"{username}::{hashed_password}\n")

print(f"Account {username} created!")
