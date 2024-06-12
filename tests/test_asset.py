"""Tests for Logseq asset files."""

from pathlib import Path

from rgb_logseq.asset import Asset


def test_asset_creation(asset_path: Path):
    asset = Asset(path=asset_path)

    assert asset.path == asset_path
    assert asset.name == asset_path.stem
