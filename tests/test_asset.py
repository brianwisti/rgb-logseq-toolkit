"""Tests for Logseq asset files."""

from pathlib import PurePosixPath

from rgb_logseq.asset import Asset


def test_asset_creation(asset_path: PurePosixPath):
    asset = Asset(path=asset_path)

    assert asset.path == asset_path
    assert asset.name == f"../assets/{asset_path.name}"


class TestAssetFileHandling:
    def test_asset_does_not_exist(self, asset_path: PurePosixPath):
        asset = Asset(path=asset_path)

        assert not asset.exists

    def test_asset_exists(self, asset_path: PurePosixPath, fs):
        fs.create_file(asset_path)
        asset = Asset(path=asset_path)

        assert asset.exists
