from agents.tools import search_web


class FakeResponse:
    def __init__(self, text, status_code=200):
        self._text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("request failed")

    @property
    def text(self):
        return self._text


def test_search_web_parses_results(monkeypatch):
    html = """
    <html>
      <body>
        <a rel="nofollow" class="result__a" href="https://example.com/one">Example One</a>
        <a class="result__snippet">First snippet</a>
        <a rel="nofollow" class="result__a" href="https://example.com/two">Example Two</a>
        <a class="result__snippet">Second snippet</a>
      </body>
    </html>
    """

    def fake_get(*args, **kwargs):
        return FakeResponse(html)

    monkeypatch.setattr("agents.tools.requests.get", fake_get)

    results = search_web("portfolio research", max_results=2)

    assert len(results) == 2
    assert results[0]["title"] == "Example One"
    assert results[0]["url"] == "https://example.com/one"
    assert results[0]["snippet"] == "First snippet"
