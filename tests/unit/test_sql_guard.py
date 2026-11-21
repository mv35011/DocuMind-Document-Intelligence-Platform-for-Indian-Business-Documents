from documind.agent.sql_guard import SQLSecurityError, guard_and_format_sql


def test_sql_guard_valid_query():
    raw = "SELECT invoice_number, grand_total FROM v_invoices WHERE grand_total > 5000"
    guarded = guard_and_format_sql(raw)
    assert "LIMIT 200" in guarded
    assert "v_invoices" in guarded


def test_sql_guard_blocks_drop():
    bad_sql = "DROP TABLE users;"
    try:
        guard_and_format_sql(bad_sql)
        assert False, "Should have raised SQLSecurityError"
    except SQLSecurityError:
        pass


def test_sql_guard_blocks_stacked_queries():
    bad_sql = "SELECT * FROM v_invoices; DROP TABLE v_invoices;"
    try:
        guard_and_format_sql(bad_sql)
        assert False, "Should have blocked stacked statements"
    except SQLSecurityError:
        pass


def test_sql_guard_blocks_unauthorized_table():
    bad_sql = "SELECT email, password_hash FROM users"
    try:
        guard_and_format_sql(bad_sql)
        assert False, "Should have blocked access to users table"
    except SQLSecurityError:
        pass


def test_sql_guard_blocks_dangerous_functions():
    bad_sql = "SELECT pg_sleep(10) FROM v_invoices"
    try:
        guard_and_format_sql(bad_sql)
        assert False, "Should have blocked pg_sleep"
    except SQLSecurityError:
        pass
