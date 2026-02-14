"""Business logic for application CRUD and data transforms."""

import json
from datetime import datetime, date, timedelta, timezone


def generate_id(seq_val: int) -> str:
    year = datetime.now().year
    return f"RK-{year}-{seq_val:05d}"


def calculate_progress(checks: dict | None) -> int:
    if not checks:
        return 0
    keys = list(checks.keys())
    if not keys:
        return 0
    complete = sum(1 for k in keys if checks[k].get("status") == "complete")
    return round((complete / len(keys)) * 100)


def build_checks_from_form(body: dict) -> dict:
    checks = {
        "dbs": {"status": "not-started", "date": None},
        "dbs_update": {"status": "not-started", "date": None},
        "la_check": {"status": "not-started", "date": None},
        "ofsted": {"status": "not-started", "date": None},
        "gp_health": {"status": "not-started", "date": None},
        "ref_1": {"status": "not-started", "date": None},
        "ref_2": {"status": "not-started", "date": None},
        "first_aid": {"status": "not-started", "date": None},
        "safeguarding": {"status": "not-started", "date": None},
        "food_hygiene": {"status": "not-started", "date": None},
        "insurance": {"status": "not-started", "date": None},
    }

    suit = body.get("suitability") or {}
    if suit.get("hasDBS") == "Yes" and suit.get("dbsNumber"):
        today = date.today().isoformat()
        checks["dbs"] = {
            "status": "pending",
            "date": today,
            "certificate": suit["dbsNumber"],
            "details": "Certificate number provided on application",
        }

    quals = body.get("qualifications") or {}
    if quals.get("firstAidCompleted") == "Yes":
        checks["first_aid"] = {
            "status": "complete",
            "date": quals.get("firstAidDate") or None,
            "provider": quals.get("firstAidOrg") or None,
        }
    if quals.get("safeguardingCompleted") == "Yes":
        checks["safeguarding"] = {
            "status": "complete",
            "date": quals.get("safeguardingDate") or None,
            "provider": quals.get("safeguardingOrg") or None,
        }
    if quals.get("foodHygieneCompleted") == "Yes":
        checks["food_hygiene"] = {
            "status": "complete",
            "date": quals.get("foodHygieneDate") or None,
            "provider": quals.get("foodHygieneOrg") or None,
        }

    refs = body.get("references") or {}
    today = date.today().isoformat()
    if refs.get("ref1", {}).get("name"):
        checks["ref_1"] = {
            "status": "pending",
            "date": today,
            "referee": refs["ref1"]["name"],
            "relationship": refs["ref1"].get("relationship") or None,
            "details": "Reference request to be sent",
        }
    if refs.get("ref2", {}).get("name"):
        checks["ref_2"] = {
            "status": "pending",
            "date": today,
            "referee": refs["ref2"]["name"],
            "relationship": refs["ref2"].get("relationship") or None,
            "details": "Reference request to be sent",
        }

    return checks


def build_connected_persons(body: dict) -> list:
    persons = []
    household = body.get("household") or {}
    adults = household.get("adults") or []
    for i, adult in enumerate(adults):
        if adult.get("firstName") and adult.get("lastName"):
            persons.append({
                "id": f"CP-NEW-{i + 1:03d}",
                "name": f"{adult['firstName']} {adult['lastName']}",
                "type": "household",
                "relationship": adult.get("relationship") or "Household member",
                "dob": adult.get("dob") or None,
                "formStatus": "not-started",
                "formType": "CMA-H2",
                "checks": {
                    "dbs": {"status": "not-started", "date": None},
                    "la_check": {"status": "not-started", "date": None},
                },
            })
    return persons


def build_premises_address(body: dict) -> str | None:
    premises = body.get("premises") or {}
    pt = premises.get("type") or "Domestic"
    same_as_home = premises.get("sameAsHome")

    if pt == "Domestic" and same_as_home is not False:
        ha = body.get("homeAddress") or {}
        parts = [ha.get("line1"), ha.get("line2"), ha.get("town"), ha.get("postcode")]
        return ", ".join(p for p in parts if p) or None

    ca = premises.get("address") or {}
    parts = [ca.get("line1"), ca.get("line2"), ca.get("town"), ca.get("postcode")]
    return ", ".join(p for p in parts if p) or None


