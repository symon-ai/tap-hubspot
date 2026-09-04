import unittest
from unittest.mock import Mock, patch, ANY

from tap_hubspot import (
    ENDPOINTS,
    normalize_deal_pipeline,
    sync_deal_pipelines,
)


class TestNormalizeDealPipeline(unittest.TestCase):

    def test_maps_2026_03_payload_to_legacy_schema(self):
        row = {
            "id": "default",
            "label": "Sales Pipeline",
            "displayOrder": 0,
            "archived": False,
            "stages": [
                {
                    "id": "appointmentscheduled",
                    "label": "Appointment Scheduled",
                    "displayOrder": 0,
                    "archived": False,
                    "metadata": {"isClosed": "false", "probability": "0.2"},
                },
                {
                    "id": "closedwon",
                    "label": "Closed Won",
                    "displayOrder": 1,
                    "archived": False,
                    "metadata": {"isClosed": "true", "probability": "1.0"},
                },
                {
                    "id": "closedlost",
                    "label": "Closed Lost",
                    "displayOrder": 2,
                    "archived": True,
                    "metadata": {"isClosed": "true", "probability": "0.0"},
                },
            ],
        }

        record = normalize_deal_pipeline(row)

        self.assertEqual(record["pipelineId"], "default")
        self.assertEqual(record["label"], "Sales Pipeline")
        self.assertTrue(record["active"])
        self.assertEqual(record["stages"][0]["stageId"], "appointmentscheduled")
        self.assertEqual(record["stages"][0]["probability"], 0.2)
        self.assertFalse(record["stages"][0]["closedWon"])
        self.assertTrue(record["stages"][0]["active"])
        self.assertTrue(record["stages"][1]["closedWon"])
        self.assertEqual(record["stages"][1]["probability"], 1.0)
        self.assertFalse(record["stages"][2]["active"])
        self.assertFalse(record["stages"][2]["closedWon"])

    def test_open_stage_with_full_probability_is_not_closed_won(self):
        row = {
            "id": "custom",
            "label": "Custom Pipeline",
            "displayOrder": 0,
            "archived": False,
            "stages": [
                {
                    "id": "negotiation",
                    "label": "Final Negotiation",
                    "displayOrder": 0,
                    "archived": False,
                    "metadata": {"isClosed": "false", "probability": "1.0"},
                },
            ],
        }

        record = normalize_deal_pipeline(row)

        self.assertEqual(record["stages"][0]["probability"], 1.0)
        self.assertFalse(record["stages"][0]["closedWon"])

    def test_passthrough_legacy_v1_payload(self):
        row = {
            "pipelineId": "custom",
            "label": "Custom",
            "displayOrder": 1,
            "active": True,
            "staticDefault": False,
            "stages": [
                {
                    "stageId": "s1",
                    "label": "Stage 1",
                    "probability": 0.5,
                    "active": True,
                    "displayOrder": 0,
                    "closedWon": False,
                }
            ],
        }

        record = normalize_deal_pipeline(row)

        self.assertEqual(record["pipelineId"], "custom")
        self.assertTrue(record["active"])
        self.assertEqual(record["staticDefault"], False)
        self.assertEqual(record["stages"][0]["stageId"], "s1")
        self.assertEqual(record["stages"][0]["probability"], 0.5)
        self.assertFalse(record["stages"][0]["closedWon"])


class TestSyncDealPipelines(unittest.TestCase):

    def test_endpoint_is_pipelines_2026_03(self):
        self.assertEqual(ENDPOINTS["deal_pipelines"], "/crm/pipelines/2026-03/deals")
        self.assertNotIn("/deals/v1/pipelines", ENDPOINTS.values())
        self.assertNotIn("/crm-pipelines/v1/pipelines/deals", ENDPOINTS.values())

    @patch("tap_hubspot.Context.get_catalog_from_id", return_value={"metadata": [], "stream_alias": None})
    @patch("singer.metadata.to_map", return_value={})
    @patch("singer.write_schema")
    @patch("singer.write_record")
    @patch("singer.write_state")
    @patch("tap_hubspot.request")
    def test_sync_reads_results_and_archived(
        self,
        mocked_request,
        mocked_write_state,
        mocked_write_record,
        mocked_write_schema,
        mocked_metadata_map,
        mocked_catalog_from_id,
    ):
        active = Mock()
        active.json.return_value = {
            "results": [
                {
                    "id": "p1",
                    "label": "Pipeline",
                    "displayOrder": 0,
                    "archived": False,
                    "stages": [
                        {
                            "id": "s1",
                            "label": "Stage",
                            "displayOrder": 0,
                            "archived": False,
                            "metadata": {"probability": "0.5"},
                        }
                    ],
                }
            ]
        }
        archived = Mock()
        archived.json.return_value = {
            "results": [
                {
                    "id": "p2",
                    "label": "Old Pipeline",
                    "displayOrder": 1,
                    "archived": True,
                    "stages": [],
                }
            ]
        }
        mocked_request.side_effect = [active, archived]

        sync_deal_pipelines({}, mocked_catalog_from_id)

        self.assertEqual(mocked_request.call_count, 2)
        mocked_request.assert_any_call(ANY)
        mocked_request.assert_any_call(ANY, params={"archived": "true"})
        self.assertEqual(mocked_write_record.call_count, 2)

        first_record = mocked_write_record.call_args_list[0][0][1]
        self.assertEqual(first_record["pipelineId"], "p1")
        self.assertTrue(first_record["active"])
        self.assertEqual(first_record["stages"][0]["stageId"], "s1")
        self.assertEqual(first_record["stages"][0]["probability"], 0.5)

        second_record = mocked_write_record.call_args_list[1][0][1]
        self.assertEqual(second_record["pipelineId"], "p2")
        self.assertFalse(second_record["active"])
