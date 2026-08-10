from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

ok = True
errors = []

resp = client.get("/openapi.json")
if resp.status_code != 200:
    print("FAILED: could not fetch /openapi.json", resp.status_code)
    raise SystemExit(1)

spec = resp.json()

# Check uploads paths have Services tag
uploads_paths = [p for p in spec.get("paths", {}) if p.startswith("/uploads")]
for p in uploads_paths:
    tags = spec["paths"][p]
    # methods like post, get
    for method, data in tags.items():
        tag_list = data.get("tags", [])
        if "Services" not in tag_list:
            ok = False
            errors.append(f"Path {p} method {method} missing 'Services' tag: {tag_list}")

# Check auth/profile responses do not include profile_image
profile_path = "/auth/profile"
if profile_path in spec.get("paths", {}):
    get_op = spec["paths"][profile_path].get("get", {})
    # response schema ref
    responses = get_op.get("responses", {})
    schema = None
    for code, r in responses.items():
        content = r.get("content", {})
        app_json = content.get("application/json")
        if app_json:
            schema = app_json.get("schema")
            break
    if not schema:
        ok = False
        errors.append("Could not find response schema for /auth/profile GET")
    else:
        # resolve $ref if present
        def resolve(ref):
            if "$ref" in ref:
                ref_path = ref["$ref"].split("/")
                node = spec
                for part in ref_path[1:]:
                    node = node.get(part)
                return node
            return ref
        resolved = resolve(schema)
        props = resolved.get("properties", {})
        if "profile_image" in props:
            ok = False
            errors.append("profile_image present in /auth/profile response schema")
else:
    ok = False
    errors.append("/auth/profile path not found in OpenAPI spec")

# Check users endpoints responses don't include profile_image
users_paths = ["/users", "/users/{user_id}"]
for p in users_paths:
    if p in spec.get("paths", {}):
        # check GET response
        get_op = spec["paths"][p].get("get", {})
        responses = get_op.get("responses", {})
        schema = None
        for code, r in responses.items():
            content = r.get("content", {})
            app_json = content.get("application/json")
            if app_json:
                schema = app_json.get("schema")
                break
        if not schema:
            ok = False
            errors.append(f"Could not find response schema for {p} GET")
        else:
            def resolve(ref):
                if "$ref" in ref:
                    ref_path = ref["$ref"].split("/")
                    node = spec
                    for part in ref_path[1:]:
                        node = node.get(part)
                    return node
                return ref
            resolved = resolve(schema)
            # if it's an array, resolve items
            if resolved.get("type") == "array":
                items = resolved.get("items", {})
                resolved = resolve(items)
            props = resolved.get("properties", {})
            if "profile_image" in props:
                ok = False
                errors.append(f"profile_image present in {p} response schema")
    else:
        ok = False
        errors.append(f"{p} path not found in OpenAPI spec")

if ok:
    print("SMOKE OK: OpenAPI checks passed")
else:
    print("SMOKE FAILED")
    for e in errors:
        print(" -", e)
    raise SystemExit(2)
