from clerk_backend_api import RequestState, authenticate_request, AuthenticateRequestOptions, Clerk
from fastapi import Request, HTTPException
import sqlalchemy.engine as _engine
from sqlalchemy import text
from datetime import datetime, timezone
import logging
import os

class ClerkAuthentication():
    def __init__(self, engine: _engine.Engine) -> None:
        self.logger = logging.getLogger(__name__)
        self.engine = engine
        key_path = os.getenv("CLERK_KEY_PATH")
        if not key_path:
            raise RuntimeError("CLERK_KEY_PATH not set")

        with open(key_path, "r") as f:
            self.clerkSecretKey = f.read().strip()

    def authenticate(self, request: Request):
        if 'Authorization' not in request.headers:
            return None

        try:
            request_state = authenticate_request(
                request,
                AuthenticateRequestOptions(
                    secret_key = self.clerkSecretKey
                )
            )

            return request_state

        except Exception as e:
            logging.error('User Authentication Error: %s', e)
            return None
        
    def get_or_create_user(self, requestState: RequestState | None):
        if requestState is None or requestState.is_signed_in != True:
            logging.warning('User Not Authenticated!')
            raise HTTPException(status_code=401, detail="User Not Authenticated!")

        with Clerk(bearer_auth=self.clerkSecretKey) as clerk:
            user_id = requestState.payload["sub"]  # type: ignore
            user_data = clerk.users.get(user_id=user_id)
            address_id = user_data.primary_email_address_id
            email = next(
                (email for email in user_data.email_addresses if email.id == address_id),
                None
            )
            firstName = user_data.first_name
            lastName = user_data.last_name
            createdAt = datetime.fromtimestamp(user_data.created_at / 1000, tz=timezone.utc)

        with self.engine.begin() as connection:
            query = text("""
                INSERT INTO "Users" (clerk_user_id, email, first_name, last_name, role, created_at)
                VALUES (:userId, :email, :firstName, :lastName, 'user', :createdAt)
                ON CONFLICT (clerk_user_id)
                DO UPDATE SET
                email = EXCLUDED.email,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name;
            """)
            connection.execute(
                query,
                {
                    'userId': user_id,
                    'email': email.email_address,  # type: ignore
                    'firstName': firstName,
                    'lastName': lastName,
                    'createdAt': createdAt
                }
            )

            

            

