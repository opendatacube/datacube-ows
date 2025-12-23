import os
from logging import Logger
from threading import Lock

from datacube.utils.aws import configure_s3_access

credential_lock = Lock()


class CredentialManager:
    _instance = None

    def __new__(cls, log: Logger | None = None) -> "CredentialManager":
        # new/init assumed to be called with credential_lock held
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, log: Logger | None = None) -> None:
        # new/init assumed to be called with credential_lock held
        # Startup initialisation of libraries controlled by environment variables
        self.use_aws = False
        self.unsigned = False
        self.requester_pays = False
        self.credentials = None
        self.log = log

        if log:
            log.debug("Initialising CredentialManager")

        # Boto3/AWS
        if os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION"):
            if "AWS_NO_SIGN_REQUEST" in os.environ:
                env_nosign = os.environ["AWS_NO_SIGN_REQUEST"]
                if env_nosign.lower() in ("y", "t", "yes", "true", "1"):
                    unsigned = True
                    # Workaround for rasterio bug
                    os.environ["AWS_NO_SIGN_REQUEST"] = "yes"
                    os.environ["AWS_ACCESS_KEY_ID"] = "fake"
                    os.environ["AWS_SECRET_ACCESS_KEY"] = "fake"
                else:
                    unsigned = False
                    # delete env variable
                    del os.environ["AWS_NO_SIGN_REQUEST"]
            else:
                unsigned = False
                if log:
                    log.warning(
                        "AWS_NO_SIGN_REQUEST is not set. "
                        + "The default behaviour has recently changed to False (i.e. signed requests) "
                        + "Please explicitly set $AWS_NO_SIGN_REQUEST to 'no' for unsigned requests."
                    )
            env_requester_pays = os.environ.get("AWS_REQUEST_PAYER", "")
            requester_pays = False
            if env_requester_pays.lower() == "requester":
                requester_pays = True
            self.use_aws = True
            if log:
                if unsigned:
                    log.info("S3 access configured with unsigned requests")
                else:
                    log.info("S3 access configured with signed requests")
            self.unsigned = unsigned
            self.requester_pays = requester_pays
            self.renew_creds()

            if "AWS_S3_ENDPOINT" in os.environ and os.environ["AWS_S3_ENDPOINT"] == "":
                del os.environ["AWS_S3_ENDPOINT"]
        elif log:
            log.warning(
                "Environment variable $AWS_DEFAULT_REGION not set.  (This warning can be ignored if all data is stored locally.)"
            )

    def _check_cred(self) -> None:
        from botocore.credentials import RefreshableCredentials

        if self.credentials and isinstance(self.credentials, RefreshableCredentials):
            if self.credentials.refresh_needed():
                self.renew_creds()
            elif self.log:
                # pylint: disable=protected-access
                self.log.info(
                    "Credentials look OK: %s seconds remaining",
                    str(self.credentials._seconds_remaining()),
                )
        elif self.log:
            self.log.debug(
                "Credentials of type %s - NOT RENEWING",
                self.credentials.__class__.__name__,
            )

    @classmethod
    def check_cred(cls) -> None:
        # pylint: disable=protected-access
        with credential_lock:
            assert cls._instance is not None
            cls._instance._check_cred()

    def renew_creds(self) -> None:
        if self.use_aws:
            from botocore.credentials import RefreshableCredentials

            if self.log:
                self.log.info("Establishing/renewing credentials")
            self.credentials = configure_s3_access(
                aws_unsigned=self.unsigned, requester_pays=self.requester_pays
            )
            if self.log and isinstance(self.credentials, RefreshableCredentials):
                # pylint: disable=protected-access
                self.log.debug(
                    "%s seconds remaining", str(self.credentials._seconds_remaining())
                )


def initialise_aws_credentials(log: Logger | None = None) -> None:
    # pylint: disable=protected-access
    with credential_lock:
        if CredentialManager._instance is None:
            _ = CredentialManager(log)
