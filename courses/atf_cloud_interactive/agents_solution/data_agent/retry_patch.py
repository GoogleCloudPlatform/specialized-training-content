from google.genai.types import HttpRetryOptions

retry_options=HttpRetryOptions(
    initial_delay=2,
    attempts=5,
    max_delay=16,
    jitter=2.0,
)

class Gemini3(Gemini):
    """Gemini subclass that forces location='global' for Gemini 3 models."""

    @cached_property
    def api_client(self) -> Client:
        return Client(
            project=os.environ["GOOGLE_CLOUD_PROJECT"],
            location="global",
            http_options=types.HttpOptions(
                headers=self._tracking_headers(),
                retry_options=retry_options,
            ),
        )