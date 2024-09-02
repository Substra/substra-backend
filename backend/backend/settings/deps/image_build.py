import os

# How long we wait before throwing errors, in seconds
IMAGE_BUILD_TIMEOUT = int(os.getenv("IMAGE_BUILD_TIMEOUT", 60 * 60))  # 1 hour
# Delay before two check
IMAGE_BUILD_CHECK_DELAY = 5
BUILDER_KANIKO_STARTUP_MAX_ATTEMPTS = int(os.getenv("BUILDER_KANIKO_STARTUP_MAX_ATTEMPTS", 60))
BUILDER_KANIKO_STARTUP_PENDING_STATE_WAIT_SECONDS = int(
    os.getenv("BUILDER_KANIKO_STARTUP_PENDING_STATE_WAIT_SECONDS", 2)
)
