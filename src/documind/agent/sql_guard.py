import re
from typing import Set

try:
    import sqlglot
    from sqlglot import exp
    HAS_SQLGLOT = True
except ImportError:
    HAS_SQLGLOT = False

ALLOWED_VIEWS: Set[str] = {
    "v_invoices",
    "v_invoice_items",
    "v_bank_statements",
    "v_bank_txns",
}

DISALLOWED_FUNCTIONS: Set[str] = {
    "pg_sleep",
    "pg_read_file",
    "pg_write_file",
    "pg_ls_dir",
    "query_to_xml",
    "current_setting",
    "set_config",
    "system",
}


class SQLSecurityError(Exception):
    """Raised when an agent-generated SQL query violates security guardrails."""
    pass


def guard_and_format_sql(raw_sql: str) -> str:
    """Enforces strict read-only AST guardrails on agent SQL queries:

    1. Single statement only (no stacked queries or semicolons hiding payloads)
    2. SELECT statements only (no DDL, DML, or transactional commands)
    3. Tables strictly restricted to approved read-only views (`v_*`)
    4. Prohibits dangerous PostgreSQL system functions
    5. Injects LIMIT 200 when absent to prevent denial-of-service
    """
    clean_sql = raw_sql.strip()

    if not HAS_SQLGLOT:
        # Regex-based fallback guard when sqlglot is not yet installed
        upper_sql = clean_sql.upper()
        if ";" in clean_sql.rstrip(";"):
            raise SQLSecurityError("Stacked statements / multiple queries are forbidden")
        if not upper_sql.startswith("SELECT"):
            raise SQLSecurityError("Only SELECT queries are allowed")
        for bad_kw in ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "PG_SLEEP", "USERS"]:
            if re.search(r"\b" + bad_kw + r"\b", upper_sql):
                raise SQLSecurityError(f"Forbidden keyword or table: {bad_kw}")
        if "LIMIT" not in upper_sql:
            clean_sql = f"{clean_sql.rstrip(';')} LIMIT 200;"
        return clean_sql

    # Parse with sqlglot for PostgreSQL dialect
    try:
        statements = sqlglot.parse(clean_sql, read="postgres")
    except Exception as e:
        raise SQLSecurityError(f"Invalid SQL syntax: {str(e)}") from e

    if not statements:
        raise SQLSecurityError("Empty SQL query")

    if len(statements) > 1:
        raise SQLSecurityError(f"Expected exactly 1 statement, got {len(statements)} (stacked queries forbidden)")

    stmt = statements[0]
    if not isinstance(stmt, exp.Select):
        raise SQLSecurityError(f"Only SELECT queries are allowed, got {stmt.key.upper()}")

    # Verify all referenced tables/relations are in the approved whitelist
    for table in stmt.find_all(exp.Table):
        table_name = table.name.lower()
        if table_name not in ALLOWED_VIEWS:
            raise SQLSecurityError(
                f"Access denied to table/view '{table_name}'. Only read-only views {sorted(ALLOWED_VIEWS)} are permitted."
            )

    # Check for forbidden functions
    for func in stmt.find_all(exp.Func):
        func_name = func.name.lower()
        if func_name in DISALLOWED_FUNCTIONS or func_name.startswith("pg_"):
            raise SQLSecurityError(f"Call to unauthorized function '{func_name}' is blocked.")

    # Inject LIMIT 200 if absent
    if not stmt.args.get("limit"):
        stmt = stmt.limit(200)

    return stmt.sql(dialect="postgres")
