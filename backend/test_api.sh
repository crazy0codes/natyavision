#!/bin/bash

# ==============================================================================
# API Endpoint Test Script for Dance Tutorial Backend
#
# Description:
#   This script tests all major endpoints of the FastAPI application. It handles
#   signup, login, JWT token extraction, and authenticated requests.
#
# Usage:
#   1. Make sure your FastAPI server is running.
#   2. Ensure you have 'jq' installed (e.g., sudo apt-get install jq).
#   3. Add data to your database and update the placeholder IDs below.
#   4. Make the script executable: chmod +x test_endpoints.sh
#   5. Run the script: ./test_endpoints.sh
# ==============================================================================

# --- Configuration ---
# CORRECTED: Added the /api prefix to the URL
BASE_URL="http://127.0.0.1:8000/api"
# Using seconds since epoch to generate a unique email for each run
USER_EMAIL="testuser$(date +%s)@example.com"
USER_PASSWORD="strongpassword123"

# --- Colors for Output ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- Global Variable for JWT Token ---
JWT_TOKEN=""

# --- Helper function to print styled headers ---
print_header() {
    echo -e "\n${YELLOW}======================================================${NC}"
    echo -e "${YELLOW}  $1${NC}"
    echo -e "${YELLOW}======================================================${NC}"
}

# --- Check for jq dependency ---
if ! command -v jq &> /dev/null
then
    echo -e "${RED}Error: 'jq' is not installed.${NC} Please install it to continue."
    exit 1
fi

# 1. Test Signup Endpoint
print_header "1. Testing POST /auth/signup"
signup_response=$(curl -s -X POST "${BASE_URL}/auth/signup" \
-H "Content-Type: application/json" \
-d "{\"email\": \"${USER_EMAIL}\", \"password\": \"${USER_PASSWORD}\"}")

echo "Server Response:"
echo "$signup_response" | jq .
if [[ $(echo "$signup_response" | jq -r '.status') == "success" ]]; then
    echo -e "${GREEN}✔ Signup Successful.${NC}"
else
    echo -e "${RED}✖ Signup Failed.${NC}"
    # Exit if signup fails, as other tests depend on it
    exit 1
fi

# 2. Test Login Endpoint and Capture JWT Token
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
    echo -e "${RED}✖ Login Failed. Cannot proceed with authenticated tests.${NC}"
    exit 1
fi

# ==============================================================================
# ATTENTION: Update these placeholder IDs with ACTUAL _id values from your MongoDB.
# The following tests will fail if these IDs do not exist in your database.
# ==============================================================================
DANCE_ID_PLACEHOLDER="633f1b9b1e4b4e8e1e4b4e8e" # <-- CHANGE THIS
SONG_ID_PLACEHOLDER="633f1ba71e4b4e8e1e4b4e8f"   # <-- CHANGE THIS

# 3. Test Get Dance Styles Endpoint
print_header "3. Testing GET /dance/styles"
curl -s -X GET "${BASE_URL}/dance/styles" \
-H "Authorization: Bearer ${JWT_TOKEN}" | jq .

# 4. Test Get Songs in a Style Endpoint
print_header "4. Testing GET /dance/:danceId"
echo "Using Dance ID: ${DANCE_ID_PLACEHOLDER}"
curl -s -X GET "${BASE_URL}/dance/${DANCE_ID_PLACEHOLDER}" \
-H "Authorization: Bearer ${JWT_TOKEN}" | jq .

# 5. Test Get Tutorial Steps Endpoint
print_header "5. Testing GET /dance/:danceId/:songId"
echo "Using Dance ID: ${DANCE_ID_PLACEHOLDER} and Song ID: ${SONG_ID_PLACEHOLDER}"
curl -s -X GET "${BASE_URL}/dance/${DANCE_ID_PLACEHOLDER}/${SONG_ID_PLACEHOLDER}" \
-H "Authorization: Bearer ${JWT_TOKEN}" | jq .

# 6. Test Get User Status Endpoint
print_header "6. Testing GET /user/status"
curl -s -X GET "${BASE_URL}/user/status" \
-H "Authorization: Bearer ${JWT_TOKEN}" | jq .

# 7. Test Update User Song Status Endpoint
print_header "7. Testing PATCH /user/status/:songId"
echo "Updating status for Song ID: ${SONG_ID_PLACEHOLDER}"
patch_response=$(curl -s -X PATCH "${BASE_URL}/user/status/${SONG_ID_PLACEHOLDER}" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer ${JWT_TOKEN}" \
-d '{
    "status": "resume",
    "progress": 50
}')

echo "Server Response:"
echo "$patch_response" | jq .
if [[ $(echo "$patch_response" | jq -r '.status') == "success" ]]; then
    echo -e "${GREEN}✔ User status update successful.${NC}"
else
    echo -e "${RED}✖ User status update failed.${NC}"
fi

print_header "All tests completed."

