# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New `SECRET_KEY` optional environment variable ([#671](https://github.com/Substra/substra-backend/pull/671))
- `/api-token-auth/` and the associated tokens can now be disabled through the `EXPIRY_TOKEN_ENABLED` environment variable and `server.allowImplicitLogin` chart value ([#698](https://github.com/Substra/substra-backend/pull/698))
- Tokens issued by `/api-token-auth/` can now be deleted like other API tokens, through a `DELETE` request on the `/active-api-tokens` endpoint ([#698](https://github.com/Substra/substra-backend/pull/698))
- Field `asset_type` on `AssetFailureReport` (based on protobuf enum `orchestrator.FailedAssetKind`) ([#727](https://github.com/Substra/substra-backend/pull/727))
- Celery task `FailableTask` that contains the logic to store the failure report, that can be re-used in different assets. ([#727](https://github.com/Substra/substra-backend/pull/727))
- Add `FunctionStatus` enum ([#263](https://github.com/Substra/orchestrator/pull/263))
- BREAKING: Add `status` on `api.Function` (type `FunctionStatus`) ([#714](https://github.com/Substra/substra-backend/pull/714))


### Changed

- Increase the number of tasks displayable in frontend workflow [#697](https://github.com/Substra/substra-backend/pull/697)
- BREAKING: Change the format of many API responses from `{"message":...}` to `{"detail":...}` ([#705](https://github.com/Substra/substra-backend/pull/705))
- `ComputeTaskFailureReport` renamed in `AssetFailureReport` ([#727](https://github.com/Substra/substra-backend/pull/727))
- Field `AssetFailureReport.compute_task_key` renamed to `asset_key` ([#727](https://github.com/Substra/substra-backend/pull/727))

### Removed

- BREAKING: `SECRET_KEY_PATH` and `SECRET_KEY_LOAD_AND_STORE` environment variables ([#671](https://github.com/Substra/substra-backend/pull/671))
- Removed logic for storing `SECRET_KEY` at startup, in order to increase stability; it should be done at a higher level, i.e. the chart ([#671](https://github.com/Substra/substra-backend/pull/671))

## Fixed
- `/api-token-auth/` sometimes handing out tokens that are about to expire ([#698](https://github.com/Substra/substra-backend/pull/698))

## [0.40.0](https://github.com/Substra/substra-backend/releases/tag/0.40.0) 2023-07-25

### Fixed

- Remove pagination on `get_performances` to remove limitation on 1000 first points ([#690](https://github.com/Substra/substra-backend/pull/690))
- - Update or create the step profiling, instead of raising an error if already exists ([#691](https://github.com/Substra/substra-backend/pull/691))

### Added

- New UserAwaitingApproval (base user with no channel) ([#680](https://github.com/Substra/substra-backend/pull/680))

## [0.39.0](https://github.com/Substra/substra-backend/releases/tag/0.39.0) 2023-06-27

### Added

- New `SECRET_KEY_PATH` and `SECRET_KEY_LOAD_AND_STORE` environment variables ([#668](https://github.com/Substra/substra-backend/pull/668))

## [0.38.0](https://github.com/Substra/substra-backend/releases/tag/0.38.0) 2023-06-12

### Added

- BREAKING: Support for multiple API tokens with expanded functionality ([#639](https://github.com/Substra/substra-backend/pull/639))

### Changed

- BREAKING: database backend now defaults to `backend_{ORG_NAME}` rather than `substra` in all cases (this was already the production setting)
- `ORG_NAME` now defaults to `default` rather than being mandatory (this is always overridden in the chart)

### Removed

- references to `substra` cli commands in `localdev.md` ([#667](https://github.com/Substra/substra-backend/pull/667))

## [0.37.0](https://github.com/Substra/substra-backend/releases/tag/0.37.0) 2023-05-11

### Changed

- Performance is now unique regarding a ComputeTaskOutput and a Metric ([#634](https://github.com/Substra/substra-backend/pull/634))
- BREAKING: `TaskProfiling` do not use `create_or_update` but retry with `PUT` if error is `409` ([#636](https://github.com/Substra/substra-backend/pull/636))

### Fixed

- Raise a serializable Exception so that CeleryRetryError won't crash ([#641](https://github.com/Substra/substra-backend/pull/641))
- Do not retry on non-timeout build errors ([#641](https://github.com/Substra/substra-backend/pull/641))

### Removed

- Metric from Performance ([#650](https://github.com/Substra/substra-backend/pull/650))

## [0.36.1](https://github.com/Substra/substra-backend/releases/tag/0.36.1) 2023-04-21

### Fixed

- Catch all exception in `get_pod_logs` and always return a string containing either logs, or the reason we couldn't get logs ([#637](https://github.com/Substra/substra-backend/pull/637))
- `redis` dependency for `metric-exporter` ([#640](https://github.com/Substra/substra-backend/pull/640))
- Skaffold `monitoring` profile ([#640](https://github.com/Substra/substra-backend/pull/640))

### Changed

- Increase the `max_attempts` in `watch_log` to allow kaniko pods to take longer to start ([#637](https://github.com/Substra/substra-backend/pull/637))

### Added

- Add function name to workflow view & ordering on functionName in cpTasks list (#635)

## [0.36.0](https://github.com/Substra/substra-backend/releases/tag/0.36.0) 2023-03-31

### Added

- Add filters to performances export (#590)
- Filter warnings in `pyproject.toml` to follow deprecation messages in `pkg_resources`([#612](https://github.com/Substra/substra-backend/pull/612))
- Prefetch `function__inputs`, `function__outputs` in `ComputeTaskViewSet` ([#613](https://github.com/Substra/substra-backend/pull/613))
- Prefetch `inputs`, `outputs`, `inputs__asset`, `outputs__assets`, `function__inputs` and `function__outputs` in `CPTaskViewSet` ([#613](https://github.com/Substra/substra-backend/pull/613))
- Add `ComputeTaskWithDetailsSerializer` as a full-view serializer (including inputs and outputs) ([#613](https://github.com/Substra/substra-backend/pull/613))
- Prefetch `outputs` in `_PerformanceMetricSerializer` ([#611](https://github.com/Substra/substra-backend/pull/611))
- Index on `DataManager.channel` ([#607](https://github.com/Substra/substra-backend/pull/607))
- Prefetch on `DataManager.data_samples` ([#607](https://github.com/Substra/substra-backend/pull/607))
- OpenID Connect integration ([#609](https://github.com/Substra/substra-backend/pull/609))

### Fixed

- order of `data_sample_key` in tests ([#607](https://github.com/Substra/substra-backend/pull/607))

### Changed

- BREAKING: rename Algo to Function ([#573](https://github.com/Substra/substra-backend/pull/573))
- BREAKING: List views of `ComputeTask` objects no longer include the `ComputeTaskInput` not the `ComputeTaskOutput` objects ([#613](https://github.com/Substra/substra-backend/pull/613))
- Rename fields in export perf csv ([#593](https://github.com/Substra/substra-backend/pull/593))
- Durations in task profiling formatted in microseconds instead of 'DD hh:mm:ss.uuuuuu' ([#598](https://github.com/Substra/substra-backend/pull/598))
- Loop through assets only once in `get_exec_command_args` (in `substrapp`)([#615](https://github.com/Substra/substra-backend/pull/615))

### Removed

- filter warnings in `pyproject.toml` for previous deprecation warning in `rest_framework_simplejwt` ([#612](https://github.com/Substra/substra-backend/pull/612))
- model `TaskDataSample` and fields `ComputeTask.data_samples` / `DataManager.compute_tasks` ([#614](https://github.com/Substra/substra-backend/pull/614))
- `data_samples_keys` in `_PerformanceComputeTaskSerializer` ([#611](https://github.com/Substra/substra-backend/pull/611))

## [0.35.1](https://github.com/Substra/substra-backend/releases/tag/0.35.1) 2023-02-16

## Fixed

- `IncomingOrganization` password hashed twice when hasher algorithm was updated ([#592](https://github.com/Substra/substra-backend/pull/592))

### Removed

- BREAKING: asset values in compute task inputs/outputs. ([#509](https://github.com/Substra/substra-backend/pull/509))

## [0.35.0](https://github.com/Substra/substra-backend/releases/tag/0.35.0) 2023-02-06

### Added

- Contributing, contributors & code of conduct files (#563)

### Fixed

- Skaffold default example configuration ([#570](https://github.com/Substra/substra-backend/pull/570))
- Skaffold spawning instances in `default` namespace ([#574](https://github.com/Substra/substra-backend/pull/574))

### Removed

- Test only field for data samples (#551)
- BREAKING: failed task category from compute plan API response([#525](https://github.com/Substra/substra-backend/pull/525))

## [0.34.1](https://github.com/Substra/substra-backend/releases/tag/0.34.1) 2023-01-09

### Removed

- Update or create the task profiling or step profiling, instead of raising an error if already exists (#559)
- `parent_tasks` in `ComputeTask` ([#554](https://github.com/Substra/substra-backend/pull/554))

## [0.34.0](https://github.com/Substra/substra-backend/releases/tag/0.34.0) 2022-12-19

- Pass the rank of a task in a task properties dictionary, send in a `--task-properties` argument (#548)

## [0.33.0](https://github.com/Substra/substra-backend/releases/tag/0.33.0) 2022-11-22

### Added

- Add `create` api from model view to submit compute task output.
- Add role filter to users list.
- Endpoints to list task input/output assets
- "Kind" filters on task input and ouput assets endpoints.
- Return train_data_sample_keys and test_data_sample_keys fields in data manager "list" API responses

### Changed

- Extract inputs and outputs from db to build the workflow_graph response.
- Add compute task category unknown value
- Improved validation at user creation.

### Fixed

- Compute task outputs/inputs valid storage address.
- Signature cookie expiration date (#540)

### Removed

- Algo creation events aren't included in newsfeed anymore.
- Remove task category from the compute engine.
- BREAKING: compute task specific endpoints.
- BREAKING: category related fields to create task.
- BREAKING: compute task specific data
- BREAKING: task category

## [0.32.0] 2022-10-03

### Changed

- Container image build error logs are now saved to the DB and served via the API.
- Replace `algo` by `algo_key` in gRPC communication

### Added

- Allow configuring gRPC keepalive
- output identifier add in metric response object in `compute_plan perf` view.
- Prevent use of `__` in asset metadata keys
- Task input asset
- Accept `CSRF_TRUSTED_ORIGINS` env var as settings option
- Generic task endpoint to list/retrieve tasks
- Add inputs and output kinds in the workflow_graph response

### Fixed

- Bug in migration 0028_data_migration_compute_task_output.

### Removed

- BREAKING: model categories
- BREAKING: algo categories
- Outdated information on patching RabbitMQ for Apple Silicon chips.

## [0.31.0] 2022-09-26

### Changed

- Don't use the `status` field of the compute plan protocol buffer messages.
- BREAKING: remove `delete_intermediary_models` field from the `compute_plan` view.
- Use task output asset in API response
- Add channel column to input/output tables.
- The test task uses the same CLI arguments format as the other tasks.

### Fixed

- Bug when executing compute tasks with too many data samples (command line length exceeding max.) The substra-tools arguments are now passed using a file.

### Added

- CI job to test forward migrations.

## [0.30.0] 2022-09-19

### Changed

- BREAKING! Rename `localrep` app to `api`, see `UPGRADE.md` for migration.
- Accept `ALGO_UNKNOWN` as a valid algo category.

## [0.29.0] 2022-09-12

### Changed

- Stop generating algo method to execute from task category as it is now passed within substra cli
- Expose a default value (`dev`) for the backend version on the `/info` endpoint

### Added

- BREAKING: allow registration of users with role from the API and reset password mechanism
- Add address and permissions for `inputs` of kind datamanager and model in compute_tasks api response
- Synchronize compute task output assets into localrep
- Add `compute_task_key` filter on the model view.

## [0.28.0] 2022-08-29

### Added

- Enable gRPC keepalive

### Changed

- Increase limit for tasks displayed in CP workflow graph to 1000

### Removed

- Periodic celery task to queue pending tasks
- Local folder support

### Fixed

- Saving of tasks timings

## [0.27.0] 2022-08-23

### Added

- Add CP default status at creation

## [0.26.0] 2022-08-17

### Added

- Add method to update algo, compute_plan and data manager name

### Changed

- BREAKING: Replace celery RabbitMQ by Redis

## [0.25.0] 2022-08-09

### Added

- `transient` field to task outputs
- Include tasks output models and performances in output fields in task endpoint response

### Changed

- Use gRPC stream to listen to events
- Update orchestrator protobuf definitions
- Pass output identifier when registering assets

### Removed

- BREAKING: Orchestrator RabbitMQ connection to listen to events

## [0.24.0] 2022-08-01

### Added

- The /task/bulk_create/ endpoint now accepts the "inputs" field

### Removed

- Category filter from /algos/ route
- Legacy compute task permission fields

### Fixed

- Removed invalid metric asset kind from newsfeed
- Add missing compute task outputs data migration

## [0.23.1] 2022-07-26

### Changed

- CP Performance endpoint returns array of performances in "results" instead of dict

## [0.23.0] 2022-07-25

### Removed

- Rule-based logic for compute task output permissions. Instead, permissions are now explicitly provided by the end-user
- The "out_trunk_model_permissions" field was removed from the /task/bulk_create/ endpoint. It is superseded by the "outputs" field.

### Fixed

- Scheduler worker now processes predict tasks too
- Compute plan status is now correctly set to CANCELED

### Added

- Local representation of task outputs
- Local representation of task inputs
- Compute tasks returned by the API now have the "outputs" field
- Compute tasks returned by the API now have the "inputs" field
- The /task/bulk_create/ endpoint now accepts the "outputs" field
- Compute plan ranks and round_idx list to cp perf view

### Changed

- `python manage.py get_outgoing_organization` can now be used to check inter-org connection.

## [0.22.0] 2022-07-11

### Removed

- BREAKING: Removed the `metric_keys` property of test tasks in favor of the generic `algo` field.

### Added

- Execute predict tasks.
- Backend hostname to the organization view

### Fixed

- Compute plan workflow graph endpoint handles predict tasks
- Don't raise an error when retrying certain orchestrator requests - @grpc_retry

## [0.21.0] 2022-07-05

### Added

- Filtering on compute tasks metadata
- View to build task workflow graph

### Fixed

- arm64 stage in the dockerfile to install dependencies and build psycopg2 from source

## [0.20.0] 2022-06-27

### Added

- Filtering and ordering on duration in CPs ans Tasks views

### Fixed

- deprecated metadata was used during event processing
- datamanagers' and metrics' storage_addresses in task responses
- CP localrep sync issues resulting in missing CP duration

### Changed

- Removed the search parameter from API

### Changed

- Return HTTP 413 "Payload Too Large" when the orchestrator gRPC payload exceeds max size

## [0.19.0] 2022-06-20

### Fixed

- failure_report KeyError when updating compute task (localrep sync)
- password displayed when running django commands to add users

### Added

- Filtering on compute plan metadata

### Changed

- use tasks from event for task processing
- set task status to doing in compute task task
- remove the `prepare_task` Celery task

### Removed

- Delete metrics endpoints; use algo endpoints instead

## [0.18.0] 2022-06-14

### Removed

- BREAKING: drop the s3 upload feature

### Changed

- BREAKING: rename node to organization

### Fixed

- Duplicated datasamples

## [0.17.0] 2022-06-07

### Added

- Support for predict Algos
- Hardcode task outputs
- Cross asset filtering by key on asset views
- Health service for the event app
- (BREAKING) New register tasks endpoint

### Changed

- Use assets embedded in events during sync

## [0.16.0] 2022-05-30

### Fixed

- Full resync: also resync metrics when syncing algos
- CP name properly included in newsfeed items
- Clean up `taskdir` before adding assets to it
- Only run `remove_directory_contents` when the directory exists

### Added

- Empty compute plan status

## [0.15.0] 2022-05-23

### Added

- Possibility to filter only important news in newsfeed view

### Changed

- (BREAKING) Store enum values as string (impact ordering) - Model
- Within a CP, allow image builds to occur concurrently with another task's execution
- (BREAKING) Store enum values as string (impact ordering) - ComputePlan ComputeTask
- Add algo inputs and outputs

### Fixed

- Mount GPU manually in GKE to be able to share them

## [0.14.0] 2022-05-16

### Added

- ComputePlanMetadataViewSet to list all existing compute plans metadata
- Filtering on timestamp for newsfeed
- View to export performances as csv file download

### Changed

- (BREAKING) Store enum values as string (impact ordering) - Algo
- (BREAKING) Add mandatory name field to compute plan
- Use the algo checksum as image tag

### Fixed

- Completed pod state in `kubernetes_utils.watch_pod()`

## [0.13.0] 2022-05-09

### Changed

- Merge Metric and Algo view and model , see UPGRADE.md for migration
- (BREAKING) feat!: Get compute plan key from the request data
- Add django-filters on datasample view and define custom IN lookup filters for all views

### Added

- Filtering on permissions for algos and datamanagers

## [0.12.0] 2022-05-03

### Changed

- (BREAKING) Pass named inputs/outputs to algos
- Set default pagination page size and max page size
- Use standard ModelViewSet to handle DataSample list and retrieve calls
- Newsfeed now returns items for metric, algo and datamanager creation
- DataSamples for Localrep ComputeTask are foreign keys
- Removed MELLODDY-specific code

### Added

- Filtering using django-filters

### Fixed

- Create ModelRep DB instance when registering model in the orchestrator
- End date for failed CP
- Prevent 301 redirects when downloading failure reports
- Add SETFCAP capability to kaniko image builder to avoid build issue on security.capability
- (BREAKING) Fix cancelled CP inconsistencies
- Cancel CP should return json

## [0.11.0] 2022-04-19

### Fixed

- Uuid substring collision made tests randomly fail

### Removed

- Drop support for `DEBUG_QUICK_IMAGE`

## [0.10.1] 2022-04-13

### Changed

- Set log level to DEBUG in dev
- Remove Orchestrator{Aggregate, CompositeTrain, Test, Train}TaskSerializer and use orchestrator client directly
- Handle error values in mapping functions
- Remove `single-snapshot` in kaniko build option

### Fixed

- Handle disabled model in resync by making address not mandatory

## [0.10.0] 2022-04-11

### Added

- Store computetasks logs address and owner in localrep
- Optimize computetask list queryset
- Full-text search in CP name
- Local representation of node assets
- Retrieve files to download permissions and storage address from localrep
- Add API endpoint to serve all performances of a given compute plan
- Extra ordering options for compute plans and tasks
- Full text search in all assets names and keys

### Changed

- Make possible to start the backend-server without orchestrator connection available
- Use the substra-tools image 0.10.0 in the example yaml files
- Return 410 error for all attempts at file download in isolated mode
- Removed unused description files cache for remote assets
- Use standard ModelViewSet to handle Metric list and retrieve calls
- Use standard ModelViewSet to handle Algo list and retrieve calls
- Removed unused create_or_update_model method
- Use standard ModelViewSet to handle DataManager list and retrieve calls
- Use standard ModelViewSet to handle ComputeTask list and retrieve calls
- Use standard ModelViewSet to handle Model list and retrieve calls
- Add field compute plan name in NewsFeedViewSet
- Use standard ModelViewSet to handle ComputePlan list and retrieve calls
- Remove OrchestratorAlgoSerializer and use orchestrator client directly
- Remove OrchestratorDataManagerSerializer and use orchestrator client directly
- Disabled models do not expose an address
- Increase max page size default
- Remove OrchestratorDataSampleSerializer and OrchestratorDataSampleUpdateSerializer and use orchestrator client directly
- Remove OrchestratorMetricSerializer and use orchestrator client directly
- Remove OrchestratorModelSerializer
- Remove OrchestratorComputePlanSerializer and use orchestrator client directly
- Dev conf uses latest substra-tools image

### Fixed

- Disable model in localrep
- Compute CP dates after updating related tasks
- Compute task stays doing forever if saving the model raises an OSError
- Compute CP dates before updating CP status
- W340 null has no effect on ManyToManyField during migrations

## [0.9.0] 2022-03-01

### Added

- Clear the asset buffer When the disk is full
- Add API endpoint to serve failed compute task logs
- In the API, allow filtering events by timestamp
- Local representation of datamanager assets
- Add task category in news feed view
- Local representation of datasample assets
- Local representation of computeplan assets
- Local representation of computetask assets
- Add `ORCHESTRATOR_RABBITMQ_ACTIVITY_TIMEOUT` to restart event app if no activity
- Exponential backoff of celery tasks retry
- Compute CP tasks count and status from localrep data
- Use localrep data in CPAlgoViewSet
- Local representation of performance assets
- Use localrep data in tasks views
- Use localrep performances in tasks views
- Localrep computeplan status field, that is synced when receiving computetask event update instead of in the computeplan view
- Compute and store cp dates and duration during sync
- Local representation of model assets
- Use localrep data in newsfeed view

### Changed

- When resyncing the local representation, only fetch the latest events
- Accept datamanager events with missing logs_permissions in localsync
- Update datasamples protobuf. `register_datasamples` return now the datasamples list registered
- When resyncing the local representation, fetch events by page of 1000 instead of one-by-one
- Update computetask protobuf. `register_tasks` return now the tasks list registered
- Stream directly asset files from MinIO without loading them on disk
- compute_plan["failed_task"] is populated when syncing a failed task event in the event app instead of in the views
- Switch from aiopika to pika in the event app
- Cancel a compute task when its compute plan is not runnable

### Fixed

- Handle incomplete medata in newsfeed
- Fix container image build lock, to prevent ImageEntrypoint concurrency issues
- Fix filters on datamanager list view
- Handle missing failed task for failed CP status
- Handle case of resync with no new events
- Corrupted asset buffer when asset download fails
- Possible race condition when deleting pod
- Use failure report owner to determine whether storage address is local
- Check that start_date and end_date are not `None` to compute duration
- Assets filtering on enums
- Synchronize performances and models before update computetask status
- Compute CP status after computetasks resync
- Safe serializer should not break db transaction

## [0.8.0] 2022-01-16

### Added

- The datamanager asset now has a `logs_permission` field
- Local representation of algo assets
  - `localrep` app with `Event` and `Algo`: migration, model and serializer
  - `localsync` module in `events` app, using localrep models and serializers to load orchestrator response and save events and algos metadata in DB.
  - `resync` the local representation at the start of the event app
  - `sync_on_event_message` method to save in the local representation the algos and events when an event on the algo is received.
- Local representation of metric assets
- Add a news feed endpoint to watch compute task event update

### Changed

- Update `substrapp` algo viewset:
  - For `list` and `retrieve`, replace orchestrator query by `localrep` models queryset.
  - For `create`, create `localrep` algo before synchronization to be able to instantly (locally) query a newly created algo.

### Fixed

- News feed now handles incomplete event metadata

## [0.7.0] 2022-01-05

### Fixed

- Preserve order of parent tasks when registering a new task
- Memory leak in MinIO client
- Zombie compute pods (pods which are never deleted) in edge cases
- Missing timeout on event app orchestrator RabbitMQ connection
- Fixed task failure due to concurrent download of input assets

### Changed

- When executing compute tasks, store Algos and Metrics in temporary folders instead of the Asset Buffer
- On compute task failure, send the type of the error that occurred to the orchestrator
- Remove validated field on Datasample, Algo, Metrics, Model and Datamanager models
- Update backend and metric export python dependencies
- Reorganize and rename exported archives

## [0.6.0] 2021-12-01

### Added

- Metrics support for the Django app behind the flag `ENABLE_METRICS`
- Limit file size upload to `DATA_UPLOAD_MAX_SIZE`
- Setting to run in "isolated" mode (when there is no backend data, only orchestrator data)
- Add `COMPUTE_POD_GKE_GPUS_LIMITS` setting to enable usage of GPU by the compute pod on GKE
- Add new route to list all algos of a compute plan
- Add cp start date, end date and duration

### Changed

- Datasample upload by path is possible only from the servermedias volumes
- algo, metrics and datamanager are stored in Minio instead of the medias volume
- Rename `RUN_AS_GROUP` setting to `COMPUTE_POD_RUN_AS_GROUP`.
- Rename `RUN_AS_USER` setting to `COMPUTE_POD_RUN_AS_USER`.
- Rename `FS_GROUP` setting to `COMPUTE_POD_FS_GROUP`.
- Do not openly expose media directory
- Do not mount the serviceAccount token on the compute pod
- Switch log format to JSON

### Removed

- `COMPUTE_REGISTRY` setting, you should provide the whole kaniko image name in `KANIKO_IMAGE`

### Fixed

- Properly prevent path traversal in archives and don't allow symbolic links
- Inject task extra information even if there are no query params

## [0.5.0] 2021-11-02

### Added

- Support for filters on compute plan sub routes
- `COMMON_HOST_DOMAIN` variable env now required to set domain property of JWT cookies
- Models and Datasamples are now stored in MinIO (they were previously stored on the filesystem)
- Possibility to deploy deploy multiple workers on different kubernetes nodes in order to use compute resources in parallel. See [charts CHANGELOG.md](./charts/substra-backend/CHANGELOG.md#6.0.0) for more details
- post_delete signal upon model deletion to remove the model from Minio storage
- Add task extra information related to start_date and end_date
- serve API behind subpath with `SUBPATH` env var

### Changed

- Task data are now mounted on `/substra_internal` instead of `/sandbox`
- (BREAKING) Replace objective by metric
- (BREAKING) Multiple metrics and performances per test task
- Insert full data manager, metrics and parent tasks objects in tuple responses for retrieve calls
- Validate orchestrator connection on readiness and liveness api checks

### Fixed

- Set the local folder dynamically instead of leaving it to substra-tools default
- Fix trailing comma that turned versions at /info into lists
- Accept `UUID.hex` UUID as asset keys
- Trying to download a disabled model will now result in a consistent http 410 error code instead of an http 500 or http 404 error code

## [0.4.0] 2021-10-04

### Added

- Models exported to bucket are prefixed with their compute plan's ID
- Backend version build in docker image and exposed in `/info`
- Orchestrator and chaincode version in `/info`

### Changed

- Unified all 3 categories of algos in a single endpoint.
  - all algos are now served through `/algo` and `/algo/:key`
  - when creating a new algo, you must give a `category` property which value is one of `ALGO_SIMPLE`, `ALGO_COMPOSITE` or `ALGO_AGGREGATE`
- Search objective by metrics with `/objective?search=objective:metrics_name:[METRIC_NAME]` instead of `/objective?search=objective:metrics:[METRIC_NAME]`
- Switched to structured logging
- Made `/info` semi-public: returns some information for anonymous users and some more for authenticated ones

### Removed

- Routes `/aggregate_algo`, `/aggregate_algo/:key`, `/composite_algo` and `/composite_algo/:key` (all algos now served through `/algo` and `/algo/:key`)
- Asset filters on attributes from different assets
  example : `GET /objective?search=traintuple:key:foo`
  The composed filter that are removed are:

```
    /dataset?search=model:field_key:value
    /dataset?search=objective:field_key:value
    /algo?search=model:field_key:value
    /objective?search=model:field_key:value
    /objective?search=dataset:field_key:value
    /model?search=algo:field_key:value
    /model?search=dataset:field_key:value
    /model?search=objective:field_key:value
```

## [0.3.1] - 2021-08-25

### Added

- Add routes to get a compute plan's compute tasks by type

### Fixed

- Compute-plan-less compute tasks all using the same lock key
- Asset buffer skipping some data samples

## [0.3.0] - 2021-08-17

### Added

- API: Added Pagination for lists of asset

### Fixed

- Fix kaniko local directory cache for base images
- The backend is compatible with FL worflow again
- lock_resource was raising a FileNotFound exception in high concurrency scenarios

### Changed

- Refactor views/datasamples.py
- The opener is now downloaded instead of being copied from disk
- Better use of shutil.copytree

## [0.2.0] - 2021-08-04

### Added

- Add docker config secret name for kaniko builder .
- Add registry cleaning tasks.

### Changed

- Use a single compute pod for all the tasks of a compute plan .
- Add two missing `__init__` files .
- Update python dependencies.

## [0.1.12] - 2021-04-13

### Added

- Export models .

### Fixed

- Binding to service.port instead of 8000.
- Datasample order for metrics.
- Auto-allocate docker-registry node port .

### Changed

- Bump django from 2.2.19 to 2.2.20 in /backend.
- Update cryptography to its latest release.

## [0.1.11] - 2021-03-12

### Changed

- Update django and django-celery-results.

## [0.1.10] - 2021-03-09

### Changed

- docker-registry default service value to nodePort
- Update grpcio
- Change local peer hostname to prevent issue from grpc client
- Fix JWT token blacklist at logout
- Add django shared cache to prevent issue in throttling
- Less permissive CORS & AllowHosts

## [0.1.9] - 2021-02-09

## [0.1.8] - 2021-01-27

## [0.1.7] - 2021-01-26

## [0.1.6] - 2020-12-08

## [0.1.5] - 2020-12-01

## [0.1.4] - 2020-11-30

## [0.1.3] - 2020-10-02

## [0.1.2] - 2020-09-29

## [0.1.1] - 2020-08-12

## [0.1.0] - 2020-07-31

## [0.0.24] - 2020-07-21

## [0.0.23] - 2020-07-15

## [0.0.22] - 2020-07-10

## [0.0.21] - 2020-07-08

## [0.0.20] - 2020-07-07

## [0.0.19] - 2020-07-03

## [0.0.18] - 2020-06-03

## [0.0.17] - 2020-06-02

## [0.0.16] - 2020-05-29

## [0.0.15] - 2020-05-28

## [0.0.14] - 2020-05-18

## [0.0.13] - 2020-05-12

## [0.0.12] - 2020-04-14

## [0.0.11] - 2019-12-13

## [0.0.10] - 2019-12-06

## [0.0.9] - 2019-11-05

## [0.0.8] - 2019-05-27

## [0.0.7] - 2019-04-10

## [0.0.6] - 2019-04-03

## [0.0.5] - 2019-03-04

## [0.0.4] - 2019-03-04

## [0.0.3] - 2019-02-20

## [0.0.2] - 2019-02-15

## [0.0.1] - 2019-01-08
