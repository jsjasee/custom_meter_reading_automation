import sys
import re
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


def _sum_counter_block(section: str, start_label: str, end_label: str) -> int:
    match = re.search(
        rf"{re.escape(start_label)}:\s*(.*?)(?=\n\s*{re.escape(end_label)}:)",
        section,
        re.DOTALL,
    ) # without .DOTALL, the dot(.) in regex will just stop at the first '\n', now the (.) dont care, it will continue to match beyond '\n' as long as it fits the pattern.
    if not match:
        raise ValueError(f"Could not find {start_label} block")
    return sum(int(value) for value in re.findall(r":\s+(\d+)", match.group(1)))
    # INTERESTING! swap out [] with () to get a generator. sum() here does the looping, it will keep calling the generator to get each of the values until there's no more
    # example:
    # text = "A4: 100\nA3: 250\nA5: 30"
    # re.findall(r":\s+(\d+)", text)          # ['100', '250', '30']   <- findall returns a LIST (of strings)
    # (int(v) for v in re.findall(...))       # a generator -> yields 100, 250, 30 one at a time
    # sum(int(v) for v in re.findall(...))    # 380                     <- sum pulls them and adds


def parse_meter_counts(text: str) -> dict[str, str | int]:
    """Parse the printer id and paper-size totals from extracted meter text.

    Args:
        text: Decoded email body containing meter counters.

    Returns:
        A mapping with the printer id plus black-and-white and full-colour totals.

    Raises:
        ValueError: If the printer id or paper-size sections are missing.
    """
    printer_id_match = re.search(r"^Equipment ID:[ \t]*(\S+)\r?$", text, re.MULTILINE)
    # with MULTILINE:
    # Default: ^ = only match at start of the whole string only.
    # With MULTILINE: ^ = start of every line (and $ = end of every line). This is important because our message spans multiple lines.
    # This regex finds the line that starts with 'Equipment ID:'
    if not printer_id_match:
        printer_id_match = re.search(r"^Serial Number:[ \t]*(\S+)\r?$", text, re.MULTILINE)
    if not printer_id_match:
        raise ValueError("Could not find Equipment ID or Serial Number")

    paper_size_match = re.search(
        r"Counters by Paper Size:\s*(.*?)\nUsage by Color Mode",
        text,
        re.DOTALL,
    )
    if not paper_size_match:
        raise ValueError("Could not isolate Counters by Paper Size section")

    paper_size_section = paper_size_match.group(1) # group(0) = the entire match captured, group(1) means whatever the first ( ) captured
    return {
        "printer_id": printer_id_match.group(1),
        "black_and_white": _sum_counter_block(paper_size_section, "Black & White", "Single Color"),
        "full_colour": _sum_counter_block(paper_size_section, "Full Color", "Total"),
    }


def aggregate_meter_counts(email_dir: str | Path) -> dict[str, dict[str, int]]:
    """Aggregate parsed meter counts for every email file in a directory.

    Args:
        email_dir: Directory containing local RFC822 meter emails.

    Returns:
        A mapping keyed by printer id with black-and-white and full-colour totals.

    Raises:
        FileNotFoundError: If the directory does not exist.
        NotADirectoryError: If the path is not a directory.
        ValueError: If two files produce the same printer id.
    """
    directory = Path(email_dir)
    if not directory.exists():
        raise FileNotFoundError(directory)
    if not directory.is_dir():
        raise NotADirectoryError(directory)

    aggregated: dict[str, dict[str, int]] = {}
    for email_path in sorted(path for path in directory.iterdir() if path.is_file()):
        parsed = parse_meter_counts(extract_rfc822_text(email_path))
        printer_id = str(parsed["printer_id"])
        if printer_id in aggregated:
            raise ValueError(f"Duplicate printer id found: {printer_id} ({email_path.name})")
        aggregated[printer_id] = {
            "black_and_white": int(parsed["black_and_white"]),
            "full_colour": int(parsed["full_colour"]),
        }

    return aggregated


def main() -> int:
    email_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("emails") # this is just decoding the command
    # Command you type:   python main.py apple banana
    # sys.argv becomes:   ["main.py", "apple", "banana"]
    #                        [0]         [1]      [2]
    # index 0 is always the script. note that same applies if we type 'uv run main.py', index 0 is still main.py
    print(aggregate_meter_counts(email_path))
    return 0


if __name__ == "__main__":
    main()
