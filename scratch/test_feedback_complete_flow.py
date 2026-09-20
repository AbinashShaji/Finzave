import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def run_test():
    print("=== FinZave Feedback Complete Flow Test ===")
    
    # 1. User A Session (Normal User)
    user_session = requests.Session()
    print("\n[User A] Logging in as 'abin'...")
    res = user_session.post(f"{BASE_URL}/auth/login", data={"username": "abin", "password": "password123"})
    
    print("[User A] Submitting new feedback...")
    feedback_payload = {
        "category": "Bug Report",
        "message": "Automated test bug report content"
    }
    csrf_token = user_session.cookies.get('csrf_access_token')
    headers = {"X-CSRF-TOKEN": csrf_token} if csrf_token else {}
    
    res = user_session.post(f"{BASE_URL}/api/feedback", json=feedback_payload, headers=headers)
    if res.status_code == 201:
        print("[User A] Feedback submitted successfully! Status Code 201")
        data = res.json()
        print(f"         Data: {data.get('feedback')}")
    else:
        print(f"[User A] Failed to submit feedback: {res.status_code} {res.text}")
        return

    # 2. Security Test - Normal user trying to access admin feedback
    print("\n[Security Test] Normal user trying to access GET /api/admin/feedback...")
    res = user_session.get(f"{BASE_URL}/api/admin/feedback")
    if res.status_code in [401, 403, 302]: # 302 is redirect to login or error
        print(f"[Security Test] PASSED: Normal user denied ({res.status_code})")
    else:
        print(f"[Security Test] FAILED: Normal user got status {res.status_code}")

    # 3. Admin Session
    admin_session = requests.Session()
    print("\n[Admin] Logging in as 'admin_feedback'...")
    res = admin_session.post(f"{BASE_URL}/auth/login", data={"username": "admin_feedback", "password": "password123"})
    
    print("[Admin] Fetching all feedback from GET /api/admin/feedback...")
    res = admin_session.get(f"{BASE_URL}/api/admin/feedback")
    if res.status_code == 200:
        feedbacks = res.json()
        print(f"[Admin] Found {len(feedbacks)} feedbacks.")
        
        # Find the one we just submitted
        target = next((f for f in feedbacks if f['content'] == "Automated test bug report content"), None)
        if target:
            print(f"[Admin] Target feedback found! ID: {target['id']}, Status: {target['status']}")
            
            # 4. Admin updates status
            print(f"\n[Admin] Updating status to 'in_progress'...")
            admin_csrf = admin_session.cookies.get('csrf_access_token')
            admin_headers = {"X-CSRF-TOKEN": admin_csrf} if admin_csrf else {}
            
            patch_res = admin_session.patch(f"{BASE_URL}/api/admin/feedback/{target['id']}/status", 
                                          json={"status": "in_progress"}, headers=admin_headers)
            if patch_res.status_code == 200:
                print("[Admin] Status updated successfully!")
            else:
                print(f"[Admin] Failed to update status: {patch_res.status_code}")
                
            # Update to resolved
            print(f"[Admin] Updating status to 'resolved'...")
            patch_res = admin_session.patch(f"{BASE_URL}/api/admin/feedback/{target['id']}/status", 
                                          json={"status": "resolved"}, headers=admin_headers)
            if patch_res.status_code == 200:
                print("[Admin] Status updated to resolved successfully!")
            else:
                print(f"[Admin] Failed to update status: {patch_res.status_code}")
                
        else:
            print("[Admin] Target feedback NOT found!")
    else:
        print(f"[Admin] Failed to fetch feedback: {res.status_code}")

    # 5. Security - CSRF Test
    print("\n[Security Test] Admin updating without CSRF...")
    patch_res = admin_session.patch(f"{BASE_URL}/api/admin/feedback/{target['id']}/status", 
                                    json={"status": "pending"})
    if patch_res.status_code in [400, 401]:
        print(f"[Security Test] PASSED: Missing CSRF denied ({patch_res.status_code})")
    else:
        print(f"[Security Test] FAILED: Missing CSRF got status {patch_res.status_code}")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    run_test()
    if res.status_code == 200:
        feedbacks = res.json()
        print(f"[Admin] Found {len(feedbacks)} feedbacks.")
        # Find the one we just submitted
        target = next((f for f in feedbacks if f['content'] == "Automated test bug report content"), None)
        if target:
            print(f"[Admin] Target feedback found! ID: {target['id']}, Status: {target['status']}")
            
            # 4. Admin updates status
            print(f"\n[Admin] Updating status to 'in_progress'...")
            admin_csrf = admin_session.cookies.get('csrf_access_token')
            admin_headers = {"X-CSRF-TOKEN": admin_csrf} if admin_csrf else {}
            
            patch_res = admin_session.patch(f"{BASE_URL}/api/admin/feedback/{target['id']}/status", 
                                          json={"status": "in_progress"}, headers=admin_headers)
            if patch_res.status_code == 200:
                print("[Admin] Status updated successfully!")
            else:
                print(f"[Admin] Failed to update status: {patch_res.status_code}")
                
            # Update to resolved
            print(f"[Admin] Updating status to 'resolved'...")
            patch_res = admin_session.patch(f"{BASE_URL}/api/admin/feedback/{target['id']}/status", 
                                          json={"status": "resolved"}, headers=admin_headers)
            if patch_res.status_code == 200:
                print("[Admin] Status updated to resolved successfully!")
            else:
                print(f"[Admin] Failed to update status: {patch_res.status_code}")
                
        else:
            print("[Admin] Target feedback NOT found!")
    else:
        print(f"[Admin] Failed to fetch feedback: {res.status_code}")

    # 5. Security - CSRF Test
    print("\n[Security Test] Admin updating without CSRF...")
    patch_res = admin_session.patch(f"{BASE_URL}/api/admin/feedback/{target['id']}/status", 
                                    json={"status": "pending"})
    if patch_res.status_code in [400, 401]:
        print(f"[Security Test] PASSED: Missing CSRF denied ({patch_res.status_code})")
    else:
        print(f"[Security Test] FAILED: Missing CSRF got status {patch_res.status_code}")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    run_test()
