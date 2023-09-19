import pytest
from dagster import (
    AssetKey,
    AssetsDefinition,
    AutoMaterializePolicy,
    DagsterInstance,
    DataVersion,
    Definitions,
    IOManager,
    SourceAsset,
    _check as check,
    asset,
    observable_source_asset,
)
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.observable_asset import (
    create_assets_def_from_source_asset,
    create_unexecutable_observable_assets_def,
)


def test_observable_asset_basic_creation() -> None:
    assets_def = create_unexecutable_observable_assets_def(
        specs=[
            AssetSpec(
                key="observable_asset_one",
                # multi-asset does not support description lol
                # description="desc",
                metadata={"user_metadata": "value"},
                group_name="a_group",
            )
        ]
    )
    assert isinstance(assets_def, AssetsDefinition)

    expected_key = AssetKey(["observable_asset_one"])

    assert assets_def.key == expected_key
    # assert assets_def.descriptions_by_key[expected_key] == "desc"
    assert assets_def.metadata_by_key[expected_key]["user_metadata"] == "value"
    assert assets_def.group_names_by_key[expected_key] == "a_group"
    assert assets_def.is_asset_executable(expected_key) is False


def test_invalid_observable_asset_creation() -> None:
    invalid_specs = [
        AssetSpec("invalid_asset1", auto_materialize_policy=AutoMaterializePolicy.eager()),
        AssetSpec("invalid_asset2", code_version="ksjdfljs"),
        AssetSpec("invalid_asset2", freshness_policy=FreshnessPolicy(maximum_lag_minutes=1)),
        AssetSpec("invalid_asset2", skippable=True),
    ]

    for invalid_spec in invalid_specs:
        with pytest.raises(check.CheckError):
            create_unexecutable_observable_assets_def(specs=[invalid_spec])


def test_normal_asset_materializeable() -> None:
    @asset
    def an_asset() -> None: ...

    assert an_asset.is_asset_executable(AssetKey(["an_asset"])) is True


def test_observable_asset_creation_with_deps() -> None:
    asset_two = AssetSpec("observable_asset_two")
    assets_def = create_unexecutable_observable_assets_def(
        specs=[
            AssetSpec(
                "observable_asset_one",
                deps=[asset_two.key],  # todo remove key when asset deps accepts it
            )
        ]
    )
    assert isinstance(assets_def, AssetsDefinition)

    expected_key = AssetKey(["observable_asset_one"])

    assert assets_def.key == expected_key
    assert assets_def.asset_deps[expected_key] == {
        AssetKey(["observable_asset_two"]),
    }


def test_how_source_assets_are_backwards_compatible() -> None:
    class DummyIOManager(IOManager):
        def handle_output(self, context, obj) -> None:
            pass

        def load_input(self, context) -> str:
            return "hardcoded"

    source_asset = SourceAsset(key="source_asset", io_manager_def=DummyIOManager())

    @asset
    def an_asset(source_asset: str) -> str:
        return "hardcoded" + "-computed"

    defs_with_source = Definitions(assets=[source_asset, an_asset])

    instance = DagsterInstance.ephemeral()

    result_one = defs_with_source.get_implicit_global_asset_job_def().execute_in_process(
        instance=instance
    )

    assert result_one.success
    assert result_one.output_for_node("an_asset") == "hardcoded-computed"

    defs_with_shim = Definitions(
        assets=[create_assets_def_from_source_asset(source_asset), an_asset]
    )

    assert isinstance(defs_with_shim.get_assets_def("source_asset"), AssetsDefinition)

    result_two = defs_with_shim.get_implicit_global_asset_job_def().execute_in_process(
        instance=instance,
        # currently we have to explicitly select the asset to exclude the source from execution
        asset_selection=[AssetKey("an_asset")],
    )

    assert result_two.success
    assert result_two.output_for_node("an_asset") == "hardcoded-computed"


def test_observable_source_asset_decorator() -> None:
    @observable_source_asset
    def an_observable_source_asset() -> DataVersion:
        return DataVersion("foo")

    defs = Definitions(assets=[create_assets_def_from_source_asset(an_observable_source_asset)])

    result = defs.get_implicit_global_asset_job_def().execute_in_process()

    assert result.success

    all_observations = result.get_asset_observation_events()
    assert len(all_observations) == 1
    observation_event = all_observations[0]
    assert observation_event.asset_observation_data.asset_observation.data_version == "foo"

    all_materializations = result.get_asset_materialization_events()
    # Note this does not make sense. We need to make framework changes to allow for the omission of
    # a materialzation event
    assert len(all_materializations) == 1
