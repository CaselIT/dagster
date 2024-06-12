import multiprocessing

import pytest
from dagster._core.test_utils import environ
from dagster._utils.test import copy_directory
from dagster_dbt.dbt_manifest import validate_manifest
from dagster_dbt.dbt_project import DbtProject
from dagster_dbt.errors import DagsterDbtManifestNotFoundError

from ..dbt_projects import test_jaffle_shop_path


@pytest.fixture(scope="session")
def shared_project_dir():
    with copy_directory(test_jaffle_shop_path) as project_dir:
        yield project_dir


@pytest.fixture(scope="function")
def project_dir(shared_project_dir):
    manifest_path = DbtProject(shared_project_dir).prepared().manifest_path
    if manifest_path.exists():
        manifest_path.unlink()
    yield shared_project_dir


def test_local_dev(project_dir) -> None:
    my_project = DbtProject(project_dir)
    assert not my_project.manifest_path.exists()
    with pytest.raises(DagsterDbtManifestNotFoundError):
        # The preparation process will fail locally
        # if no env var are provided and the manifest does not exist
        DbtProject(project_dir).prepared()
    with environ({"DAGSTER_IS_DEV_CLI": "1"}):
        my_project = DbtProject(project_dir).prepared()
        assert my_project.manifest_path.exists()


def test_opt_in_env_var(project_dir) -> None:
    my_project = DbtProject(project_dir)
    assert not my_project.manifest_path.exists()
    with pytest.raises(DagsterDbtManifestNotFoundError):
        # The preparation process will fail locally
        # if no env var are provided and the manifest does not exist
        DbtProject(project_dir).prepared()
    with environ({"DAGSTER_DBT_PARSE_PROJECT_ON_LOAD": "1"}):
        my_project = DbtProject(project_dir).prepared()
        assert my_project.manifest_path.exists()


def _init(project_dir):
    my_project = DbtProject(project_dir).prepared()
    assert my_project.manifest_path.exists()
    assert validate_manifest(my_project.manifest_path)
    return


def test_concurrent_processes(project_dir):
    my_project = DbtProject(project_dir)
    assert not my_project.manifest_path.exists()
    with pytest.raises(DagsterDbtManifestNotFoundError):
        # The preparation process will fail locally
        # if no env var are provided and the manifest does not exist
        DbtProject(project_dir).prepared()
    with environ({"DAGSTER_IS_DEV_CLI": "1"}):
        procs = [multiprocessing.Process(target=_init, args=(project_dir,)) for _ in range(4)]
        for proc in procs:
            proc.start()

        for proc in procs:
            proc.join(timeout=30)
            assert proc.exitcode == 0

        assert my_project.manifest_path.exists()
