from dagster_externals import init_dagster_ext

context = init_dagster_ext()

context.log(f"Got tickers: {context.extras['tickers']}")
