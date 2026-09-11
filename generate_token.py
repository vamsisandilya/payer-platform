import argparse

import jwt

from app.auth import ALGORITHM, SECRET_KEY

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider-id", type=int, required=True)
    parser.add_argument("--role", type=str, required=True)
    args = parser.parse_args()

    payload = {"provider_id": args.provider_id, "role": args.role}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    print(token)
