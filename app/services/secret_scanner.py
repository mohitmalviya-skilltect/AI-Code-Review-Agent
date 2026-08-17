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

    # -----------------------------------------------------
    # Gemini / Google API Key
    # -----------------------------------------------------

    (
        "Gemini API Key",
        re.compile(
            r"(?:GEMINI_API_KEY|GOOGLE_API_KEY)"
            r"\s*[:=]\s*"
            r"['\"]?"
            r"([A-Za-z0-9._\-]{20,})"
            r"['\"]?"
        ),
    ),

    # -----------------------------------------------------
    # GitHub Personal Access Token
    # -----------------------------------------------------

    (
        "GitHub Token",
        re.compile(
            r"(?:GITHUB_TOKEN|GH_TOKEN)"
            r"\s*[:=]\s*"
            r"['\"]?"
            r"(gh[pousr]_[A-Za-z0-9_]{20,}"
            r"|github_pat_[A-Za-z0-9_]{20,})"
            r"['\"]?"
        ),
    ),

    # -----------------------------------------------------
    # AWS Access Key
    # -----------------------------------------------------

    (
        "AWS Access Key",
        re.compile(
            r"(?:AWS_ACCESS_KEY_ID|aws_access_key_id)"
            r"\s*[:=]\s*"
            r"['\"]?"
            r"(AKIA[0-9A-Z]{16})"
            r"['\"]?"
        ),
    ),

    # -----------------------------------------------------
    # AWS Secret Access Key
    # -----------------------------------------------------

    (
        "AWS Secret Key",
        re.compile(
            r"(?:AWS_SECRET_ACCESS_KEY|aws_secret_access_key)"
            r"\s*[:=]\s*"
            r"['\"]?"
            r"([A-Za-z0-9/+=]{30,})"
            r"['\"]?"
        ),
    ),

    # -----------------------------------------------------
    # Private Key
    # -----------------------------------------------------

    (
        "Private Key",
        re.compile(
            r"-----BEGIN "
            r"(?:RSA |EC |OPENSSH |DSA |PGP )?"
            r"PRIVATE KEY-----"
        ),
    ),

    # -----------------------------------------------------
    # Password
    # -----------------------------------------------------

    (
        "Password",
        re.compile(
            r"(?:password|passwd|pwd)"
            r"\s*[:=]\s*"
            r"['\"]"
            r"[^'\"]{4,}"
            r"['\"]",
            re.IGNORECASE,
        ),
    ),

    # -----------------------------------------------------
    # Generic API Key
    # -----------------------------------------------------

    (
        "API Key",
        re.compile(
            r"(?:api[_-]?key|apikey)"
            r"\s*[:=]\s*"
            r"['\"]"
            r"[^'\"]{10,}"
            r"['\"]",
            re.IGNORECASE,
        ),
    ),

    # -----------------------------------------------------
    # Generic Secret
    # -----------------------------------------------------

    (
        "Secret",
        re.compile(
            r"(?:secret|client_secret)"
            r"\s*[:=]\s*"
            r"['\"]"
            r"[^'\"]{10,}"
            r"['\"]",
            re.IGNORECASE,
        ),
    ),
]


# =========================================================
# Extract added lines from Git diff
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

        # -------------------------------------------------
        # Parse diff hunk header
        #
        # Example:
        # @@ -4,5 +4,6 @@
        # -------------------------------------------------

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
                    .split(",", 1)[0]
                    .replace("+", "")
                )

            continue

        # -------------------------------------------------
        # Ignore diff metadata
        # -------------------------------------------------

        if line.startswith(
            ("---", "+++")
        ):
            continue

        if current_line is None:
            continue

        # -------------------------------------------------
        # Added line
        # -------------------------------------------------

        if line.startswith("+"):

            content = line[1:]

            added_lines.append(
                (
                    current_line,
                    content,
                )
            )

            current_line += 1

        # -------------------------------------------------
        # Removed line
        # -------------------------------------------------

        elif line.startswith("-"):

            # Removed lines don't exist in the
            # new version.

            continue

        # -------------------------------------------------
        # Context line
        # -------------------------------------------------

        else:

            current_line += 1

    return added_lines


# =========================================================
# Check whether a line is an environment-variable lookup
# =========================================================

def is_environment_variable_reference(
    line: str,
) -> bool:
    """
    Return True when the line retrieves a secret from
    an environment variable instead of hardcoding it.
    """

    environment_patterns = [
        r"os\.getenv\(",
        r"os\.environ\.get\(",
        r"process\.env\.",
        r"process\.env\[",
    ]

    return any(
        re.search(
            pattern,
            line,
        )
        for pattern in environment_patterns
    )


# =========================================================
# Scan added lines for secrets
# =========================================================

def scan_diff(
    file_path: str,
    patch: str,
) -> list[SecretFinding]:
    """
    Scan only newly added lines in a Git diff.

    Removed lines and unchanged lines are ignored.
    """

    findings = []

    added_lines = extract_added_lines(
        patch
    )

    for line_number, line in added_lines:

        # -------------------------------------------------
        # Ignore environment-variable references
        # -------------------------------------------------

        if is_environment_variable_reference(
            line
        ):
            continue

        # -------------------------------------------------
        # Check all secret patterns
        # -------------------------------------------------

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

            # -------------------------------------------------
            # Don't report multiple secrets for the same line
            # -------------------------------------------------

            break

    return findings


# =========================================================
# Scan multiple ReviewFile objects
# =========================================================

def scan_files(
    files: list,
) -> list[SecretFinding]:
    """
    Scan multiple ReviewFile objects for secrets.
    """

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