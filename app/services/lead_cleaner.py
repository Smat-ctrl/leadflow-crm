import pandas as pd


def sheet_cleaner(uploaded_file):
    df = pd.read_csv(uploaded_file)
    df.columns = [
        col.strip().lower().replace(" ", "_")
        for col in df.columns
    ]

    df = df.rename(columns={
        "company_name": "company",
        "job_title": "title",
    })

    required_columns = ["first_name", "email", "company", "title"]
    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing_columns)
        )

    if "industry" not in df.columns:
        df["industry"] = ""

    cleaned = df[["first_name", "email", "company", "title", "industry"]].copy()
    cleaned = cleaned.dropna(subset=["email"])
    cleaned["email"] = cleaned["email"].astype(str).str.strip().str.lower()
    cleaned = cleaned[cleaned["email"] != ""]

    return cleaned
