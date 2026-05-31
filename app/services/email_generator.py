def generate_email(leads, template_message):
    if not template_message.strip():
        raise ValueError("Enter an email template before generating messages.")

    email_messages = []

    for _, lead in leads.iterrows():
        fields = {
            "Name": lead["first_name"],
            "Company Name": lead["company"],
            "Company_Name": lead["company"],
            "Title": lead["title"],
            "Email": lead["email"],
            "first_name": lead["first_name"],
            "company": lead["company"],
            "title": lead["title"],
            "email": lead["email"],
        }
        try:
            message = template_message.format(**fields)
        except KeyError as error:
            raise ValueError(
                f"Unknown placeholder: {{{error.args[0]}}}. "
                "Use {Name}, {Company Name}, or {Title}."
            ) from error

        email_messages.append({
            "Email": lead["email"],
            "Message": message
        })

    return email_messages
