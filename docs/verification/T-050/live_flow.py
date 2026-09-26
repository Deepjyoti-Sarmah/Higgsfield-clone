"""T-050 live end-to-end: face -> clip -> video face swap -> sequence.

Run: python3 docs/verification/T-050/live_flow.py https://api-production-8afc.up.railway.app
"""
import http.cookiejar, json, sys, time, urllib.error, urllib.request, uuid
from pathlib import Path

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://api-production-8afc.up.railway.app"
API = "/api/v1"
UA = "live-flow/1.0"
TARGET_IMAGE = "apps/web/public/showcase/sample-03.jpg"
TIMEOUTS = {"image": 300, "clip": 600, "swap": 800, "sequence": 300}

failures = []


def check(label, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + label + ((": " + str(detail)) if detail else ""), flush=True)
    if not ok:
        failures.append(label)


def raw(path, method, payload=None, jar=None, expect=None):
    body = None if payload is None else json.dumps(payload).encode()
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    try:
        with opener.open(request, timeout=60) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def api(path, method, payload=None, jar=None, expect=200):
    status, body = raw(path, method, payload, jar)
    if status != expect:
        raise SystemExit(f"{method} {path} -> {status} (expected {expect}): {body[:300]!r}")
    return json.loads(body) if body else None


def upload(file_path, jar):
    data = Path(file_path).read_bytes()
    created = api(f"{API}/uploads", "POST", {"content_type": "image/jpeg", "byte_size": len(data)}, jar, 201)
    headers = {"User-Agent": UA, "Content-Length": str(len(data))}
    headers.update(created.get("upload_headers") or {})
    request = urllib.request.Request(created["upload_url"], data=data, headers=headers, method="PUT")
    with urllib.request.urlopen(request, timeout=120) as response:
        assert response.status in (200, 201, 204), response.status
    asset = api(f"{API}/uploads/{created['asset_id']}/complete", "POST", None, jar)
    return created["asset_id"], asset["status"]


def wait(path, job_id, timeout, jar):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = api(f"{path}/{job_id}", "GET", None, jar)
        if job["status"] == "succeeded":
            return job
        if job["status"] == "failed":
            raise SystemExit(f"job {job_id} failed: {job.get('error_message')}")
        time.sleep(5)
    raise SystemExit(f"job {job_id} did not finish in {timeout}s")


def main():
    jar = http.cookiejar.CookieJar()
    status, body = raw(f"{API}/auth/guest", "POST", None, jar)
    check("guest session", status == 201, f"HTTP {status}")
    if status != 201:
        print("STOP: guest cap or auth, no bypass attempted:", body[:200])
        return
    me = api(f"{API}/me", "GET", None, jar)
    print("guest", me["id"], "balance", api(f"{API}/credits", "GET", None, jar)["balance"], flush=True)

    face = api(f"{API}/image-jobs", "POST", {
        "prompt": "portrait of a man with short dark hair and a beard, front facing, even studio light",
        "aspect_ratio": "1:1", "quality": "standard", "count": 1,
        "idempotency_key": "t050-live-face-" + str(uuid.uuid4())}, jar, 202)
    face_job = wait(f"{API}/image-jobs", face["id"], TIMEOUTS["image"], jar)
    library = api(f"{API}/jobs", "GET", None, jar)
    item = next(entry for entry in library["items"] if entry["id"] == face["id"])
    face_asset = item["images"][0]["asset_id"]
    check("source face generated", bool(face_asset), f"job {face['id']} -> {face_job['image_urls'][0][:70]}")
    print("FACE_URL", face_job["image_urls"][0], flush=True)

    target_asset, asset_status = upload(TARGET_IMAGE, jar)
    check("target still uploaded", asset_status == "ready", target_asset)
    clip = api(f"{API}/jobs", "POST", {
        "preset_slug": "slow-drift", "input_asset_id": target_asset,
        "prompt": "portrait, gentle drift, face steady",
        "idempotency_key": "t050-live-clip-" + str(uuid.uuid4())}, jar, 202)
    clip_job = wait(f"{API}/jobs", clip["id"], TIMEOUTS["clip"], jar)
    check("target clip rendered", clip_job["status"] == "succeeded",
          f"{clip['id']} generated_by={clip_job.get('generated_by')} duration={clip_job.get('duration_ms')}")
    print("CLIP_URL", clip_job["video_url"], flush=True)

    swap = api(f"{API}/video-faceswap-jobs", "POST", {
        "source_asset_id": face_asset, "target_job_id": clip["id"],
        "idempotency_key": "t050-live-swap-" + str(uuid.uuid4())}, jar, 202)
    check("video swap accepted", swap["status"] in ("queued", "running"),
          f"cost={swap['credit_cost']}")
    swap_job = wait(f"{API}/video-faceswap-jobs", swap["id"], TIMEOUTS["swap"], jar)
    check("video swap rendered", swap_job["status"] == "succeeded",
          f"generated_by={swap_job.get('generated_by')} duration={swap_job.get('duration_ms')}")
    print("SWAP_URL", swap_job["video_url"], flush=True)

    sequence = api(f"{API}/sequence-jobs", "POST", {
        "clips": [
            {"job_id": clip["id"], "transition_in": "cut"},
            {"job_id": swap["id"], "transition_in": "crossfade"},
        ],
        "idempotency_key": "t050-live-seq-" + str(uuid.uuid4())}, jar, 202)
    sequence_job = wait(f"{API}/sequence-jobs", sequence["id"], TIMEOUTS["sequence"], jar)
    check("sequence with swapped video rendered", sequence_job["status"] == "succeeded",
          f"clip_count={sequence_job.get('clip_count')} duration={sequence_job.get('duration_ms')}")
    print("SEQUENCE_URL", sequence_job["video_url"], flush=True)

    balance = api(f"{API}/credits", "GET", None, jar)["balance"]
    spent = face["credit_cost"] + clip["credit_cost"] + swap["credit_cost"] + sequence["credit_cost"]
    check("credits settled", balance == 60 - spent, f"balance={balance} spent={spent}")

    print("RESULT", "PASS" if not failures else "FAIL " + ",".join(failures), flush=True)


if __name__ == "__main__":
    main()
