"""R1 · The roles: two logins, groups without logins, nobody super."""


def test_roles(admin):
    rows = admin.execute(
        """select rolname, rolcanlogin, rolinherit, rolbypassrls, rolsuper, rolcreaterole, rolcreatedb
           from pg_roles where rolname in ('lab_owner', 'clinician', 'microbiologist', 'ecb_app', 'ecb_backup')"""
    ).fetchall()
    roles = {row.pop("rolname"): row for row in rows}
    assert set(roles) == {"lab_owner", "clinician", "microbiologist", "ecb_app", "ecb_backup"}
    assert {name for name, role in roles.items() if role["rolcanlogin"]} == {"ecb_app", "ecb_backup"}
    assert roles["ecb_app"]["rolinherit"] is False
    assert {name for name, role in roles.items() if role["rolbypassrls"]} == {"ecb_backup"}
    assert not any(role["rolsuper"] or role["rolcreaterole"] or role["rolcreatedb"] for role in roles.values())
    members = admin.execute(
        """select r.rolname from pg_auth_members m join pg_roles r on r.oid = m.roleid
           join pg_roles u on u.oid = m.member where u.rolname = 'ecb_app' order by 1"""
    ).fetchall()
    assert [row["rolname"] for row in members] == ["clinician", "microbiologist"]