def _json_or_none(val) -> str | None:
    if val is None:
        return None
    return json.dumps(val)


def _format_date(dt) -> str | None:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d")
    if isinstance(dt, date):
        return dt.isoformat()
    return str(dt)[:10]


def _format_datetime(dt) -> str | None:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M")
    return str(dt)[:16]


def _parse_jsonb(val):
    if val is None:
        return None
    if isinstance(val, str):
        return json.loads(val)
    return val


def to_dashboard_shape(row: dict, timeline: list[dict]) -> dict:
    now = datetime.now(timezone.utc)
    last_updated = row.get("last_updated") or now
    if isinstance(last_updated, date) and not isinstance(last_updated, datetime):
        last_updated = datetime.combine(last_updated, datetime.min.time(), tzinfo=timezone.utc)
    elif isinstance(last_updated, datetime) and last_updated.tzinfo is None:
        last_updated = last_updated.replace(tzinfo=timezone.utc)
    days_in_stage = max(0, (now - last_updated).days)

    checks = _parse_jsonb(row.get("checks")) or {}
    connected = _parse_jsonb(row.get("connected_persons")) or []
    registers = _parse_jsonb(row.get("registers")) or []
    ofsted = _parse_jsonb(row.get("ofsted_check"))
    household = _parse_jsonb(row.get("household"))
    service = _parse_jsonb(row.get("service"))
    premises_details = _parse_jsonb(row.get("premises_details"))

    result = {
        "id": row["id"],
        "name": row.get("name") or "",
        "email": row.get("email") or "",
        "phone": row.get("phone") or "",
        "dob": _format_date(row.get("dob")),
        "stage": row.get("stage") or "new",
        "startDate": _format_date(row.get("start_date")),
        "registrationDate": _format_date(row.get("registration_date")),
        "lastUpdated": _format_date(row.get("last_updated")),
        "daysInStage": days_in_stage,
        "risk": row.get("risk") or "low",
        "progress": row.get("progress") or 0,
        "premisesType": row.get("premises_type") or "",
        "premisesAddress": row.get("premises_address") or "",
        "localAuthority": row.get("local_authority") or "",
        "registers": registers,
        "checks": checks,
        "connectedPersons": connected,
        "timeline": [
            {
                "date": _format_datetime(t.get("created_at")),
                "event": t.get("event"),
                "type": t.get("type"),
            }
            for t in reversed(timeline)
        ],
    }

    if row.get("ni_number"):
        result["niNumber"] = row["ni_number"]
    if row.get("registration_number"):
        result["registrationNumber"] = row["registration_number"]
    if ofsted is not None:
        result["ofstedCheck"] = ofsted
    if household is not None:
        result["household"] = household
    if service is not None:
        result["service"] = service
    if premises_details is not None:
        result["premisesDetails"] = premises_details

    return result


