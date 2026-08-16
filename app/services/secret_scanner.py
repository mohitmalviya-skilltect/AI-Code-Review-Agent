import re
from dataclasses import dataclass


@dataclass
class SecretFinding:
    file: str
    line: int
    severity: str
    category: str
    secret_type: str
    message: str


# =========================================================
# Secret patterns
# =========================================================

SECRET_PATTERNS = [
    (
        "Gemini API Key",
        re.compile(
            r"(?:GEMINI_API_KEY|GOOGLE_API_KEY)"
            r"\s*[:=]\s*['\"]?"
            r"([A-Za-z0-9_\-]{20,})"
        ),
    ),
    (
        "GitHub Token",
        re.compile(
            r"(?:GITHUB_TOKEN|GH_TOKEN)"
            r"\s*[:=]\s*['\"]?"
            r"(gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})"
        ),
    ),
    (
        "AWS Access Key",
        re.compile(
            r"(?:AWS_ACCESS_KEY_ID|aws_access_key_id)"
            r"\s*[:=]\s*['\"]?"
            r"(AKIA[0-9A-Z]{16})"
        ),
    ),
    (
        "AWS Secret Key",
        re.compile(
            r"(?:AWS_SECRET_ACCESS_KEY|aws_secret_access_key)"
            r"\s*[:=]\s*['\"]?"
            r"([A-Za-z0-9/+=]{30,})"
        ),
    ),
    (
        "Private Key",
        re.compile(
            r"-----BEGIN "
            r"(?:RSA |EC |OPENSSH |DSA )?"
            r"PRIVATE KEY-----"
        ),
    ),
    (
        "Password",
        re.compile(
            r"(?:password|passwd|pwd)"
            r"\s*[:=]\s*['\"]"
            r"[^'\"]{4,}"
            r"['\"]",
            re.IGNORECASE,
        ),
    ),
    (
        "API Key",
        re.compile(
            r"(?:api[_-]?key|apikey)"
            r"\s*[:=]\s*['\"]"
            r"[^'\"]{10,}"
            r"['\"]",
            re.IGNORECASE,
        ),
    ),
    (
        "Secret",
        re.compile(
            r"(?:secret|client_secret)"
            r"\s*[:=]\s*['\"]"
            r"[^'\"]{10,}"
            r"['\"]",
            re.IGNORECASE,
        ),
    ),
]


# =========================================================
# Extract added lines from a Git diff
# =========================================================

def extract_added_lines(
    patch: str,
) -> list[tuple[int, str]]:
    """
    Extract added lines and their actual file line numbers
    from a unified Git diff.

    Returns:
        [
            (line_number, line_content),
            ...
        ]
    """

    added_lines = []

    current_line = None

    for line in patch.splitlines():

        # ---------------------------------------------
        # Parse hunk header
        #
        # Example:
        # @@ -4,5 +4,6 @@
        # ---------------------------------------------

        if line.startswith("@@"):

            match = re.search(
                r"\+\d+(?:,\d+)?",
                line,
            )

            if match:

                new_file_range = match.group(
                    0
                )

                current_line = int(
                    new_file_range
                    .split(",")[0]
                    .replace("+", "")
                )

            continue

        # Ignore diff metadata
        if line.startswith(
            ("---", "+++")
        ):
            continue

        if current_line is None:
            continue

        # ---------------------------------------------
        # Added line
        # ---------------------------------------------

        if line.startswith("+"):

            content = line[1:]

            added_lines.append(
                (
                    current_line,
                    content,
                )
            )

            current_line += 1

        # ---------------------------------------------
        # Removed line
        # ---------------------------------------------

        elif line.startswith("-"):

            # Removed lines don't exist in the
            # new version, so don't increment
            # the new-file line number.
            continue

        # ---------------------------------------------
        # Context line
        # ---------------------------------------------

        else:

            current_line += 1

    return added_lines


# =========================================================
# Scan added lines for secrets
# =========================================================

def scan_diff(
    file_path: str,
    patch: str,
) -> list[SecretFinding]:

    findings = []

    added_lines = extract_added_lines(
        patch
    )

    for line_number, line in added_lines:

        # ---------------------------------------------
        # Ignore environment variable references
        # ---------------------------------------------

        if (
            "os.getenv(" in line
            or "os.environ.get(" in line
            or "process.env." in line
        ):
            continue

        for secret_type, pattern in SECRET_PATTERNS:

            match = pattern.search(
                line
            )

            if not match:
                continue

            findings.append(
                SecretFinding(
                    file=file_path,
                    line=line_number,
                    severity="critical",
                    category="security",
                    secret_type=secret_type,
                    message=(
                        f"Potential {secret_type} "
                        "detected in newly added code. "
                        "The credential should not "
                        "be committed to Git."
                    ),
                )
            )

            # Don't report multiple patterns
            # for the same line.
            break

    return findings


# =========================================================
# Scan multiple ReviewFile objects
# =========================================================

def scan_files(
    files: list,
) -> list[SecretFinding]:

    findings = []

    for file in files:

        file_path = getattr(
            file,
            "path",
            "",
        )

        diff = getattr(
            file,
            "diff",
            "",
        )

        if not file_path or not diff:
            continue

        file_findings = scan_diff(
            file_path=file_path,
            patch=diff,
        )

        findings.extend(
            file_findings
        )

    return findings