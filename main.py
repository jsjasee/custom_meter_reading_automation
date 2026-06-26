import sys
from email import policy # policy is just a bunch of rules telling the computer how to parse the email
from email.message import EmailMessage
from email.parser import BytesParser
from pathlib import Path
from typing import cast # we need this to tell py charm that we are using the LATEST parser to process the email,
# otherwise it will flag a error saying .get_content() is not a method of the message object. LIKE DECLARING THE TYPE!


def extract_rfc822_text(path: str | Path) -> str:
    """Return the readable body text from a local RFC822 email file.

    Args:
        path: Filesystem path to a raw `.eml`-style message.

    Returns:
        The decoded plain-text body, or HTML text if no plain-text part exists.

    Raises:
        FileNotFoundError: If the message file does not exist.
        ValueError: If the message has no readable text body.
    """
    message_path = Path(path)
    with message_path.open("rb") as handle:
        message = cast(EmailMessage, BytesParser(policy=policy.default).parse(handle))
        # this parses the email into an email object, with parts like 'content-type', 'headers' etc.
        # We will need this later to walk down the tree (same concept as walking down the DOM tree,
        # some parts has its own children parts - this walking down the tree is done recursively by our code)

        # Rb means Open the file as "rb" = READ BINARY (not read-only!). Bytes, not text, because decoding too early (text mode) corrupts emoji /
        # Chinese into weird symbols. Bytes lets the parser decode later using the email's OWN charset.

    if not message.is_multipart():
        body = message.get_content()
        if body.strip():
            return body.strip()
        raise ValueError(f"No readable text body found in {message_path}")

    html_fallback = ""
    # same concept as walking down the dom tree.
    for part in message.walk():
        if part.get_content_disposition() == "attachment":
            continue
        if part.get_content_type() == "text/plain":
            body = part.get_content()
            if body.strip():
                return body.strip()
        if not html_fallback and part.get_content_type() == "text/html":
            # this means no text found, we found a html version, use that.
            body = part.get_content()
            if body.strip():
                html_fallback = body.strip()

    if html_fallback:
        return html_fallback
    raise ValueError(f"No readable text body found in {message_path}")


def main() -> int:
    email_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("emails/TASKalfa 5054ci_1") # this is just decoding the command
    # Command you type:   python main.py apple banana
    # sys.argv becomes:   ["main.py", "apple", "banana"]
    #                        [0]         [1]      [2]
    # index 0 is always the script. note that same applies if we type 'uv run main.py', index 0 is still main.py
    print(extract_rfc822_text(email_path))
    return 0


if __name__ == "__main__":
    main()
