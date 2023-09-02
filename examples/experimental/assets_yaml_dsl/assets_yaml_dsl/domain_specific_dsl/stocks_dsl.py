import os
import shutil
from typing import Any, Dict, List, NamedTuple

import yaml
from dagster._core.execution.context.compute import AssetExecutionContext

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from dagster import AssetKey, AssetsDefinition, asset, file_relative_path, multi_asset
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.external_execution.subprocess import ExtSubprocess


def load_yaml(relative_path: str) -> Dict[str, Any]:
    path = os.path.join(os.path.dirname(__file__), relative_path)
    with open(path, "r", encoding="utf8") as ff:
        return yaml.load(ff, Loader=Loader)


def get_ticker_data(ticker: str) -> str:
    # imagine instead of returning a string, this function fetches data from an external service
    return f"{ticker}-data"


def enrich_and_insert_data(ticker_data) -> None:
    # imagine this modifies the data and inserts it into ouj database
    pass


def fetch_data_for_ticker(ticker: str) -> str:
    # imagine this fetches data from our database
    return f"{ticker}-data-enriched"


class StockInfo(NamedTuple):
    ticker: str


class IndexStrategy(NamedTuple):
    type: str


class Forecast(NamedTuple):
    days: int


class StockAssets(NamedTuple):
    stock_infos: List[StockInfo]
    index_strategy: IndexStrategy
    forecast: Forecast


def build_stock_assets_object(stocks_dsl_document: Dict[str, Dict]) -> StockAssets:
    return StockAssets(
        stock_infos=[
            StockInfo(ticker=stock_block["ticker"])
            for stock_block in stocks_dsl_document["stocks_to_index"]
        ],
        index_strategy=IndexStrategy(type=stocks_dsl_document["index_strategy"]["type"]),
        forecast=Forecast(int(stocks_dsl_document["forecast"]["days"])),
    )


def get_stocks_dsl_example_defs() -> List[AssetsDefinition]:
    stocks_dsl_document = load_yaml("stocks.yaml")
    stock_assets = build_stock_assets_object(stocks_dsl_document)
    return assets_defs_from_stock_assets(stock_assets)


def assets_defs_from_stock_assets(stock_assets: StockAssets) -> List[AssetsDefinition]:
    group_name = "stocks"

    def spec_for_stock_info(stock_info: StockInfo) -> AssetSpec:
        ticker = stock_info.ticker
        return AssetSpec(
            asset_key=AssetKey(ticker),
            group_name=group_name,
            description=f"Fetch {ticker} from internal service",
        )

    tickers = [stock_info.ticker for stock_info in stock_assets.stock_infos]
    ticker_specs = [spec_for_stock_info(stock_info) for stock_info in stock_assets.stock_infos]

    @multi_asset(specs=ticker_specs)
    def fetch_the_tickers(context: AssetExecutionContext, ext_subprocess: ExtSubprocess):
        python_executable = shutil.which("python")
        assert python_executable is not None
        script_path = file_relative_path(__file__, "user_scripts/fetch_the_tickers.py")
        ext_subprocess.run(
            command=[python_executable, script_path], context=context, extras={"tickers": tickers}
        )

    @asset(deps=fetch_the_tickers.keys, group_name=group_name)
    def index_strategy() -> None:
        stored_ticker_data = {}
        for ticker in tickers:
            stored_ticker_data[ticker] = fetch_data_for_ticker(ticker)

        # do someting with stored_ticker_data

    @asset(deps=fetch_the_tickers.keys, group_name=group_name)
    def forecast() -> None:
        # do some forecast thing
        pass

    return [fetch_the_tickers, index_strategy, forecast]
