import copy
import os
import unittest
from http.cookies import SimpleCookie
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.responses import Response
from starlette.requests import Request

from src import app as app_module


def make_request(cookie_value=None):
    headers = []
    if cookie_value is not None:
        headers.append(
            (b"cookie", f"{app_module.TEACHER_SESSION_COOKIE}={cookie_value}".encode())
        )
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": headers,
        "server": ("testserver", 80),
        "client": ("testclient", 12345),
    }
    return Request(scope)


class TeacherAuthTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(
            os.environ,
            {
                "TEACHER_USERNAME": "teacher",
                "TEACHER_PASSWORD": "safe-test-password",
                "SESSION_SECRET": "test-session-secret-with-more-than-32-characters",
            },
        )
        self.environment.start()
        self.original_activities = copy.deepcopy(app_module.activities)

    def tearDown(self):
        app_module.activities.clear()
        app_module.activities.update(self.original_activities)
        self.environment.stop()

    def test_write_routes_reject_requests_without_teacher_session(self):
        request = make_request()

        with self.assertRaises(HTTPException) as signup_error:
            app_module.signup_for_activity("Chess Club", "student@example.edu", request)
        with self.assertRaises(HTTPException) as unregister_error:
            app_module.unregister_from_activity(
                "Chess Club", "michael@mergington.edu", request
            )

        self.assertEqual(signup_error.exception.status_code, 401)
        self.assertEqual(unregister_error.exception.status_code, 401)

    def test_valid_login_allows_teacher_to_manage_enrollment(self):
        response = Response()
        app_module.login(
            app_module.TeacherCredentials(
                username="teacher", password="safe-test-password"
            ),
            make_request(),
            response,
        )
        cookie = SimpleCookie()
        cookie.load(response.headers["set-cookie"])
        session_value = cookie[app_module.TEACHER_SESSION_COOKIE].value
        request = make_request(session_value)

        signup_result = app_module.signup_for_activity(
            "Chess Club", "student@example.edu", request
        )
        unregister_result = app_module.unregister_from_activity(
            "Chess Club", "michael@mergington.edu", request
        )

        self.assertEqual(signup_result["message"], "Signed up student@example.edu for Chess Club")
        self.assertEqual(
            unregister_result["message"],
            "Unregistered michael@mergington.edu from Chess Club",
        )

    def test_invalid_credentials_do_not_create_a_session(self):
        with self.assertRaises(HTTPException) as error:
            app_module.login(
                app_module.TeacherCredentials(
                    username="teacher", password="incorrect-password"
                ),
                make_request(),
                Response(),
            )

        self.assertEqual(error.exception.status_code, 401)

    def test_unconfigured_teacher_auth_fails_explicitly(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(HTTPException) as error:
                app_module.get_auth_status(make_request())

        self.assertEqual(error.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
