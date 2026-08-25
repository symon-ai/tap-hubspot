# tap-hubspot

This is a [Singer](https://singer.io) tap that produces JSON-formatted data following the [Singer spec](https://github.com/singer-io/getting-started/blob/master/SPEC.md).

This tap:
- Pulls raw data from HubSpot's [REST API](http://developers.hubspot.com/docs/overview)
- Extracts the following resources from HubSpot
  - [Campaigns](http://developers.hubspot.com/docs/methods/email/get_campaign_data)
  - [Companies](http://developers.hubspot.com/docs/methods/companies/get_company)
  - [Contacts](https://developers.hubspot.com/docs/methods/contacts/get_contacts)
  - [Contact Lists](http://developers.hubspot.com/docs/methods/lists/get_lists)
  - [Deals](http://developers.hubspot.com/docs/methods/deals/get_deals_modified)
  - [Deal Pipelines](https://developers.hubspot.com/docs/api-reference/latest/crm/pipelines/guide)
  - [Email Events](http://developers.hubspot.com/docs/methods/email/get_events)
  - [Engagements](https://developers.hubspot.com/docs/methods/engagements/get-all-engagements)
  - [Forms](http://developers.hubspot.com/docs/methods/forms/v2/get_forms)
  - [Keywords](http://developers.hubspot.com/docs/methods/keywords/get_keywords)
  - [Owners](http://developers.hubspot.com/docs/methods/owners/get_owners)
  - [Subscription Changes](http://developers.hubspot.com/docs/methods/email/get_subscriptions_timeline)
  - [Workflows](http://developers.hubspot.com/docs/methods/workflows/v3/get_workflows)
- Outputs the schema for each resource
- Incrementally pulls data based on the input state

## Configuration

This tap requires a `config.json` which specifies details regarding [OAuth 2.0](https://developers.hubspot.com/docs/methods/oauth2/oauth2-overview) authentication, a cutoff date for syncing historical data, and an optional flag which controls collection of anonymous usage metrics. See [config.sample.json](config.sample.json) for an example. You may specify an API key instead of OAuth parameters for development purposes, as detailed below.

To run `tap-hubspot` with the configuration file, use this command:

```bash
› tap-hubspot -c my-config.json
```

### Install and Run

Ensure poetry is installed on your machine. 

- This command will return the installed version of poetry if it is installed.
```
poetry --version
```

- If not, install poetry using the following commands (from https://python-poetry.org/docs/#installation):
```
curl -sSL https://install.python-poetry.org | python3 -
PATH=~/.local/bin:$PATH
```

Within the `tap-hubspot` directory, install dependencies:
```
poetry install
```

Then run the tap:
```
poetry run tap-hubspot <options>
```

## Package manager

We only use poetry to manage our packages. Pipfile is there because our code scan doesn't support poetry.lock. So we do the following hack to generate Pipfile and Pipfile.lock based on our poetry.lock:
# 1. Export all dependencies from poetry.lock to requirements.txt
```
poetry export -f requirements.txt --output requirements.txt --without-hashes
```
# 1b. (Optional) Make sure pipenv has the right python version
Check:
```
pipenv --support
```
Install:
```
python -m pip install --user pipenv
```

# 2. Generate Pipfile and Pipfile.lock from requirements.txt (make sure you pass in right version of python)
```
pipenv install --python 3.13 -r requirements.txt
```

Check that the required python version in the Pipfile matches your expected python version. For some reason even if requirements.txt specify the right python version pipenv can still default to a different version based on the some stale versioning in the venv. In which case, do the following:

# 1. Delete the Pipfile and lock, and deactivate your venv

# 2. Delete the venv with `pipenv --rm`

# 3. Re-run the pipenv install command

## API Key Authentication (for development)

As an alternative to OAuth 2.0 authentication during development, you may specify an API key (`HAPIKEY`) to authenticate with the HubSpot API. This should be used only for low-volume development work, as the [HubSpot API Usage Guidelines](https://developers.hubspot.com/apps/api_guidelines) specify that integrations should use OAuth for authentication.

To use an API key, include a `hapikey` configuration variable in your `config.json` and set it to the value of your HubSpot API key. Any OAuth authentication parameters in your `config.json` **will be ignored** if this key is present!

---

Copyright &copy; 2017 Stitch
