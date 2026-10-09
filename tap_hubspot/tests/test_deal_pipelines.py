import datetime
import unittest
from unittest.mock import Mock, patch

from tap_hubspot import (
    BASE_URL,
    CONFIG,
    acquire_access_token_from_refresh_token,
    map_deal_pipeline,
    sync_deal_pipelines,
)


PIPELINE_RESPONSE = {
    'id': 'default',
    'label': 'Sales Pipeline',
    'displayOrder': 0,
    'archived': False,
    'createdAt': '2026-03-01T00:00:00Z',
    'updatedAt': '2026-03-02T00:00:00Z',
    'stages': [
        {
            'id': 'closedwon',
            'label': 'Closed Won',
            'displayOrder': 5,
            'archived': False,
            'metadata': {'probability': '1.0'},
            'createdAt': '2026-03-01T00:00:00Z',
            'updatedAt': '2026-03-02T00:00:00Z',
            'writePermissions': 'CRM_PERMISSIONS_ENFORCEMENT',
        },
        {
            'id': 'closedlost',
            'label': 'Closed Lost',
            'displayOrder': 6,
            'archived': True,
            'metadata': {'probability': '0.0'},
            'createdAt': '2026-03-01T00:00:00Z',
            'updatedAt': '2026-03-02T00:00:00Z',
            'writePermissions': 'CRM_PERMISSIONS_ENFORCEMENT',
        },
    ],
}


class TestDealPipelines(unittest.TestCase):

    def test_maps_versioned_pipeline_response_to_existing_stream_schema(self):
        self.assertEqual(
            {
                'pipelineId': 'default',
                'label': 'Sales Pipeline',
                'active': True,
                'displayOrder': 0,
                'staticDefault': None,
                'stages': [
                    {
                        'stageId': 'closedwon',
                        'label': 'Closed Won',
                        'probability': 1.0,
                        'active': True,
                        'displayOrder': 5,
                        'closedWon': True,
                    },
                    {
                        'stageId': 'closedlost',
                        'label': 'Closed Lost',
                        'probability': 0.0,
                        'active': False,
                        'displayOrder': 6,
                        'closedWon': False,
                    },
                ],
            },
            map_deal_pipeline(PIPELINE_RESPONSE),
        )

    @patch('tap_hubspot.singer.write_state')
    @patch('tap_hubspot.singer.write_record')
    @patch('tap_hubspot.singer.write_schema')
    @patch('tap_hubspot.request')
    def test_sync_uses_versioned_endpoint_and_results_envelope(
            self, mocked_request, mocked_write_schema, mocked_write_record,
            mocked_write_state):
        response = Mock()
        response.json.return_value = {'results': [PIPELINE_RESPONSE]}
        mocked_request.return_value = response
        context = Mock()
        context.get_catalog_from_id.return_value = {
            'metadata': [],
            'stream_alias': None,
        }

        sync_deal_pipelines({}, context)

        mocked_request.assert_called_once_with(
            BASE_URL + '/crm/pipelines/2026-03/deals')
        record = mocked_write_record.call_args.args[1]
        self.assertEqual('default', record['pipelineId'])
        self.assertEqual('closedwon', record['stages'][0]['stageId'])
        mocked_write_state.assert_called_once_with({})
        self.assertEqual(1, mocked_write_record.call_count)
        self.assertEqual(1, mocked_write_schema.call_count)

    @patch('tap_hubspot.requests.post')
    def test_refreshes_access_token_through_versioned_oauth_endpoint(
            self, mocked_post):
        response = Mock(status_code=200)
        response.json.return_value = {
            'access_token': 'new-access-token',
            'refresh_token': 'new-refresh-token',
            'expires_in': 1800,
        }
        mocked_post.return_value = response
        config = {
            'redirect_uri': 'https://example.com/callback',
            'refresh_token': 'refresh-token',
            'client_id': 'client-id',
            'client_secret': 'client-secret',
        }

        with patch.dict(CONFIG, config, clear=False):
            acquire_access_token_from_refresh_token()
            self.assertEqual('new-access-token', CONFIG['access_token'])
            self.assertEqual('new-refresh-token', CONFIG['refresh_token'])
            self.assertGreater(
                CONFIG['token_expires'], datetime.datetime.utcnow())

        mocked_post.assert_called_once_with(
            BASE_URL + '/oauth/2026-03/token',
            data={
                'grant_type': 'refresh_token',
                'redirect_uri': 'https://example.com/callback',
                'refresh_token': 'refresh-token',
                'client_id': 'client-id',
                'client_secret': 'client-secret',
            },
        )


if __name__ == '__main__':
    unittest.main()
