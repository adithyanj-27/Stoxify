import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from fastapi import HTTPException
from starlette.requests import Request
import database
from main import (
    api_check_username, 
    api_create_user, 
    api_login_user, 
    api_update_user_profile, 
    CreateUserRequest, 
    LoginRequest, 
    UpdateProfileRequest
)

def test_credentials_flow():
    print("=======================================================")
    print(" Testing Username & Password System (Stoxify v7.2)")
    print("=======================================================")

    database.init_db()

    # 1. Test api_check_username API endpoint
    print("\n[1/5] Testing Username Availability API...")
    data = api_check_username(username="alpha_trader_99")
    assert data["available"] is True, f"Expected available: True, got {data}"
    print(f" ✓ Clean username 'alpha_trader_99': {data['message']}")

    data_at = api_check_username(username="@alpha_trader_99")
    assert data_at["available"] is True
    print(" ✓ Username with leading '@' correctly normalized and checked")

    data_short = api_check_username(username="ab")
    assert data_short["available"] is False
    print(f" ✓ Short username rejected: {data_short['message']}")

    data_invalid = api_check_username(username="bad.name!")
    assert data_invalid["available"] is False
    print(f" ✓ Invalid characters rejected: {data_invalid['message']}")

    # 2. Test Account Creation with Username, Password & Separate PIN
    print("\n[2/5] Testing Account Creation...")
    user_payload = CreateUserRequest(
        name="Arjun Sharma",
        username="arjun_stocks",
        password="SecurePassword#2026",
        pin="5432",
        email="arjun.test@example.com",
        phone="9876543210",
        pan="ABCDE1234F",
        dob="1995-05-15",
        bank_name="HDFC Bank",
        bank_account="123456789012"
    )
    create_res = api_create_user(user_payload)
    assert create_res["success"] is True
    user_data = create_res["user"]
    user_id = user_data["id"]
    assert user_data["username"] == "arjun_stocks"
    assert user_data["pin"] == "5432"
    print(f" ✓ User created successfully! ID: {user_id}, Username: @{user_data['username']}")

    # Check that username is now taken
    chk_taken = api_check_username(username="arjun_stocks")
    assert chk_taken["available"] is False
    chk_taken_upper = api_check_username(username="ARJUN_STOCKS")
    assert chk_taken_upper["available"] is False
    print(" ✓ Uniqueness confirmed: 'arjun_stocks' and 'ARJUN_STOCKS' now reported as taken")

    # Duplicate creation with same username should fail
    try:
        api_create_user(CreateUserRequest(
            name="Another Person",
            username="ARJUN_STOCKS",
            password="AnotherPassword123",
            pin="1111",
            email="another@example.com",
            phone="9998887776"
        ))
        assert False, "Should have raised HTTPException for duplicate username"
    except HTTPException as e:
        assert e.status_code == 400
        assert "already taken" in e.detail
        print(f" ✓ Duplicate username registration successfully blocked: {e.detail}")

    # 3. Test Multi-Identifier Login (Username, Email, Phone) with Password and PIN
    print("\n[3/5] Testing Multi-Credential Authentication...")

    # (a) Login via @username and Password
    l1 = api_login_user(LoginRequest(identifier="@arjun_stocks", password="SecurePassword#2026"))
    assert l1["success"] is True
    assert l1["user"]["id"] == user_id
    print(" ✓ Login via '@arjun_stocks' + Password: SUCCESS")

    # (b) Login via username (no @) and separate PIN
    l2 = api_login_user(LoginRequest(identifier="arjun_stocks", pin="5432"))
    assert l2["success"] is True
    assert l2["user"]["id"] == user_id
    print(" ✓ Login via 'arjun_stocks' + 4-digit PIN: SUCCESS")

    # (c) Login via Email + Password
    l3 = api_login_user(LoginRequest(identifier="arjun.test@example.com", password="SecurePassword#2026"))
    assert l3["success"] is True
    assert l3["user"]["id"] == user_id
    print(" ✓ Login via Email + Password: SUCCESS")

    # (d) Login via Phone + PIN
    l4 = api_login_user(LoginRequest(identifier="9876543210", pin="5432"))
    assert l4["success"] is True
    assert l4["user"]["id"] == user_id
    print(" ✓ Login via Phone + 4-digit PIN: SUCCESS")

    # (e) Login with wrong password and wrong PIN
    try:
        api_login_user(LoginRequest(identifier="arjun_stocks", password="WrongPassword"))
        assert False, "Should fail with 401"
    except HTTPException as e:
        assert e.status_code == 401
    try:
        api_login_user(LoginRequest(identifier="arjun_stocks", pin="0000"))
        assert False, "Should fail with 401"
    except HTTPException as e:
        assert e.status_code == 401
    print(" ✓ Incorrect Password & PIN correctly rejected (HTTP 401)")

    # 4. Test Profile Update (Username and Password)
    print("\n[4/5] Testing Profile Credential Update...")
    upd_res = api_update_user_profile(UpdateProfileRequest(
        id=user_id,
        name="Arjun Sharma",
        username="arjun_pro",
        password="NewUltraSecretPassword!99",
        pin="9999",
        email="arjun.new@example.com",
        phone="9876543210"
    ), request=None)
    assert upd_res["success"] is True
    assert upd_res["user"]["username"] == "arjun_pro"
    print(" ✓ Profile updated: Username changed to 'arjun_pro', PIN updated to '9999'")

    # Old username is now free again
    chk_old = api_check_username(username="arjun_stocks")
    assert chk_old["available"] is True
    print(" ✓ Old username 'arjun_stocks' released and available again")

    # Login with new username & new password
    l_new = api_login_user(LoginRequest(identifier="@arjun_pro", password="NewUltraSecretPassword!99"))
    assert l_new["success"] is True
    print(" ✓ Login with new '@arjun_pro' + new Password: SUCCESS")

    # 5. Clean up test user
    print("\n[5/5] Cleaning up test data...")
    database.delete_user(user_id)
    assert database.get_user(user_id) is None
    print(" ✓ Test user removed cleanly")

    print("\n=======================================================")
    print(" ALL USERNAME & PASSWORD TESTS PASSED (100% SUCCESS)!")
    print("=======================================================")

if __name__ == "__main__":
    test_credentials_flow()