async def create_application(pool, body: dict) -> str:
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT nextval('application_id_seq') AS val"
            )
            app_id = generate_id(int(row["val"]))
            now = datetime.now()

            checks = build_checks_from_form(body)
            connected = build_connected_persons(body)
            progress = calculate_progress(checks)
            premises_addr = build_premises_address(body)

            registers = (body.get("service") or {}).get("ageGroups") or []

            premises = body.get("premises") or {}
            premises_details = {
                "sameAsHome": premises.get("sameAsHome"),
                "outdoorSpace": premises.get("outdoorSpace") or None,
                "pets": premises.get("pets") or None,
                "petsDetails": premises.get("petsDetails") or None,
            }

            personal = body.get("personal") or {}

            await conn.execute(
                """INSERT INTO applications (
                    id, title, first_name, middle_names, last_name,
                    email, phone, dob, gender, right_to_work, ni_number,
                    home_address, premises_type, premises_address,
                    premises_details, local_authority,
                    registers, service, stage, risk, progress,
                    checks, connected_persons,
                    previous_names, address_history, qualifications,
                    employment_history, references_data,
                    household, suitability, declaration,
                    start_date, last_updated, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5,
                    $6, $7, $8, $9, $10, $11,
                    $12, $13, $14,
                    $15, $16,
                    $17, $18, 'new', 'low', $19,
                    $20, $21,
                    $22, $23, $24,
                    $25, $26,
                    $27, $28, $29,
                    $30, $31, $31
                )""",
                app_id,
                personal.get("title") or None,
                personal.get("firstName"),
                personal.get("middleNames") or None,
                personal.get("lastName"),
                personal.get("email"),
                personal.get("phone") or None,
                personal.get("dob") or None,
                personal.get("gender") or None,
                personal.get("rightToWork") or None,
                personal.get("niNumber") or None,
                json.dumps(body.get("homeAddress") or {}),
                (premises.get("type") or "domestic").lower(),
                premises_addr,
                json.dumps(premises_details),
                premises.get("localAuthority") or None,
                json.dumps(registers),
                _json_or_none(body.get("service")),
                progress,
                json.dumps(checks),
                json.dumps(connected),
                _json_or_none(body.get("previousNames")),
                _json_or_none(body.get("addressHistory")),
                _json_or_none(body.get("qualifications")),
                _json_or_none(body.get("employment")),
                _json_or_none(body.get("references")),
                _json_or_none(body.get("household")),
                _json_or_none(body.get("suitability")),
                _json_or_none(body.get("declaration")),
                now,
                now,
            )

            await conn.execute(
                """INSERT INTO timeline_events (application_id, event, type, created_at)
                   VALUES ($1, 'Application started', 'action', $2)""",
                app_id, now,
            )
            await conn.execute(
                """INSERT INTO timeline_events (application_id, event, type, created_at)
                   VALUES ($1, 'Application form submitted', 'complete', $2)""",
                app_id, now + timedelta(seconds=1),
            )

            return app_id


async def get_all_applications(pool) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM applications ORDER BY created_at DESC"
        )
        result = []
        for row in rows:
            tl = await conn.fetch(
                """SELECT event, type, created_at FROM timeline_events
                   WHERE application_id = $1 ORDER BY created_at ASC""",
                row["id"],
            )
            result.append(
                to_dashboard_shape(dict(row), [dict(t) for t in tl])
            )
        return result


async def get_application(pool, app_id: str) -> dict | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM applications WHERE id = $1", app_id
        )
        if not row:
            return None
        tl = await conn.fetch(
            """SELECT event, type, created_at FROM timeline_events
               WHERE application_id = $1 ORDER BY created_at ASC""",
            app_id,
        )
        return to_dashboard_shape(dict(row), [dict(t) for t in tl])


async def update_application(pool, app_id: str, updates: dict) -> bool:
    allowed = {
        "stage": "stage",
        "risk": "risk",
        "progress": "progress",
        "checks": "checks",
        "connected_persons": "connected_persons",
        "connectedPersons": "connected_persons",
        "ofsted_check": "ofsted_check",
        "ofstedCheck": "ofsted_check",
        "registration_date": "registration_date",
        "registrationDate": "registration_date",
        "registration_number": "registration_number",
        "registrationNumber": "registration_number",
    }

    json_cols = {"checks", "connected_persons", "ofsted_check"}
    sets = []
    vals = []
    idx = 1

    for key, val in updates.items():
        col = allowed.get(key)
        if not col:
            continue
        sets.append(f"{col} = ${idx}")
        vals.append(json.dumps(val) if col in json_cols else val)
        idx += 1

    if not sets:
        return False

    sets.append("last_updated = NOW()")
    vals.append(app_id)

    async with pool.acquire() as conn:
        result = await conn.execute(
            f"UPDATE applications SET {', '.join(sets)} WHERE id = ${idx} RETURNING id",
            *vals,
        )
        return "UPDATE" in result


async def delete_application(pool, app_id: str) -> bool:
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM applications WHERE id = $1", app_id
        )
        return "DELETE 1" in result


async def add_timeline_event(pool, app_id: str, event: str, event_type: str = "action") -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO timeline_events (application_id, event, type)
               VALUES ($1, $2, $3) RETURNING *""",
            app_id, event, event_type,
        )
        return dict(row)
