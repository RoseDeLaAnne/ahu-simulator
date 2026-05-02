from app.ui.scene.model_catalog import build_scene_model_catalog


def test_scene_model_catalog_discovers_glb_assets() -> None:
    catalog = build_scene_model_catalog()

    assert catalog.default_model_id is not None
    assert len(catalog.models) >= 3
    assert any(model.id == catalog.default_model_id for model in catalog.models)


def test_scene_model_catalog_exposes_static_urls() -> None:
    catalog = build_scene_model_catalog()
    featured = next(model for model in catalog.models if model.featured)

    assert featured.model_url.startswith("/models/")
    assert featured.model_path.endswith(".glb")
    assert featured.preview_url is not None
    assert featured.preview_url.startswith("/images-of-models/")
    assert featured.profile
    assert "anchors" in featured.profile
    assert "camera" in featured.profile


def test_scene_model_catalog_hides_duplicate_installation_exports() -> None:
    catalog = build_scene_model_catalog()
    model_ids = {model.id for model in catalog.models}

    assert "base_classic" in model_ids
    assert "base_variant_a" not in model_ids


def test_scene_model_catalog_uses_new_folder_models_for_master_and_variant_c() -> None:
    catalog = build_scene_model_catalog()
    models_by_id = {model.id: model for model in catalog.models}

    assert "modular_ahu" in models_by_id
    assert models_by_id["modular_ahu"].model_path.startswith("models/ahu/master/")
    assert "base_variant_c" in models_by_id
    assert models_by_id["base_variant_c"].model_path.startswith("models/ahu/variants/")
