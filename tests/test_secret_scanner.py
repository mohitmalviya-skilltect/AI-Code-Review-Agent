from app.services.secret_scanner import (
    extract_added_lines,
    scan_diff,
    redact_secrets,
)


def test_extract_added_lines():

    patch = """@@ -1,3 +1,4 @@
 def example():
     value = 10
-    old_value = 20
+    new_value = 30
     return value
"""

    lines = extract_added_lines(
        patch
    )

    assert lines == [
        (3, "    new_value = 30"),
    ]


def test_detect_added_gemini_key():

    patch = """@@ -1,2 +1,3 @@
 import os
+GEMINI_API_KEY = "AIza12345678901234567890"
"""

    findings = scan_diff(
        file_path="config.py",
        patch=patch,
    )

    assert len(findings) == 1

    assert findings[0].secret_type == (
        "Gemini API Key"
    )

    assert findings[0].line == 2

    assert findings[0].severity == (
        "critical"
    )


def test_ignore_removed_secret():

    patch = """@@ -1,2 +1,2 @@
-GEMINI_API_KEY = "AIza12345678901234567890"
+api_key = os.getenv("GEMINI_API_KEY")
"""

    findings = scan_diff(
        file_path="config.py",
        patch=patch,
    )

    assert len(findings) == 0


def test_ignore_environment_variable():

    patch = """@@ -1,2 +1,3 @@
 import os
+api_key = os.getenv("GEMINI_API_KEY")
"""

    findings = scan_diff(
        file_path="config.py",
        patch=patch,
    )

    assert len(findings) == 0


def test_redact_secrets():
    # Test Gemini API key redaction
    assert redact_secrets('GEMINI_API_KEY = "AIza12345678901234567890"') == 'GEMINI_API_KEY = "[REDACTED_GEMINI_API_KEY]"'
    
    # Test Github token redaction
    assert redact_secrets('GH_TOKEN = "ghp_123456789012345678901234567890"') == 'GH_TOKEN = "[REDACTED_GITHUB_TOKEN]"'
    
    # Test password redaction
    assert redact_secrets('password: "mysecretpassword"') == 'password: "[REDACTED_PASSWORD]"'
    assert redact_secrets("passwd = 'another_pass'") == "passwd = '[REDACTED_PASSWORD]'"
    
    # Test non-secrets are not redacted
    assert redact_secrets("normal_var = 'value'") == "normal_var = 'value'"
    assert redact_secrets('os.getenv("GEMINI_API_KEY")') == 'os.getenv("GEMINI_API_KEY")'