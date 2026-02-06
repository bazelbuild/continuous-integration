import argparse
import base64
import os
import subprocess
import sys
from typing import List, Optional


os.environ["BUILDKITE_ORGANIZATION_SLUG"] = "bazel"
import bazelci


def encrypt(value: str, kms_key: str) -> bytes:
    return subprocess.check_output(
        [
            "gcloud",
            "kms",
            "encrypt",
            "--project",
            "bazel-untrusted",
            "--location",
            "global",
            "--keyring",
            "buildkite",
            "--key",
            kms_key,
            "--ciphertext-file",
            "-",
            "--plaintext-file",
            "-",
        ],
        input=value.encode("utf-8"),
        env=os.environ,
    )


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Bazel Continuous Integration Encryption Tool")
    parser.add_argument("--key_name", type=str)
    parser.add_argument("--value", type=str)

    args = parser.parse_args(argv)

    if not args.key_name or not args.value:
        print("Both --key_name and --value must be specified", file=sys.stderr)
        return 1

    print("Original: %s" % args.value)

    enc_bytes = encrypt(args.value, args.key_name)
    enc_str = base64.b64encode(enc_bytes).decode("utf-8").strip()
    print("Encoded:  %s" % enc_str)

    dec = bazelci.decrypt_token(enc_str, args.key_name)
    print("Decoded:  %s" % dec)
    return 0


if __name__ == "__main__":
    sys.exit(main())
