"""Unit tests for HubSpot OAuth token refreshes."""
import unittest
from unittest.mock import Mock, patch

from tap_hubspot import acquire_access_token_from_refresh_token
from tap_hubspot import BASE_URL
from tap_hubspot import CONFIG


class TestOAuthRefresh(unittest.TestCase):
    def test_refresh_posts_to_supported_token_endpoint(self):
        config = {
            "redirect_uri": "https://example.com/oauth/callback",
            "refresh_token": "refresh-token",
            "client_id": "client-id",
            "client_secret": "client-secret",
        }
        response = Mock(status_code=200)
        response.json.return_value = {
            "access_token": "access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 3600,
        }

        with patch.dict(CONFIG, config), \
                patch("tap_hubspot.requests.post", return_value=response) as post:
            acquire_access_token_from_refresh_token()

        post.assert_called_once_with(
            BASE_URL + "/oauth/2026-03/token",
            data={
                "grant_type": "refresh_token",
                **config,
            },
        )
