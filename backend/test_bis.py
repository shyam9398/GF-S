import httpx


BIS_SEARCH_URL = (
    "https://standardsadmin.bis.gov.in/"
    "review-service//searchKnowStandards"
)


payload = {
    "searchText": "helmet",
    "token": None,
    "refreshToken": None,
    "clientId": None,
    "clientSecret": None,
    "sub": None,
}


try:
    response = httpx.post(
        BIS_SEARCH_URL,
        json=payload,
        timeout=30.0,
    )

    print("\n========== BIS RESPONSE ==========\n")
    print("Status:", response.status_code)
    print("Content-Type:", response.headers.get("content-type"))
    print("\nResponse:\n")
    print(response.text)

    print("\n========== END ==========\n")

except Exception as error:
    print("\n========== BIS REQUEST FAILED ==========\n")
    print(type(error).__name__)
    print(error)