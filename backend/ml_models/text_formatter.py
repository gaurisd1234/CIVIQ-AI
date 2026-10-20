def format_official_text(complaint_text):
    complaint_text = complaint_text.strip()

    if not complaint_text.endswith("."):
        complaint_text += "."

    official_summary = (
        "A civic issue has been officially reported. "
        "The complaint states that "
        + complaint_text[0].lower()
        + complaint_text[1:]
        + " Immediate action by the concerned municipal department is requested."
    )

    return official_summary