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
    def test_init(self, viz):
        ud = u.UploadData(viz)
        assert isinstance(ud.widgets, ipw.Widget)
        assert ud.image_file_name is None
        assert ud.catalog_file is None

    @pytest.mark.parametrize("allow_reload", [True, False])
    def test_load_image(self, viz, image_file, allow_reload):
        ud = u.UploadData(viz)
        ud.allow_data_replace = allow_reload

        # nothing happens if button does not have new files
        change = {"new": [], "old": [], "owner": ud.image_file_upload}
        ud.load_image(change)
        assert not ud.has_wcs
        assert ud.image_file_name is None
        assert not ud.image_file_upload.disabled

        # mock a file in input widget
        image_name = image_file.name
        with image_file.open("rb") as file:
            file_content = file.read()
        file_info = {"name": image_name, "content": file_content}
        ud.image_file_upload.value = (file_info,)
        change = {"new": [file_info], "old": [], "owner": ud.image_file_upload}
        ud.load_image(change)
        assert ud.has_wcs
        assert ud.image_file_name == image_name

        # viewer has data
        assert image_name in str(ud.viz._app.data_collection)

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
        assert image_name not in str(ud.viz._app.data_collection)

        # when image list is empty, UI upload is not blocked, regardless of setting
        assert not ud.image_file_upload.disabled

    def test_load_image_errors(self, mocker, viz, image_file_no_wcs, bad_catalog_file):
        ud = u.UploadData(viz)

        # mock hub broadcast to check for error messages
        m1 = mocker.patch.object(ud.viz._app.hub, "broadcast")

        # mock the file upload
        image_name = image_file_no_wcs.name
        with image_file_no_wcs.open("rb") as file:
            file_content = file.read()
        file_info = {"name": image_name, "content": file_content}
        ud.image_file_upload.value = (file_info,)
        change = {"new": [file_info], "old": [], "owner": ud.image_file_upload}
        ud.load_image(change)

        # data is displayed, but not stored and marked as has_wcs = False
        assert ud.image_file_name is None
        assert not ud.has_wcs

        # viewer has data
        assert image_name in str(ud.viz._app.data_collection)

        # viewer shows error message
        last_message = m1.call_args_list[-1][0][0]
        assert "No WCS" in last_message.text

        # try uploading something non-FITS - should throw error and
        # not appear in viewer or uploaded data
        image_name = bad_catalog_file.name
        with bad_catalog_file.open("rb") as file:
            bad_file_content = file.read()
        file_info = {"name": image_name, "content": bad_file_content}
        ud.image_file_upload.value = (file_info,)
        change = {"new": [file_info], "old": [], "owner": ud.image_file_upload}
        ud.load_image(change)

        assert ud.image_file_name is None
        assert not ud.has_wcs
        assert image_name not in str(ud.viz._app.data_collection)
        last_message = m1.call_args_list[-1][0][0]
        assert "No valid loaders" in last_message.text

    def test_load_catalog(self, viz, catalog_file):
        ud = u.UploadData(viz)

        # nothing happens if button does not have new files
        change = {"new": [], "old": [], "owner": ud.catalog_file_upload}
        ud.load_catalog(change)
        assert not ud.has_catalog
        assert ud.catalog_file is None
        assert not ud.image_file_upload.disabled

        # mock a file in input widget
        cat_name = catalog_file.name
        with catalog_file.open("rb") as file:
            catalog_file_content = file.read()
        file_info = {"name": cat_name, "content": catalog_file_content}
        ud.catalog_file_upload.value = (file_info,)
        change = {"new": [file_info], "old": [], "owner": ud.catalog_file_upload}
        ud.load_catalog(change)
        assert ud.has_catalog
        assert ud.catalog_file["name"] == cat_name

        # remove the file
        change = {"new": [], "old": [file_info], "owner": ud.catalog_file_upload}
        ud.load_catalog(change)
        assert not ud.has_catalog
        assert ud.catalog_file is None

    def test_upload_config(self, viz, config_file):
        ud = u.UploadData(viz, allow_configuration=True)
        assert ud.config_file_upload is not None
        assert len(ud.configuration) == 0

        # bad config file - nothing happens
        file_info = {"name": "bad", "content": b"bad"}
        ud.catalog_file_upload.value = (file_info,)
        change = {"new": [file_info], "old": [], "owner": ud.catalog_file_upload}
        ud.load_config(change)
        assert len(ud.configuration) == 0

        # upload a good config file
        cfg_name = config_file.name
        with config_file.open("rb") as fh:
            file_info = {"name": cfg_name, "content": fh.read()}
            ud.catalog_file_upload.value = (file_info,)
            change = {"new": [file_info], "old": [], "owner": ud.catalog_file_upload}
            ud.load_config(change)

        # config dict is now in the configuration attribute
        assert len(ud.configuration) > 0
        assert ud.configuration["catalog"]["color_primary"] == "orange"
