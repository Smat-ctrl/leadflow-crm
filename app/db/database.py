import sqlite3

import pandas as pd

DB_PATH = "leads.db"


def check_db(dataset):
    required_columns = {"first_name", "email", "company", "title", "industry"}
    missing_columns = required_columns - set(dataset.columns)
    if missing_columns:
        raise ValueError(
            "Missing required columns: " + ", ".join(sorted(missing_columns))
        )

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    seen_emails = set()
    results = {
        "inserted": [],
        "already_in_database": [],
        "duplicate_in_upload": [],
    }

    for _, lead in dataset.iterrows():
        email = lead["email"]
        if pd.isna(email) or str(email).strip() == "":
            continue

        email = str(email).strip()
        if email in seen_emails:
            results["duplicate_in_upload"].append(email)
            continue
        seen_emails.add(email)

        cursor.execute("SELECT * FROM leads WHERE email = ?", (email,))
        existing_lead = cursor.fetchone()

        if existing_lead:
            print(f"Lead with email {email} already exists. Skipping insertion.")
            results["already_in_database"].append(email)
        else:
            cursor.execute("""
                INSERT INTO leads (first_name, email, company, title, industry, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                lead["first_name"],
                email,
                lead["company"],
                lead["title"],
                lead["industry"],
                "Not Contacted"
            ))

            print(f"Inserted lead with email {email}.")
            results["inserted"].append(email)

    conn.commit()
    conn.close()
    return results

def delete_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS leads")
    conn.commit()
    conn.close()
    
