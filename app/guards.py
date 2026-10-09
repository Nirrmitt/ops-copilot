"""Safety checks for read-only SQL."""
import re

FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|call|execute)\b", re.IGNORECASE)


def validate_select(sql: str, limit: int = 100) -> str:
    """Accept a single read-only SELECT and ensure it has a bounded row count."""
    cleaned = sql.strip()
    if not cleaned or "--" in cleaned or "/*" in cleaned or "*/" in cleaned:
        raise ValueError("SQL is empty or contains comments")
    if ";" in cleaned.rstrip(";"):
        raise ValueError("Multiple SQL statements are not allowed")
    cleaned = cleaned.rstrip(";").strip()
    if not re.match(r"(?is)^select\b", cleaned) or FORBIDDEN.search(cleaned):
        raise ValueError("Only a read-only SELECT is allowed")
    if re.search(r"(?is)\b(for\s+update|into\s+|pg_sleep\s*\()", cleaned):
        raise ValueError("Unsafe SQL construct")
    if re.search(r"(?is)\blimit\s+\d+", cleaned):
        cleaned = re.sub(r"(?is)\blimit\s+\d+", f"LIMIT {limit}", cleaned)
    else:
        cleaned += f" LIMIT {limit}"
    return cleaned
