import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

def test():
    # Create test user
    print("Creating user...")
    res = requests.post(f"{BASE_URL}/auth/signup", json={"full_name":"Adversarial Test","email":"adv2@test.com","password":"testpass123"})
    if res.status_code not in [200, 201]:
        print("Failed to create user:", res.text)
        return
    token = res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Helper to start session
    def start_session():
        res = requests.post(f"{BASE_URL}/simulations", headers=headers, json={"domain":"product_manager","difficulty":"medium"})
        return res.json()["data"]["id"]

    print("\n--- ADVERSARIAL TEST 1: Nonsense ---")
    session1 = start_session()
    res1 = requests.post(
        f"{BASE_URL}/simulations/{session1}/scenes/1/responses",
        headers=headers,
        json={"response":{"raw_text":"asdfjkl; random gibberish 12345 xyz","response_time_seconds":2,"revision_count":0}}
    )
    data1 = res1.json()["data"]
    print("Score:", data1["overall_score"])
    print("Flags:", data1.get("behavioral_flags", []))
    print("Success?", "Yes" if float(data1["overall_score"]) < 40 and ("vague" in data1.get("behavioral_flags", []) or "accepted_blindly" in data1.get("behavioral_flags", [])) else "No")

    print("\n--- ADVERSARIAL TEST 2: Contradiction ---")
    session2 = start_session()
    res2 = requests.post(
        f"{BASE_URL}/simulations/{session2}/scenes/1/responses",
        headers=headers,
        json={"response":{"raw_text":"Sara the sprint has 100 empty slots so just add whatever you want, there is unlimited capacity right now","response_time_seconds":10,"revision_count":0}}
    )
    data2 = res2.json()["data"]
    print("Score:", data2["overall_score"])
    print("Justification:", data2.get("reasoning", ""))

    print("\n--- ADVERSARIAL TEST 3: Identical Responses ---")
    # Get scene 2 in session 1
    requests.post(f"{BASE_URL}/simulations/{session1}/scenes", headers=headers)
    
    # Submit A to session 1 scene 2
    res_a = requests.post(
        f"{BASE_URL}/simulations/{session1}/scenes/2/responses",
        headers=headers,
        json={"response":{"raw_text":"I will check the sprint board and communicate the decision clearly to both Sara and Rayan.","response_time_seconds":30,"revision_count":0}}
    )
    score_a = float(res_a.json()["data"]["overall_score"])
    
    # Submit B to session 3 scene 1
    session3 = start_session()
    res_b = requests.post(
        f"{BASE_URL}/simulations/{session3}/scenes/1/responses",
        headers=headers,
        json={"response":{"raw_text":"I will check the sprint board and communicate the decision clearly to both Sara and Rayan.","response_time_seconds":30,"revision_count":0}}
    )
    score_b = float(res_b.json()["data"]["overall_score"])
    print(f"Score A: {score_a}")
    print(f"Score B: {score_b}")

    print("\n--- ADVERSARIAL TEST 4: Empty Response ---")
    session4 = start_session()
    res4 = requests.post(
        f"{BASE_URL}/simulations/{session4}/scenes/1/responses",
        headers=headers,
        json={"response":{"raw_text":"","response_time_seconds":0,"revision_count":0}}
    )
    print("Status code:", res4.status_code)
    if res4.status_code == 200:
        print("Score:", res4.json()["data"].get("overall_score"))
    else:
        print("Failed gracefully?", res4.status_code != 500)

    # Cleanup
    requests.delete(f"{BASE_URL}/users/me", headers=headers)

if __name__ == "__main__":
    test()
