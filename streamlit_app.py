import streamlit as st

from app.db.database import check_db
from app.db.schema import create_tables
from app.db.database import delete_db
from app.services.email_generator import generate_email
from app.services.graph_service import (
    create_email_drafts,
    get_access_token_from_device_login,
    start_device_login,
)
from app.services.lead_cleaner import sheet_cleaner


def main():
    st.title("LEADCRM FLOW")
    st.write(
        "LeadCRM Flow helps you turn raw outreach lists into organized, actionable leads. "
        "Upload your Apollo CSV to clean duplicate contacts, organize lead details, "
        "track outreach status, and prepare personalized email drafts without losing track "
        "of who you've already contacted."
    )

    uploaded_file = st.file_uploader(
        "Before uploading, make sure your CSV includes key fields like name, company, email, and job title.",
        type=["csv"],
    )
    if st.button("Click to Delete Database"):
        delete_db()
    if uploaded_file:
        try:
            data = sheet_cleaner(uploaded_file)
        except ValueError as error:
            st.error(str(error))
            return
        st.success("File uploaded and cleaned successfully!")
    else:
        st.warning("Please upload a CSV file to proceed.")
        return

    st.subheader("Cleaned Lead Data:")
    st.dataframe(data)

    create_tables()
    try:
        db_results = check_db(data)
    except ValueError as error:
        st.error(str(error))
        return
    unique_data = data.drop_duplicates(subset=["email"])

    if db_results["inserted"]:
        st.success(f"Added {len(db_results['inserted'])} new lead(s) to the database.")
    if db_results["already_in_database"]:
        st.warning(
            "Skipped "
            f"{len(db_results['already_in_database'])} lead(s) already in the database: "
            + ", ".join(db_results["already_in_database"])
        )
    if db_results["duplicate_in_upload"]:
        st.warning(
            "Skipped "
            f"{len(db_results['duplicate_in_upload'])} duplicate email(s) in this upload: "
            + ", ".join(db_results["duplicate_in_upload"])
        )
    if not any(db_results.values()):
        st.info("No new leads were added.")

    message = st.text_area(
        "Enter your email template (use {Name}, {Company Name}, {Title} as placeholders):"
    )
    if st.button("Generate Messages"):
        try:
            email_messages = generate_email(unique_data, message)
        except ValueError as error:
            st.error(str(error))
            return

        st.session_state["email_messages"] = email_messages

        st.success(f"Generated {len(email_messages)} email message(s).")
        st.toast("Email messages generated.")

    if "email_messages" in st.session_state:
        st.subheader("Generated Email Messages:")

        subject = st.text_input("Email subject:", value="Quick question")
        microsoft_account = st.text_input(
            "Microsoft account to sign in with:",
            placeholder="you@example.com",
            help="Drafts are created in the mailbox for the Microsoft account you sign into.",
        )

        for index, email in enumerate(st.session_state["email_messages"]):
            st.write(f"To: {email['Email']}")
            st.write(f"Message: {email['Message']}")
            st.write("---")

        if st.button("Start Microsoft Sign In"):
            try:
                st.session_state["device_flow"] = start_device_login()
            except ValueError as error:
                st.error(str(error))
                return

        if "device_flow" in st.session_state:
            st.info(
                "Sign in with the Microsoft account above. "
                "After signing in, come back here and create the drafts."
            )
            st.code(st.session_state["device_flow"].get("message", ""))
            if microsoft_account:
                st.caption(
                    f"Make sure you sign in as {microsoft_account}. "
                    "The drafts will be created in that signed-in mailbox."
                )

        if st.button("Create Drafts for All Emails"):
            try:
                access_token = get_access_token_from_device_login(
                    st.session_state.get("device_flow")
                )
                result = create_email_drafts(
                    email_messages=st.session_state["email_messages"],
                    subject=subject,
                    access_token=access_token,
                )
            except ValueError as error:
                st.error(str(error))
                return

            if result["drafts"]:
                st.success(f"Created {len(result['drafts'])} draft(s).")
                st.toast("Outlook drafts created.")
                with st.expander("Created draft IDs"):
                    for draft in result["drafts"]:
                        st.write(f"{draft['email']}: {draft['id']}")

            if result["failures"]:
                st.error(f"{len(result['failures'])} draft(s) failed.")
                with st.expander("Failed drafts"):
                    for failure in result["failures"]:
                        st.write(f"{failure['email']}: {failure['error']}")


if __name__ == "__main__":
    main()
