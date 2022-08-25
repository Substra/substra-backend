# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Increase limit for tasks displayed in CP workflow graph to 1000 (#1266)

### Removed

- Periodic celery task to queue pending tasks
- Local folder support

## [0.27.0] 2022-08-23

### Added

- Add CP default status at creation (#1248)

## [0.26.0] 2022-08-17

### Added

- Add method to update algo, compute_plan and data manager name (#1137)

## [0.25.0] 2022-08-09

### Added

- `transient` field to task outputs (#1236)
- Include tasks output models and performances in output fields in task endpoint response (#1201)

### Changed

- Use gRPC stream to listen to events (#1188)
- Update orchestrator protobuf definitions
- Pass output identifier when registering assets

### Removed

- BREAKING: Orchestrator RabbitMQ connection to listen to events (#1188)

## [0.24.0] 2022-08-01

### Added

- The /task/bulk_create/ endpoint now accepts the "inputs" field (#1111)

### Removed

- Category filter from /algos/ route (#1199)
- Legacy compute task permission fields (#1203)

### Fixed

- Removed invalid metric asset kind from newsfeed (#1200)
- Add missing compute task outputs data migration (#1205)

## [0.23.1] 2022-07-26

### Changed

- CP Performance endpoint returns array of performances in "results" instead of dict (#1198)

## [0.23.0] 2022-07-25

### Removed

- Rule-based logic for compute task output permissions. Instead, permissions are now explicitly provided by the end-user (#1128)
- The "out_trunk_model_permissions" field was removed from the /task/bulk_create/ endpoint. It is superseded by the "outputs" field. (#1128)

### Fixed

- Scheduler worker now processes predict tasks too (#1184)
- Compute plan status is now correctly set to CANCELED (#1193)

### Added

- Local representation of task outputs (#1181)
- Local representation of task inputs (#1182)
- Compute tasks returned by the API now have the "outputs" field  (#1181)
- Compute tasks returned by the API now have the "inputs" field (#1182)
- The /task/bulk_create/ endpoint now accepts the "outputs" field (#1128)
- Compute plan ranks and round_idx list to cp perf view (#1136)

### Changed

- `python manage.py get_outgoing_organization` can now be used to check inter-org connection. (#1161)

## [0.22.0] 2022-07-11

### Removed

- BREAKING: Removed the `metric_keys` property of test tasks in favor of the generic `algo` field. (#1091)

### Added

- Execute predict tasks. (#1091)
- Backend hostname to the organization view (#1167)

### Fixed

- Compute plan workflow graph endpoint handles predict tasks (#1171)
- Don't raise an error when retrying certain orchestrator requests - @grpc_retry (#1173)

## [0.21.0] 2022-07-05

### Added

- Filtering on compute tasks metadata (#1131)
- View to build task workflow graph (#1135)

### Fixed

- arm64 stage in the dockerfile to install dependencies and build psycopg2 from source (#1169)

## [0.20.0] 2022-06-27

### Added

- Filtering and ordering on duration in CPs ans Tasks views (#1101)

### Fixed

- deprecated metadata was used during event processing (#1116)
- datamanagers' and metrics' storage_addresses in task responses (#1124)
- CP localrep sync issues resulting in missing CP duration (#1119)

### Changed

- Removed the search parameter from API (#1123)

### Changed

- Return HTTP 413 "Payload Too Large" when the orchestrator gRPC payload exceeds max size (#1122)

## [0.19.0] 2022-06-20

### Fixed

- failure_report KeyError when updating compute task (localrep sync) (#1092)
- password displayed when running django commands to add users (#1109)

### Added

- Filtering on compute plan metadata (#1043)

### Changed

- use tasks from event for task processing (#1104)
- set task status to doing in compute task task (#1105)
- remove the `prepare_task` Celery task (#1106)

### Removed

- Delete metrics endpoints; use algo endpoints instead (#1113)

## [0.18.0] 2022-06-14

### Removed

- BREAKING: drop the s3 upload feature (#1095)

### Changed

- BREAKING: rename node to organization (#1096)

### Fixed

- Duplicated datasamples (#1102)

## [0.17.0] 2022-06-07

### Added

- Support for predict Algos (#1071)
- Hardcode task outputs (#1068)
- Cross asset filtering by key on asset views (#1070)
- Health service for the event app (#1089)
- (BREAKING) New register tasks endpoint (#1053)

### Changed

- Use assets embedded in events during sync (#1062)

## [0.16.0] 2022-05-30

### Fixed

- Full resync: also resync metrics when syncing algos (#1063)
- CP name properly included in newsfeed items (#1060)
- Clean up `taskdir` before adding assets to it (#1039)
- Only run `remove_directory_contents` when the directory exists (#1051)

### Added

- Empty compute plan status (#1048)

## [0.15.0] 2022-05-23

### Added

- Possibility to filter only important news in newsfeed view (#1050)

### Changed

- (BREAKING) Store enum values as string (impact ordering) - Model (#1044)
- Within a CP, allow image builds to occur concurrently with another task's execution (#996)
- (BREAKING) Store enum values as string (impact ordering) - ComputePlan ComputeTask (#1045)
- Add algo inputs and outputs (#1030)

### Fixed

- Mount GPU manually in GKE to be able to share them (#1041)

## [0.14.0] 2022-05-16

### Added

- ComputePlanMetadataViewSet to list all existing compute plans metadata (#1042)
- Filtering on timestamp for newsfeed (#1028)
- View to export performances as csv file download (#1031)

### Changed

- (BREAKING) Store enum values as string (impact ordering) - Algo (#1040)
- (BREAKING) Add mandatory name field to compute plan (#1027)
- Use the algo checksum as image tag (#1019)

### Fixed

- Completed pod state in `kubernetes_utils.watch_pod()` (#1046)

## [0.13.0] 2022-05-09

### Changed

- Merge Metric and Algo view and model (#976), see UPGRADE.md for migration
- (BREAKING) feat!: Get compute plan key from the request data (#999)
- Add django-filters on datasample view and define custom IN lookup filters for all views (#1017)

### Added

- Filtering on permissions for algos and datamanagers (#1018)

## [0.12.0] 2022-05-03

### Changed

- (BREAKING) Pass named inputs/outputs to algos (#877)
- Set default pagination page size and max page size (#950)
- Use standard ModelViewSet to handle DataSample list and retrieve calls (#972)
- Newsfeed now returns items for metric, algo and datamanager creation (#954)
- DataSamples for Localrep ComputeTask are foreign keys (#944)
- Removed MELLODDY-specific code (#998)

### Added

- Filtering using django-filters (#946)

### Fixed

- Create ModelRep DB instance when registering model in the orchestrator (#965)
- End date for failed CP (#961)
- Prevent 301 redirects when downloading failure reports (#975)
- Add SETFCAP capability to kaniko image builder to avoid build issue on security.capability (#995)
- (BREAKING) Fix cancelled CP inconsistencies (#894)
- Cancel CP should return json (#1020)

## [0.11.0] 2022-04-19

### Fixed

- Uuid substring collision made tests randomly fail (#941)

### Removed

- Drop support for `DEBUG_QUICK_IMAGE` (#957)

## [0.10.1] 2022-04-13

### Changed

- Set log level to DEBUG in dev (#952)
- Remove Orchestrator{Aggregate, CompositeTrain, Test, Train}TaskSerializer and use orchestrator client directly (#920)
- Handle error values in mapping functions (#945)
- Remove `single-snapshot` in kaniko build option (#897)

### Fixed

- Handle disabled model in resync by making address not mandatory (#948)

## [0.10.0] 2022-04-11

### Added

- Store computetasks logs address and owner in localrep (#801)
- Optimize computetask list queryset (#810)
- Full-text search in CP name (#823)
- Local representation of node assets (#814)
- Retrieve files to download permissions and storage address from localrep (#800)
- Add API endpoint to serve all performances of a given compute plan (#907)
- Extra ordering options for compute plans and tasks (#919)
- Full text search in all assets names and keys (#931)

### Changed

- Make possible to start the backend-server without orchestrator connection available (#811)
- Use the connect-tools image 0.10.0 in the example yaml files (#850)
- Return 410 error for all attempts at file download in isolated mode (#849)
- Removed unused description files cache for remote assets (#873)
- Use standard ModelViewSet to handle Metric list and retrieve calls (#856)
- Use standard ModelViewSet to handle Algo list and retrieve calls (#878)
- Removed unused create_or_update_model method (#885)
- Use standard ModelViewSet to handle DataManager list and retrieve calls (#882)
- Use standard ModelViewSet to handle ComputeTask list and retrieve calls (#891)
- Use standard ModelViewSet to handle Model list and retrieve calls (#892)
- Add field compute plan name in NewsFeedViewSet (#905)
- Use standard ModelViewSet to handle ComputePlan list and retrieve calls (#893)
- Remove OrchestratorAlgoSerializer and use orchestrator client directly (#818)
- Remove OrchestratorDataManagerSerializer and use orchestrator client directly (#908)
- Disabled models do not expose an address (#910)
- Increase max page size default (#922)
- Remove OrchestratorDataSampleSerializer and OrchestratorDataSampleUpdateSerializer and use orchestrator client directly (#911)
- Remove OrchestratorMetricSerializer and use orchestrator client directly (#912)
- Remove OrchestratorModelSerializer (#915)
- Remove OrchestratorComputePlanSerializer and use orchestrator client directly (#916)
- Dev conf uses latest connect-tools image (#943)

### Fixed

- Disable model in localrep (#848)
- Compute CP dates after updating related tasks (#855)
- Compute task stays doing forever if saving the model raises an OSError (#880)
- Compute CP dates before updating CP status (#883)
- W340 null has no effect on ManyToManyField during migrations (#947)

## [0.9.0] 2022-03-01

### Added

- Clear the asset buffer When the disk is full (#472)
- Add API endpoint to serve failed compute task logs (#579)
- In the API, allow filtering events by timestamp (#649)
- Local representation of datamanager assets (#648)
- Add task category in news feed view (#685)
- Local representation of datasample assets (#668)
- Local representation of computeplan assets (#651)
- Local representation of computetask assets (#688)
- Add `ORCHESTRATOR_RABBITMQ_ACTIVITY_TIMEOUT` to restart event app if no activity (#739)
- Exponential backoff of celery tasks retry (#736)
- Compute CP tasks count and status from localrep data (#717)
- Use localrep data in CPAlgoViewSet (#763)
- Local representation of performance assets (#778)
- Use localrep data in tasks views (#760)
- Use localrep performances in tasks views (#780)
- Localrep computeplan status field, that is synced when recieving computetask event update instead of in the computeplan view  (#762)
- Compute and store cp dates and duration during sync (#757)
- Local representation of model assets (#784)
- Use localrep data in newsfeed view (#795)

### Changed

- When resyncing the local representation, only fetch the latest events (#656)
- Accept datamanager events with missing logs_permissions in localsync (#678)
- Update datasamples protobuf. `register_datasamples` return now the datasamples list registered (#665)
- When resyncing the local representation, fetch events by page of 1000 instead of one-by-one (#680)
- Update computetask protobuf. `register_tasks` return now the tasks list registered (#677)
- Stream directly asset files from MinIO without loading them on disk (#732)
- compute_plan["failed_task"] is populated when syncing a failed task event in the event app instead of in the views (#755)
- Switch from aiopika to pika in the event app (#768)
- Cancel a compute task when its compute plan is not runnable (#796)

### Fixed

- Handle incomplete medata in newsfeed (#652)
- Fix container image build lock, to prevent ImageEntrypoint concurrency issues (#671)
- Fix filters on datamanager list view (#681)
- Handle missing failed task for failed CP status (#682)
- Handle case of resync with no new events (#695)
- Corrupted asset buffer when asset download fails (#673)
- Possible race condition when deleting pod (#746)
- Use failure report owner to determine whether storage address is local (#748)
- Check that start_date and end_date are not `None` to compute duration (#770)
- Assets filtering on enums (#788)
- Synchronize performances and models before update computetask status (#792)
- Compute CP status after computetasks resync (#793)
- Safe serializer should not break db transaction (#794)

## [0.8.0] 2022-01-16

### Added

- The datamanager asset now has a `logs_permission` field (#581)
- Local representation of algo assets (#473)
  - `localrep` app with `Event` and `Algo`: migration, model and serializer
  - `localsync` module in `events` app, using localrep models and serializers to load orchestrator response and save events and algos metadata in DB.
  - `resync` the local representation at the start of the event app
  - `sync_on_event_message` method to save in the local representation the algos and events when an event on the algo is received.
- Local representation of metric assets (#637)
- Add a news feed endpoint to watch compute task event update (#541)

### Changed

- Update `substrapp` algo viewset:
  - For `list` and `retrieve`, replace orchestrator query by `localrep` models queryset.
  - For `create`, create `localrep` algo before synchronization to be able to instantly (locally) query a newly created algo.

### Fixed

- News feed now handles incomplete event metadata (#652)

## [0.7.0] 2022-01-05

### Fixed

- Preserve order of parent tasks when registering a new task (#583)
- Memory leak in MinIO client
- Zombie compute pods (pods which are never deleted) in edge cases
- Missing timeout on event app orchestrator RabbitMQ connection
- Fixed task failure due to concurrent download of input assets (#571)

### Changed

- When executing compute tasks, store Algos and Metrics in temporary folders instead of the Asset Buffer
- On compute task failure, send the type of the error that occurred to the orchestrator
- Remove validated field on Datasample, Algo, Metrics, Model and Datamanager models (#544)
- Update backend and metric export python dependencies
- Reorganize and rename exported archives (#613)

## [0.6.0] 2021-12-01

### Added

- Metrics support for the Django app behind the flag `ENABLE_METRICS`
- Limit file size upload to `DATA_UPLOAD_MAX_SIZE` (#450)
- Setting to run in "isolated" mode (when there is no backend data, only orchestrator data) (#392)
- Add `COMPUTE_POD_GKE_GPUS_LIMITS` setting to enable usage of GPU by the compute pod on GKE (#460)
- Add new route to list all algos of a compute plan (#393)
- Add cp start date, end date and duration (#402)

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

- `COMPUTE_REGISTRY` setting, you should provide the whole kaniko image name in `KANIKO_IMAGE` (#350)

### Fixed

- Properly prevent path traversal in archives and don't allow symbolic links (#465)
- Inject task extra information even if there are no query params (#536)

## [0.5.0] 2021-11-02

### Added

- Support for filters on compute plan sub routes
- `COMMON_HOST_DOMAIN` variable env now required to set domain property of JWT cookies
- Models and Datasamples are now stored in MinIO (they were previously stored on the filesystem)
- Possibility to deploy deploy multiple workers on different kubernetes nodes in order to use compute resources in parallel. See [charts CHANGELOG.md](./charts/substra-backend/CHANGELOG.md#6.0.0) for more details
- post_delete signal upon model deletion to remove the model from Minio storage
- Add task extra information related to start_date and end_date
- serve API behind subpath with `SUBPATH` env var (#386)

### Changed

- Task data are now mounted on `/substra_internal` instead of `/sandbox`
- (BREAKING) Replace objective by metric (#313)
- (BREAKING) Multiple metrics and performances per test task (#320)
- Insert full data manager, metrics and parent tasks objects in tuple responses for retrieve calls
- Validate orchestrator connection on readiness and liveness api checks

### Fixed

- Set the local folder dynamically instead of leaving it to connect-tools default
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
exemple : `GET /objective?search=traintuple:key:foo`
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

- Add routes to get a compute plan's compute tasks by type (#204)

### Fixed

- Compute-plan-less compute tasks all using the same lock key (#205)
- Asset buffer skipping some data samples (#228)

## [0.3.0] - 2021-08-17

### Added

- API: Added Pagination for lists of asset (#123)

### Fixed

- Fix kaniko local directory cache for base images (#190)
- The backend is compatible with FL worflow again (#194)
- lock_resource was raising a FileNotFound exception in high concurrency scenarios (#187)

### Changed

- Refactor views/datasamples.py (#189)
- The opener is now downloaded instead of being copied from disk (#193)
- Better use of shutil.copytree (#182)

## [0.2.0] - 2021-08-04

### Added

- Add docker config secret name for kaniko builder (#99).
- Add registry cleaning tasks.

### Changed

- Use a single compute pod for all the tasks of a compute plan (#17).
- Add two missing `__init__` files (#89).
- Update python dependencies.

## [0.1.12] - 2021-04-13

### Added

- Export models (#395).

### Fixed

- Binding to service.port instead of 8000.
- Datasample order for metrics.
- Auto-allocate docker-registry node port (#391).

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

[Unreleased]: https://github.com/owkin/connect-backend/compare/0.2.0...HEAD
[0.2.0]: https://github.com/owkin/connect-backend/compare/0.1.12...0.2.0
[0.1.12]: https://github.com/owkin/connect-backend/compare/0.1.11...0.1.12
[0.1.11]: https://github.com/owkin/connect-backend/compare/0.1.10...0.1.11
[0.1.10]: https://github.com/owkin/connect-backend/compare/0.1.9...0.1.10
[0.1.9]: https://github.com/owkin/connect-backend/compare/0.1.8...0.1.9
[0.1.8]: https://github.com/owkin/connect-backend/compare/0.1.7...0.1.8
[0.1.7]: https://github.com/owkin/connect-backend/compare/0.1.6...0.1.7
[0.1.6]: https://github.com/owkin/connect-backend/compare/0.1.5...0.1.6
[0.1.5]: https://github.com/owkin/connect-backend/compare/0.1.4...0.1.5
[0.1.4]: https://github.com/owkin/connect-backend/compare/0.1.3...0.1.4
[0.1.3]: https://github.com/owkin/connect-backend/compare/0.1.2...0.1.3
[0.1.2]: https://github.com/owkin/connect-backend/compare/0.1.1...0.1.2
[0.1.1]: https://github.com/owkin/connect-backend/compare/0.1.0...0.1.1
[0.1.0]: https://github.com/owkin/connect-backend/compare/0.0.24...0.1.0
[0.0.24]: https://github.com/owkin/connect-backend/compare/0.0.23...0.0.24
[0.0.23]: https://github.com/owkin/connect-backend/compare/0.0.22...0.0.23
[0.0.22]: https://github.com/owkin/connect-backend/compare/0.0.21...0.0.22
[0.0.21]: https://github.com/owkin/connect-backend/compare/0.0.20...0.0.21
[0.0.20]: https://github.com/owkin/connect-backend/compare/0.0.19...0.0.20
[0.0.19]: https://github.com/owkin/connect-backend/compare/0.0.18...0.0.19
[0.0.18]: https://github.com/owkin/connect-backend/compare/0.0.17...0.0.18
[0.0.17]: https://github.com/owkin/connect-backend/compare/0.0.16...0.0.17
[0.0.16]: https://github.com/owkin/connect-backend/compare/0.0.15...0.0.16
[0.0.15]: https://github.com/owkin/connect-backend/compare/0.0.14...0.0.15
[0.0.14]: https://github.com/owkin/connect-backend/compare/0.0.13...0.0.14
[0.0.13]: https://github.com/owkin/connect-backend/compare/0.0.12...0.0.13
[0.0.12]: https://github.com/owkin/connect-backend/compare/0.0.11...0.0.12
[0.0.11]: https://github.com/owkin/connect-backend/compare/0.0.10...0.0.11
[0.0.10]: https://github.com/owkin/connect-backend/compare/0.0.9...0.0.10
[0.0.9]: https://github.com/owkin/connect-backend/compare/0.0.8...0.0.9
[0.0.8]: https://github.com/owkin/connect-backend/compare/0.0.7...0.0.8
[0.0.7]: https://github.com/owkin/connect-backend/compare/0.0.6...0.0.7
[0.0.6]: https://github.com/owkin/connect-backend/compare/0.0.5...0.0.6
[0.0.5]: https://github.com/owkin/connect-backend/compare/0.0.4...0.0.5
[0.0.4]: https://github.com/owkin/connect-backend/compare/0.0.3...0.0.4
[0.0.3]: https://github.com/owkin/connect-backend/compare/0.0.2...0.0.3
[0.0.2]: https://github.com/owkin/connect-backend/compare/0.0.1...0.0.2
[0.0.1]: https://github.com/owkin/connect-backend/releases/tag/0.0.1
