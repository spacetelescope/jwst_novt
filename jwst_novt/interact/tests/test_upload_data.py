import pytest

try:
    import ipywidgets as ipw

    from jwst_novt.interact import upload_data as u
except ImportError:
    ipw = None
    u = None
    HAS_DISPLAY = False
else:
    HAS_DISPLAY = True


@pytest.mark.skipif(not HAS_DISPLAY, reason="Missing optional dependencies")
class TestUploadData:
    def test_init(self, imviz):
        ud = u.UploadData(imviz)
        assert isinstance(ud.widgets, ipw.Widget)
        assert ud.image_file_name is None
        assert ud.catalog_file is None

    @pytest.mark.parametrize("allow_reload", [True, False])
    def test_load_image(self, mocker, imviz, image_file, allow_reload):
        ud = u.UploadData(imviz)
        ud.allow_data_replace = allow_reload

        # nothing happens if button does not have new files
        change = {"new": [], "old": [], "owner": ud.image_file_upload}
        ud.load_image(change)
        assert not ud.has_wcs
        assert ud.image_file_name is None
        assert not ud.image_file_upload.disabled

        # mock a file in input widget
        image_name = image_file.name
        file_info = {"name": image_name, "file_obj": str(image_file)}
        mocker.patch.object(ud.image_file_upload, "get_files", return_value=[file_info])
        change = {"new": [file_info], "old": [], "owner": ud.image_file_upload}
        ud.load_image(change)
        assert ud.has_wcs
        assert ud.image_file_name == image_name

        # viewer has data
        assert image_name in str(ud.viz.app.data_collection)

        # changing the image via the UI is blocked if necessary
        if allow_reload:
            assert not ud.image_file_upload.disabled
        else:
            assert ud.image_file_upload.disabled

        # remove the file
        change = {"new": [], "old": [file_info], "owner": ud.image_file_upload}
        ud.load_image(change)
        assert not ud.has_wcs
        assert ud.image_file_name is None

        # viewer no longer has data
        assert image_name not in str(ud.viz.app.data_collection)

        # when image list is empty, UI upload is not blocked, regardless of setting
        assert not ud.image_file_upload.disabled

    def test_load_image_errors(
        self, mocker, imviz, image_file_no_wcs, bad_catalog_file
    ):
        ud = u.UploadData(imviz)

        # mock hub broadcast to check for error messages
        m1 = mocker.patch.object(ud.viz.app.hub, "broadcast")
        base_count = 12  # normal messages broadcast on load

        # mock the file upload
        image_name = image_file_no_wcs.name
        file_info = {"name": image_name, "file_obj": str(image_file_no_wcs)}
        mocker.patch.object(ud.image_file_upload, "get_files", return_value=[file_info])
        change = {"new": [file_info], "old": [], "owner": ud.image_file_upload}
        ud.load_image(change)

        # data is displayed, but not stored and marked as has_wcs = False
        assert ud.image_file_name is None
        assert not ud.has_wcs

        # viewer has data
        assert image_name in str(ud.viz.app.data_collection)

        # viewer shows error message
        assert m1.call_count == base_count + 1

        # try uploading something non-FITS - should throw error and
        # not appear in viewer or uploaded data
        image_name = bad_catalog_file.name
        file_info = {"name": image_name, "file_obj": str(bad_catalog_file)}
        mocker.patch.object(ud.image_file_upload, "get_files", return_value=[file_info])
        change = {"new": [file_info], "old": [], "owner": ud.image_file_upload}
        ud.load_image(change)

        assert ud.image_file_name is None
        assert not ud.has_wcs
        assert image_name not in str(ud.viz.app.data_collection)
        assert m1.call_count == base_count + 2

    def test_load_catalog(self, mocker, imviz, catalog_file):
        ud = u.UploadData(imviz)

        # nothing happens if button does not have new files
        change = {"new": [], "old": [], "owner": ud.catalog_file_upload}
        ud.load_catalog(change)
        assert not ud.has_catalog
        assert ud.catalog_file is None
        assert not ud.image_file_upload.disabled

        # mock a file in input widget
        cat_name = catalog_file.name
        file_info = {"name": cat_name, "file_obj": str(catalog_file)}
        mocker.patch.object(
            ud.catalog_file_upload, "get_files", return_value=[file_info]
        )
        change = {"new": [file_info], "old": [], "owner": ud.catalog_file_upload}
        ud.load_catalog(change)
        assert ud.has_catalog
        assert ud.catalog_file["name"] == cat_name

        # remove the file
        change = {"new": [], "old": [file_info], "owner": ud.catalog_file_upload}
        ud.load_catalog(change)
        assert not ud.has_catalog
        assert ud.catalog_file is None

    def test_upload_config(self, mocker, imviz, config_file):
        ud = u.UploadData(imviz, allow_configuration=True)
        assert ud.config_file_upload is not None
        assert len(ud.configuration) == 0

        # bad config file - nothing happens
        file_info = {"name": "bad", "file_obj": "bad"}
        mocker.patch.object(
            ud.catalog_file_upload, "get_files", return_value=[file_info]
        )
        change = {"new": [file_info], "old": [], "owner": ud.catalog_file_upload}
        ud.load_config(change)
        assert len(ud.configuration) == 0

        # upload a good config file
        cfg_name = config_file.name
        with config_file.open() as fh:
            file_info = {"name": cfg_name, "file_obj": fh}
            mocker.patch.object(
                ud.catalog_file_upload, "get_files", return_value=[file_info]
            )
            change = {"new": [file_info], "old": [], "owner": ud.catalog_file_upload}
            ud.load_config(change)

        # config dict is now in the configuration attribute
        assert len(ud.configuration) > 0
        assert ud.configuration["catalog"]["color_primary"] == "orange"
