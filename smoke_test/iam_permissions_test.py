#!/usr/bin/env python3
"""Read-only IAM permission diagnostic. Uses Application Default Credentials (ADC). Never prints, stores, or exports access tokens. Always exits with status code 0."""
import json
import sys
import urllib.error
import urllib.request
PROJECT_ID = "bazel-untrusted"
SERVICE_ACCOUNT = "buildkite-testing@bazel-untrusted.iam.gserviceaccount.com"
PROJECT_PERMISSIONS = ["storage.objects.get","storage.objects.create","storage.objects.delete","storage.buckets.get","secretmanager.versions.access"]
SERVICE_ACCOUNT_PERMISSIONS = ["iam.serviceAccounts.actAs","iam.serviceAccounts.getAccessToken"]
BUCKETS = ["bazel-untrusted-build-cache","bazel-untrusted-buildkite-artifacts","bazel-testing-builds"]
SCOPE = "https://www.googleapis.com/auth/cloud-platform"
class HttpResponse:
    def __init__(self, status, data, headers):
        self.status = status
        self.data = data
        self.headers = headers
class StdlibTransport:
    def __call__(self, url, method="GET", body=None, headers=None, timeout=None, **kwargs):
        request = urllib.request.Request(url=url, data=body, headers=headers or {}, method=method)
        try:
            with urllib.request.urlopen(request, timeout=timeout or 20) as response:
                return HttpResponse(response.status, response.read(), response.headers)
        except urllib.error.HTTPError as error:
            return HttpResponse(error.code, error.read(), error.headers)
def authenticated_request(credentials, transport, url, method="GET", body=None):
    headers = {}
    if body is not None:
        headers["Content-Type"] = "application/json"
    credentials.before_request(transport, method, url, headers)
    return transport(url, method=method, body=body, headers=headers, timeout=20)
def test_permissions(credentials, transport, resource_url, permissions, label):
    payload = json.dumps({"permissions": permissions}).encode("utf-8")
    try:
        response = authenticated_request(credentials, transport, resource_url, method="POST", body=payload)
        print("{}_HTTP_STATUS={}".format(label, response.status))
        if response.status != 200:
            print("{}_RESULT=UNAVAILABLE".format(label))
            return
        result = json.loads(response.data.decode("utf-8"))
        granted = set(result.get("permissions", []))
        for permission in permissions:
            status = "GRANTED" if permission in granted else "DENIED"
            print("{} {} {}".format(label, status, permission))
    except Exception:
        print("{}_RESULT=UNAVAILABLE".format(label))
def check_bucket(credentials, transport, bucket):
    url = "https://storage.googleapis.com/storage/v1/b/" + bucket + "?fields=name"
    try:
        response = authenticated_request(credentials, transport, url)
        accessible = response.status == 200
        print("BUCKET={} ACCESSIBLE={} HTTP_STATUS={}".format(bucket, str(accessible).lower(), response.status))
    except Exception:
        print("BUCKET={} ACCESSIBLE=unknown HTTP_STATUS=unavailable".format(bucket))
def main():
    try:
        import google.auth
    except ImportError:
        print("DIAGNOSTIC=UNAVAILABLE REASON=google.auth_not_installed")
        return
    try:
        credentials, _ = google.auth.default(scopes=[SCOPE])
        transport = StdlibTransport()
    except Exception:
        print("DIAGNOSTIC=UNAVAILABLE REASON=credentials_unavailable")
        return
    project_url = "https://cloudresourcemanager.googleapis.com/v1/projects/" + PROJECT_ID + ":testIamPermissions"
    service_account_url = "https://iam.googleapis.com/v1/projects/" + PROJECT_ID + "/serviceAccounts/" + SERVICE_ACCOUNT.replace("@", "%40") + ":testIamPermissions"
    test_permissions(credentials, transport, project_url, PROJECT_PERMISSIONS, "PROJECT")
    test_permissions(credentials, transport, service_account_url, SERVICE_ACCOUNT_PERMISSIONS, "SERVICE_ACCOUNT")
    for bucket in BUCKETS:
        check_bucket(credentials, transport, bucket)
if __name__ == "__main__":
    try:
        main()
    except BaseException:
        pass
    sys.exit(0)