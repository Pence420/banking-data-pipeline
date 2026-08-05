import os
from faker import Faker
from supabase import create_client
from dotenv import load_dotenv
import random

load_dotenv()
fake = Faker("id_ID")  # locale Indonesia, biar nama/alamat kerasa realistis

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_API_KEY"))

def generate_customers(n=100):
    customers = []
    for _ in range(n):
        customers.append({
            "full_name": fake.name(),
            "email": fake.unique.email(),
            "address": fake.address(),
            "loyalty_tier": random.choices(
                ["Platinum", "Gold", "Silver"], weights=[10, 30, 60]
            )[0],  # distribusi realistis: mayoritas Silver
            "status": "active"
        })
    result = supabase.table("customers").insert(customers).execute()
    print(f"Inserted {len(result.data)} customers")
    return result.data

def generate_accounts(customers, accounts_per_customer=(1, 2)):
    accounts = []
    for customer in customers:
        n_accounts = random.randint(*accounts_per_customer)
        for _ in range(n_accounts):
            accounts.append({
                "customer_id": customer["customer_id"],
                "account_number": fake.unique.numerify("################"),  # 16 digit
                "account_type": random.choice(["savings", "checking"]),
                "balance": round(random.uniform(500_000, 50_000_000), 2),
                "status": "active"
            })
    result = supabase.table("accounts").insert(accounts).execute()
    print(f"Inserted {len(result.data)} accounts")
    return result.data


def generate_transactions(accounts, transactions_per_account=(5, 20)):
    transactions = []
    for account in accounts:
        n_tx = random.randint(*transactions_per_account)
        for _ in range(n_tx):
            transactions.append({
                "account_id": account["account_id"],
                "transaction_type": random.choice(["deposit", "withdrawal", "transfer"]),
                "amount": round(random.uniform(10_000, 5_000_000), 2),
                "status": random.choices(
                    ["success", "failed"], weights=[95, 5]
                )[0]  # sebagian kecil gagal, biar success rate KPI nggak 100%
            })
    result = supabase.table("transactions").insert(transactions).execute()
    print(f"Inserted {len(result.data)} transactions")


if __name__ == "__main__":
    customers = generate_customers(n=500)
    accounts = generate_accounts(customers)
    generate_transactions(accounts)