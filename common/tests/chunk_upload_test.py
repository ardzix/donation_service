import base64
import hashlib
import requests

CHUNK_SIZE = 1024 * 300  # 300 KB per chunk
FILE_PATH = "image.jpg"
FILE_NAME = "image.jpg"
UPLOAD_URL = "http://127.0.0.1:8000/api/file/chunk-upload/"
HEADERS = {
    "Authorization": "Bearer JWT_TOKEN",
    "Content-Type": "application/json",
}

def load_base64_encoded_file(file_path):
    with open(file_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded}"

def split_base64_to_chunks(base64_string, chunk_size):
    return [base64_string[i:i + chunk_size] for i in range(0, len(base64_string), chunk_size)]

def md5_checksum(base64_string):
    return hashlib.md5(base64_string.encode("utf-8")).hexdigest()

def safe_print_json_response(response, label=""):
    try:
        print(f"{label} ✅", response.json())
    except Exception:
        print(f"{label} ❌ Response not JSON:")
        print("   Status Code:", response.status_code)
        print("   Response Text:", response.text)

def upload_file():
    print("🔄 Loading and encoding file...")
    base64_data = load_base64_encoded_file(FILE_PATH)
    chunks = split_base64_to_chunks(base64_data, CHUNK_SIZE)
    checksum = md5_checksum(base64_data)

    print("📦 Sending init request...")
    init_res = requests.post(
        UPLOAD_URL + "?is_init=true",
        json={"file_name": FILE_NAME},
        headers=HEADERS
    )
    safe_print_json_response(init_res, "[INIT]")

    print("📤 Uploading chunks...")
    for index, chunk in enumerate(chunks):
        payload = {
            "file_name": FILE_NAME,
            "chunk": chunk,
            "chunk_no": index,
            "chunk_count": len(chunks),
        }
        res = requests.post(UPLOAD_URL, json=payload, headers=HEADERS)
        print(f"[CHUNK {index + 1}/{len(chunks)}] Status:", res.status_code)
        if res.status_code != 200:
            safe_print_json_response(res, f"[CHUNK ERROR {index}]")
            return

    print("🧾 Finalizing with checksum...")
    final_payload = {
        "file_name": FILE_NAME,
        "chunk_count": len(chunks),
        "checksum": checksum,
    }
    finalize_res = requests.post(
        UPLOAD_URL + "?is_checksum=true",
        json=final_payload,
        headers=HEADERS
    )

    safe_print_json_response(finalize_res, "[FINAL]")

if __name__ == "__main__":
    upload_file()
