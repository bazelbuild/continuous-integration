import argparse
import base64
import os
import subprocess
import sys


os.environ["BUILDKITE_ORGANIZATION_SLUG"] = "bazel"


def encrypt(value, kms_key):
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


def decrypt(encrypted_token, kms_key):
    return (
        subprocess.check_output(
            [
                "gcloud",
                "kms",
                "decrypt",
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
            input=base64.b64decode(encrypted_token),
            env=os.environ,
        )
        .decode("utf-8")
        .strip()
    )


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Bazel Continuous Integration Encryption Tool")
    parser.add_argument("--key_name", type=str)
    parser.add_argument("--value", type=str)

    args = parser.parse_args(argv)

    if not args.key_name or not args.value:
        print("Both --key_name and --value must be specified", file=sys.stderr)
        exit(1)

    print("Original: %s" % args.value)

    enc = encrypt(args.value, args.key_name)
    enc = base64.b64encode(enc).decode("utf-8").strip()
    print("Encoded:  %s" % enc)

    dec = decrypt(enc, args.key_name)
    print("Decoded:  %s" % dec)


if __name__ == "__main__":
    sys.exit(main())
