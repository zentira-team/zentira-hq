"""Unit test offline untuk konfigurasi dan Agent 1 (Riset Tren)."""

from __future__ import annotations

import unittest

from agents.trend_researcher.agent import (
    StoryIdea,
    TrendAnalysisOutput,
    TrendResearcherAgent,
)
from agents.trend_researcher.fetcher import (
    TrendFetchError,
    TrendItem,
    parse_trends_rss,
)
from core.config import ConfigError, load_settings
from core.gemini_client import GeminiClient, GeminiClientError

SAMPLE_RSS_HTTPS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<rss xmlns:atom="http://www.w3.org/2005/Atom" xmlns:ht="https://trends.google.com/trending/rss" version="2.0">
  <channel>
    <title>Daily Search Trends</title>
    <item>
      <title>kopi susu viral</title>
      <ht:approx_traffic>5000+</ht:approx_traffic>
      <pubDate>Fri, 20 Nov 2026 09:50:00 -0800</pubDate>
      <ht:news_item>
        <ht:news_item_title>Tren Kopi Susu Gula Aren Baru Bikin Antre Panjang</ht:news_item_title>
        <ht:news_item_source>Kompas</ht:news_item_source>
        <ht:news_item_url>https://example.com/kopi-1</ht:news_item_url>
      </ht:news_item>
      <ht:news_item>
        <ht:news_item_title>Anak Muda Rela Antre Demi Gelas Unik</ht:news_item_title>
        <ht:news_item_source>Detik</ht:news_item_source>
        <ht:news_item_url>https://example.com/kopi-2</ht:news_item_url>
      </ht:news_item>
    </item>
    <item>
      <title>gaji UMR naik</title>
      <ht:approx_traffic>10000+</ht:approx_traffic>
      <pubDate>Fri, 20 Nov 2026 08:00:00 -0800</pubDate>
    </item>
  </channel>
</rss>
"""

SAMPLE_RSS_HTTP_AND_DUPLICATE = """<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:ht="http://trends.google.com/trending/rss" version="2.0">
  <channel>
    <item>
      <title>Hujan Deras</title>
      <ht:approx_traffic>2000+</ht:approx_traffic>
    </item>
    <item>
      <title>hujan deras</title>
      <ht:approx_traffic>1000+</ht:approx_traffic>
    </item>
    <item>
      <title>Diskon Tanggal Kembar</title>
      <ht:approx_traffic>500+</ht:approx_traffic>
    </item>
    <item>
      <title>Kucing Oren</title>
      <ht:approx_traffic>300+</ht:approx_traffic>
    </item>
  </channel>
