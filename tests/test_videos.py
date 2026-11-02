import urllib.error

import pytest

from obi.content import load_content
from obi.videos import Status, check_all, check_video, report


class _Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _opener_failing_with(code):
    def opener(url, timeout):
        raise urllib.error.HTTPError(url, code, "error", {}, None)

    return opener


@pytest.mark.parametrize(
    ("code", "status"),
    [
        (401, Status.NOT_EMBEDDABLE),
        (403, Status.NOT_EMBEDDABLE),
        (404, Status.UNAVAILABLE),
        (400, Status.UNAVAILABLE),
        (500, Status.UNKNOWN),
    ],
)
def test_http_errors_map_to_a_status(code, status):
    assert check_video("AAAAAAAAAAA", opener=_opener_failing_with(code)) is status


def test_ok_and_network_failure():
    assert check_video("AAAAAAAAAAA", opener=lambda url, timeout: _Response()) is Status.OK

    def offline(url, timeout):
        raise urllib.error.URLError("no network")

    assert check_video("AAAAAAAAAAA", opener=offline) is Status.UNKNOWN


def test_report_lists_only_problems(write_data, data):
    content = load_content(write_data(data))
    statuses = {"BBBBBBBBBBB": Status.UNAVAILABLE}
    results = check_all(content, check=lambda youtube: statuses.get(youtube, Status.OK))

    assert [r.video.youtube for r in results if r.broken] == ["BBBBBBBBBBB"]
    text = report(results)
    assert "1 of 3 videos have a problem." in text
    assert (
        "| o-soto-gari | [A video](https://www.youtube.com/watch?v=BBBBBBBBBBB&t=12s) | yes |"
        in text
    )
