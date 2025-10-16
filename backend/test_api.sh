#!/bin/bash

# ==============================================================================
# 🌟 API Endpoint Test Script for Dance Tutorial Backend
# ==============================================================================

# --- Configuration ---
BASE_URL="http://127.0.0.1:8000/api"
USER_EMAIL="testuser$(date +%s)@example.com"
USER_PASSWORD="strongpassword123"

# --- Colors ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- Header Printer ---
print_header() {
    echo -e "\n${YELLOW}======================================================${NC}"
    echo -e "${YELLOW}  $1${NC}"
    echo -e "${YELLOW}======================================================${NC}"
}

# --- jq Check ---
if ! command -v jq &> /dev/null
then
    echo -e "${RED}❌ Error: 'jq' is not installed.${NC}"
    echo "Install it via: sudo apt install jq"
    exit 1
fi

# ==============================================================================
# 1️⃣  SIGNUP
# ==============================================================================
print_header "1. Testing POST /auth/signup"

signup_response=$(curl -s -X POST "${BASE_URL}/auth/signup" \
-H "Content-Type: application/json" \
-d "{\"email\": \"${USER_EMAIL}\", \"password\": \"${USER_PASSWORD}\"}")

echo "Server Response:"
echo "$signup_response" | jq .

if [[ $(echo "$signup_response" | jq -r '.status') == "success" ]]; then
    echo -e "${GREEN}✔ Signup Successful.${NC}"
else
    echo -e "${YELLOW}⚠ Signup may already exist or failed. Proceeding to login with test credentials.${NC}"
fi

# ==============================================================================
# 2️⃣  LOGIN
# ==============================================================================
print_header "2. Testing POST /auth/login"

login_response=$(curl -s -X POST "${BASE_URL}/auth/login" \
-H "Content-Type: application/json" \
-d "{\"email\": \"${USER_EMAIL}\", \"password\": \"${USER_PASSWORD}\"}")

echo "Server Response:"
echo "$login_response" | jq .

JWT_TOKEN=$(echo "$login_response" | jq -r '.jwt_token')

if [[ "$JWT_TOKEN" != "null" && -n "$JWT_TOKEN" ]]; then
    echo -e "${GREEN}✔ Login Successful. JWT Token captured.${NC}"
else
    echo -e "${RED}✖ Login Failed. Cannot continue.${NC}"
    exit 1
fi

# ==============================================================================
# 3️⃣  GET DANCE STYLES (Public Endpoint)
# ==============================================================================
print_header "3. Testing GET /dance/styles"

# Auth header is included but not strictly needed for this specific endpoint
dance_response=$(curl -s -X GET "${BASE_URL}/dance/styles" \
-H "Authorization: Bearer ${JWT_TOKEN}")

echo "$dance_response" | jq .

first_dance_id=$(echo "$dance_response" | jq -r '.[0]._id')

if [[ "$first_dance_id" == "null" || -z "$first_dance_id" ]]; then
    echo -e "${RED}✖ No dance styles found in DB. Please seed data first.${NC}"
    exit 1
fi

echo -e "${GREEN}✔ Retrieved Dance ID: ${first_dance_id}${NC}"

# ==============================================================================
# 4️⃣  GET SONGS IN STYLE (Protected Endpoint)
# ==============================================================================
print_header "4. Testing GET /dance/{dance_id}"

songs_response=$(curl -s -X GET "${BASE_URL}/dance/${first_dance_id}" \
-H "Authorization: Bearer ${JWT_TOKEN}")

echo "$songs_response" | jq .

first_song_id=$(echo "$songs_response" | jq -r '.[0]._id')

if [[ "$first_song_id" == "null" || -z "$first_song_id" ]]; then
    echo -e "${RED}✖ No songs found for this dance style.${NC}"
    exit 1
fi

echo -e "${GREEN}✔ Retrieved Song ID: ${first_song_id}${NC}"

# ==============================================================================
# 5️⃣  GET TUTORIAL STEPS (Protected Endpoint)
# ==============================================================================
print_header "5. Testing GET /dance/{dance_id}/{song_id}"

steps_response=$(curl -s -X GET "${BASE_URL}/dance/${first_dance_id}/${first_song_id}" \
-H "Authorization: Bearer ${JWT_TOKEN}")

echo "$steps_response" | jq .
echo -e "${GREEN}✔ Tutorial steps fetched successfully.${NC}"

# ==============================================================================
# 6️⃣  GET USER SONG STATUS (Protected Endpoint)
# ==============================================================================
print_header "6. Testing GET /user/status (Initial status)"

status_response=$(curl -s -X GET "${BASE_URL}/user/status" \
-H "Authorization: Bearer ${JWT_TOKEN}")

echo "$status_response" | jq .
echo -e "${GREEN}✔ User song statuses retrieved.${NC}"

# ==============================================================================
# 7️⃣  PATCH USER SONG STATUS (Protected Endpoint)
# ==============================================================================
print_header "7. Testing PATCH /user/status/{song_id} (Update progress)"

patch_response=$(curl -s -X PATCH "${BASE_URL}/user/status/${first_song_id}" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer ${JWT_TOKEN}" \
-d '{
    "status": "resume",
    "progress": 60
}')

echo "$patch_response" | jq .

if [[ $(echo "$patch_response" | jq -r '.status') == "success" ]]; then
    echo -e "${GREEN}✔ User song status updated successfully.${NC}"
else
    echo -e "${RED}✖ Failed to update song status.${NC}"
    exit 1
fi

# ==============================================================================
# 8️⃣  GET USER SONG STATUS (Verify Update)
# ==============================================================================
print_header "8. Testing GET /user/status (Verify updated status)"

status_response_verify=$(curl -s -X GET "${BASE_URL}/user/status" \
-H "Authorization: Bearer ${JWT_TOKEN}")

echo "$status_response_verify" | jq .

if [[ $(echo "$status_response_verify" | jq -r '.[0].progress') == 60 ]]; then
    echo -e "${GREEN}✔ Verification Successful: Progress is 60%.${NC}"
else
    echo -e "${RED}✖ Verification Failed: Progress did not update.${NC}"
    exit 1
fi

print_header "✅ All tests completed successfully!"