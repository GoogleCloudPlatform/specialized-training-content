import httpx

signed_url="""https://storage.googleapis.com/jwd-atf-int-cymbal-meet-interventions/test.pdf?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=gcs-mcp-sa%40jwd-atf-int.iam.gserviceaccount.com%2F20260303%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20260303T210803Z&X-Goog-Expires=900&X-Goog-SignedHeaders=content-type%3Bhost&X-Goog-Signature=388bee8f22c6dbed0c10859d7696b20c192fb9da4bdd77d6a1a7e5dfb370575dfad5e39a562a613653ce61140b501df543bc9dc75543406ae386456847e0c41e2d783fba1a968d9059c2edf5838498fe41b4154d43473d62f87851292663e5ec2fade8a2d0d773d8696e16d19f0d54da677808580b828359b5404ac43312606c2fb28c88ddd91f25c3fa909039c2f5ec4e4d697aa6e984e90af5ef2a8bdcc180caff5dda06a1393ad3860614e28e3b4790d7b73a163324225e6129670176ad1e9c8345dafd276d0a4641ce4ce05671962217c7eb15184b82bbe5f7d1b963864dff3be95bd8f75ea967b49f82953eb630c2548c21526fcb4c4041021169a846b1"""

with open("admin_guide_user_onboarding.pdf", "rb") as f:
    data = f.read()

response = httpx.put(
    signed_url.strip(),
    content=data,
    headers={"Content-Type": "application/pdf"},
)
response.raise_for_status()  # 200 on success