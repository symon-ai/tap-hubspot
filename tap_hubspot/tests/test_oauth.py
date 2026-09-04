import unittest

import requests_mock

from tap_hubspot import CONFIG, OAUTH_TOKEN_URL, acquire_access_token_from_refresh_token


class TestOAuthTokenRefresh(unittest.TestCase):

    def setUp(self):
        CONFIG.update({
            "redirect_uri": "https://example.com/redirect",
            "refresh_token": "old-refresh",
            "client_id": "client-id",
            "client_secret": "client-secret",
            "access_token": None,
            "token_expires": None,
        })

    def test_token_url_is_2026_03(self):
        self.assertEqual(OAUTH_TOKEN_URL, "https://api.hubapi.com/oauth/2026-03/token")
        self.assertNotIn("/oauth/v1/token", OAUTH_TOKEN_URL)

    def test_refresh_posts_to_dated_oauth_endpoint(self):
        with requests_mock.Mocker() as mocker:
            mocker.post(
                OAUTH_TOKEN_URL,
                json={
                    "access_token": "new-access",
                    "refresh_token": "new-refresh",
                    "expires_in": 1800,
                },
            )
            acquire_access_token_from_refresh_token()

        self.assertEqual(CONFIG["access_token"], "new-access")
        self.assertEqual(CONFIG["refresh_token"], "new-refresh")
        self.assertEqual(mocker.last_request.url, OAUTH_TOKEN_URL)

    def test_keeps_existing_refresh_token_when_response_omits_it(self):
        with requests_mock.Mocker() as mocker:
            mocker.post(
                OAUTH_TOKEN_URL,
                json={
                    "access_token": "new-access",
                    "expires_in": 1800,
                },
            )
            acquire_access_token_from_refresh_token()

        self.assertEqual(CONFIG["access_token"], "new-access")
        self.assertEqual(CONFIG["refresh_token"], "old-refresh")
