import pytest
from textual.app import App, ComposeResult


@pytest.mark.asyncio
async def test_gallery_row_height_applied(tmp_path, monkeypatch):
    import shared.paths as p
    monkeypatch.setattr(p, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(p, "CONFIG_FILE", tmp_path / "config.json")
    from tui.widgets.gallery import GalleryRow

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield GalleryRow(widget_height=12)

    async with TestApp().run_test() as pilot:
        row = pilot.app.query_one(GalleryRow)
        assert row.styles.height.value == 12


@pytest.mark.asyncio
async def test_load_widgets_creates_rows(tmp_path, monkeypatch):
    import shared.paths as p
    monkeypatch.setattr(p, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(p, "CONFIG_FILE", tmp_path / "config.json")
    from tui.widgets.gallery import GalleryRow, WidgetGallery
    from tui.widgets.currency_widget import CurrencyWidget

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield WidgetGallery(widget_height=12)

    async with TestApp().run_test() as pilot:
        gallery = pilot.app.query_one(WidgetGallery)
        gallery.load_widgets([
            CurrencyWidget("EUR/USD", "1M", widget_height=12),
            CurrencyWidget("GBP/USD", "1M", widget_height=12),
            CurrencyWidget("USD/JPY", "1M", widget_height=12),
        ])
        await pilot.pause()
        rows = list(gallery.query(GalleryRow))
        assert len(rows) == 2
        assert len(list(rows[0].query(CurrencyWidget))) == 2
        assert len(list(rows[1].query(CurrencyWidget))) == 1
