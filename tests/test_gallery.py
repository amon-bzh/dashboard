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