</rss>
"""


class FakeGeminiClient:
    """Mock GeminiClient untuk menguji orkestrasi Agent 1 tanpa API call."""

    def __init__(self, ideas_count: int = 5) -> None:
        self.calls: list[dict[str, str]] = []
        self.ideas_count = ideas_count

    def generate_structured(
        self,
        prompt: str,
        response_schema: type[TrendAnalysisOutput],
        system_instruction: str | None = None,
        temperature: float = 0.7,
    ) -> TrendAnalysisOutput:
        self.calls.append(
            {
                "prompt": prompt,
                "system_instruction": system_instruction or "",
            }
        )
        ideas = [
            StoryIdea(
                judul_ide=f"Ide Cerita #{i}",
                tren_sumber="kopi susu viral",
                alasan_dipilih="Relatable dengan gaya hidup anak muda.",
                sudut_pandang_cerita="Denn santai tapi overthinking soal harga kopi, Miki heboh bandingin sama cicilan.",
                hook_3_detik="Miki masuk frame bawa struk panjang: 'Den, ini beli kopi apa bayar kosan?!'",
                estimasi_durasi="45 detik",
            )
            for i in range(1, self.ideas_count + 1)
        ]
        return TrendAnalysisOutput(
            ringkasan_filter="2 tren dipilih, topik sensitif dilewati.",
            ide_cerita=ideas,
        )


class TestConfig(unittest.TestCase):
    def test_load_settings_rejects_empty_or_placeholder_key(self) -> None:
        with self.assertRaises(ConfigError):
            load_settings(
                require_gemini_key=True,
                load_dotenv_file=False,
                environ={"GEMINI_API_KEY": ""},
            )

        with self.assertRaises(ConfigError):
            load_settings(
                require_gemini_key=True,
                load_dotenv_file=False,
                environ={"GEMINI_API_KEY": "masukkan_api_key_gemini_anda_di_sini"},
            )

    def test_load_settings_allows_missing_key_when_not_required(self) -> None:
        settings = load_settings(
            require_gemini_key=False,
            load_dotenv_file=False,
            environ={"TRENDS_MAX_IDEAS": "10", "TRENDS_GEO": "id"},
        )
        self.assertEqual(settings.trends_geo, "ID")
        self.assertEqual(settings.trends_max_ideas, 3)
        self.assertEqual(settings.gemini_model, "gemini-3.5-flash")
        self.assertEqual(
            settings.gemini_fallback_models, ("gemini-3.5-flash-lite", "gemini-3.8-flash")
        )

    def test_load_settings_parses_fallback_models_and_none(self) -> None:
        custom = load_settings(
            require_gemini_key=False,
            load_dotenv_file=False,
            environ={"GEMINI_FALLBACK_MODELS": "gemini-3.8-flash, gemini-3.5-flash"},
        )
        self.assertEqual(
            custom.gemini_fallback_models, ("gemini-3.8-flash", "gemini-3.5-flash")
        )

        disabled = load_settings(
            require_gemini_key=False,
            load_dotenv_file=False,
            environ={"GEMINI_FALLBACK_MODELS": "none"},
        )
        self.assertEqual(disabled.gemini_fallback_models, ())


class _FakeModelsAPI:
    def __init__(self, handler) -> None:
        self._handler = handler
        self.called_models: list[str] = []

    def generate_content(self, model: str, contents: str, config: object):
        self.called_models.append(model)
        return self._handler(model)


class _FakeRawClient:
    def __init__(self, handler) -> None:
        self.models = _FakeModelsAPI(handler)


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text
        self.parsed = None


class TestGeminiClientFallback(unittest.TestCase):
    def test_fallback_on_503_unavailable(self) -> None:
        def handler(model: str) -> _FakeResponse:
            if model == "gemini-3.5-flash":
                raise RuntimeError("503 UNAVAILABLE: high demand")
            return _FakeResponse("OK")

        raw = _FakeRawClient(handler)
        client = GeminiClient(
            api_key="dummy-key",
            model="gemini-3.5-flash",
            fallback_models=("gemini-3.8-flash",),
            client=raw,
        )
        self.assertEqual(client.generate_text("tes"), "OK")
        self.assertEqual(
            raw.models.called_models, ["gemini-3.5-flash", "gemini-3.8-flash"]
        )
        self.assertEqual(client.last_used_model, "gemini-3.8-flash")

    def test_does_not_fallback_on_401_unauthenticated(self) -> None:
        def handler(model: str) -> _FakeResponse:
            raise RuntimeError("401 UNAUTHENTICATED: API key not valid")

        raw = _FakeRawClient(handler)
        client = GeminiClient(
            api_key="dummy-key",
            model="gemini-3.5-flash",
            fallback_models=("gemini-3.8-flash",),
            client=raw,
        )
        with self.assertRaises(GeminiClientError):
            client.generate_text("tes")
        self.assertEqual(raw.models.called_models, ["gemini-3.5-flash"])

    def test_automatic_failover_from_gemini_503_to_groq_structured(self) -> None:
        def gemini_503(model: str) -> _FakeResponse:
            raise RuntimeError("503 UNAVAILABLE: high demand")

        groq_calls: list[dict] = []

        class _FakeHTTPResponse:
            def __init__(self, status_code: int, payload: dict) -> None:
                self.status_code = status_code
                self._payload = payload
                self.text = str(payload)

            def json(self) -> dict:
                return self._payload

        def fake_groq_post(url: str, headers: dict, json: dict, timeout: float):
            groq_calls.append({"url": url, "model": json["model"], "format": json.get("response_format")})
            return _FakeHTTPResponse(
                200,
                {
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    '```json\n'
                                    '{"ringkasan_filter": "Dipilih via Groq.", "ide_cerita": ['
                                    '{"judul_ide": "Kopi Viral", "tren_sumber": "kopi", '
                                    '"alasan_dipilih": "Relatable", '
                                    '"sudut_pandang_cerita": "Denn bingung harga kopi, Miki ketawa.", '
                                    '"hook_3_detik": "Kopi segelas seharga bensin?!", '
                                    '"estimasi_durasi": "40 detik"}]}\n'
                                    '```'
                                )
                            }
                        }
                    ]
                },
            )

        raw = _FakeRawClient(gemini_503)
        client = GeminiClient(
            api_key="dummy-gemini",
            model="gemini-3.5-flash",
            fallback_models=("gemini-3.5-flash-lite",),
            client=raw,
            groq_api_key="gsk_dummy_test",
            groq_model="llama-3.3-70b-versatile",
            primary_provider="gemini",
            groq_http_post=fake_groq_post,
        )

        result = client.generate_structured("buat ide", TrendAnalysisOutput)
        self.assertEqual(raw.models.called_models, ["gemini-3.5-flash", "gemini-3.5-flash-lite"])
        self.assertEqual(len(groq_calls), 1)
        self.assertEqual(groq_calls[0]["model"], "llama-3.3-70b-versatile")
        self.assertEqual(groq_calls[0]["format"], {"type": "json_object"})
        self.assertEqual(client.last_used_provider, "groq")
        self.assertEqual(client.last_used_model, "groq:llama-3.3-70b-versatile")
        self.assertEqual(result.ide_cerita[0].judul_ide, "Kopi Viral")

    def test_load_settings_accepts_groq_only_key(self) -> None:
        settings = load_settings(
            require_gemini_key=True,
            load_dotenv_file=False,
            environ={"GROQ_API_KEY": "gsk_valid_sample", "AI_PRIMARY_PROVIDER": "gemini"},
        )
        self.assertEqual(settings.gemini_api_key, "")
        self.assertEqual(settings.groq_api_key, "gsk_valid_sample")
        self.assertEqual(settings.groq_model, "openai/gpt-oss-120b")
        self.assertEqual(settings.ai_primary_provider, "gemini")


class TestTrendFetcher(unittest.TestCase):
    def test_parse_trends_rss_https_namespace(self) -> None:
        items = parse_trends_rss(SAMPLE_RSS_HTTPS, max_items=10)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].title, "kopi susu viral")
        self.assertEqual(items[0].approx_traffic, "5000+")
        self.assertEqual(len(items[0].news_items), 2)
        self.assertEqual(items[0].news_items[0].source, "Kompas")

    def test_parse_trends_rss_http_namespace_deduplicates_and_limits(self) -> None:
        items = parse_trends_rss(SAMPLE_RSS_HTTP_AND_DUPLICATE, max_items=2)
        self.assertEqual(len(items), 2)
        self.assertEqual([item.title for item in items], ["Hujan Deras", "Diskon Tanggal Kembar"])

    def test_parse_trends_rss_invalid_xml_raises(self) -> None:
        with self.assertRaises(TrendFetchError):
            parse_trends_rss("<rss><broken>")


class TestTrendResearcherAgent(unittest.TestCase):
    def test_agent_caps_ideas_at_three_and_uses_character_profile(self) -> None:
        fake_client = FakeGeminiClient(ideas_count=5)
        sample_trends = [
            TrendItem(title="kopi susu viral", approx_traffic="5000+"),
            TrendItem(title="diskon tanggal kembar", approx_traffic="2000+"),
        ]
        agent = TrendResearcherAgent(
            gemini_client=fake_client,  # type: ignore[arg-type]
            geo="ID",
            max_items=20,
            max_ideas=3,
            fetcher=lambda _geo, _max_items: sample_trends,
        )

        report = agent.run()
        self.assertEqual(len(report.ide_cerita), 3)
        self.assertEqual(report.total_tren_dipindai, 2)
        self.assertEqual(len(fake_client.calls), 1)
        self.assertIn("Denn", fake_client.calls[0]["system_instruction"])
        self.assertIn("Miki", fake_client.calls[0]["system_instruction"])

        formatted = agent.format_report(report)
        self.assertIn("Hook 3 Detik Pertama", formatted)
        self.assertIn("Sudut Pandang Cerita (Denn & Miki)", formatted)

    def test_agent_handles_empty_trends_without_calling_gemini(self) -> None:
        fake_client = FakeGeminiClient(ideas_count=3)
        agent = TrendResearcherAgent(
            gemini_client=fake_client,  # type: ignore[arg-type]
            fetcher=lambda _geo, _max_items: [],
        )

        report = agent.run()
        self.assertEqual(report.total_tren_dipindai, 0)
        self.assertEqual(report.ide_cerita, [])
        self.assertEqual(len(fake_client.calls), 0)


if __name__ == "__main__":
    unittest.main()
