from datetime import datetime, timedelta

from assets.assets_provider import AssetsProvider
from entities.timespan import TimeSpan
from pipeline.processors.candle_cache import CandleCache
from pipeline.processors.strategy import StrategyProcessor
from pipeline.processors.technicals import TechnicalsProcessor
from pipeline.processors.technicals_buckets_matcher import TechnicalsBucketsMatcher
from pipeline.processors.technicals_normalizer import TechnicalsNormalizerProcessor
from pipeline.runner import PipelineRunner
from pipeline.sources.mongodb_source import MongoDBSource
from pipeline.strategies.connors_rsi2 import ConnorsRSI2
from pipeline.strategies.history_bucket_compare import HistoryBucketCompareStrategy
from pipeline.strategies.history_cosine_similarity import HistoryCosineSimilarityStrategy
from storage.mongodb_storage import MongoDBStorage
from trade.simple_sum_signals_executor import SimpleSumSignalsExecutor


class BacktestPipelines:
    @staticmethod
    def build_mongodb_backtester() -> PipelineRunner:
        mongodb_storage = MongoDBStorage()
        symbols = AssetsProvider.get_sp500_symbols()

        from_time = datetime.now() - timedelta(days=365 * 2)
        source = MongoDBSource(mongodb_storage, symbols, TimeSpan.Day, from_time)

        cache_processor = CandleCache()
        strategy_processor = StrategyProcessor([ConnorsRSI2()], SimpleSumSignalsExecutor(), cache_processor)
        technicals_processor = TechnicalsProcessor(strategy_processor)
        processor = TechnicalsProcessor(technicals_processor)

        return PipelineRunner(source, processor)

    @staticmethod
    def build_mongodb_history_buckets_backtester(bins_file_path: str) -> PipelineRunner:
        mongodb_storage = MongoDBStorage()
        symbols = AssetsProvider.get_sp500_symbols()

        backtest_from_time = datetime.now() - timedelta(days=30 * 6)
        data_from_time = datetime.now() - timedelta(days=365 * 3)
        source = MongoDBSource(mongodb_storage, symbols, TimeSpan.Day, backtest_from_time)

        history_compare_strategy = HistoryBucketCompareStrategy(mongodb_storage,
                                                                data_from_time,
                                                                backtest_from_time,
                                                                indicators_to_compare=['sma5', 'sma20',
                                                                                       'cci7', 'cci14',
                                                                                       'rsi7', 'rsi14',
                                                                                       'stddev5', 'ema5',
                                                                                       'ema20', 'correlation'],
                                                                return_field='ctc1', min_event_count=50,
                                                                min_avg_return=0.2)

        cache_processor = CandleCache()
        strategy_processor = StrategyProcessor([history_compare_strategy], SimpleSumSignalsExecutor(), cache_processor)
        bucket_matcher = TechnicalsBucketsMatcher(bins_file_path, next_processor=strategy_processor)
        technical_normalizer = TechnicalsNormalizerProcessor(next_processor=bucket_matcher)
        processor = TechnicalsProcessor(technical_normalizer)

        return PipelineRunner(source, processor)

    @staticmethod
    def build_mongodb_history_similarity_backtester(bins_file_path: str) -> PipelineRunner:
        mongodb_storage = MongoDBStorage()
        symbols = AssetsProvider.get_sp500_symbols()

        backtest_from_time = datetime.now() - timedelta(days=30 * 6)
        data_from_time = datetime.now() - timedelta(days=365 * 3)
        source = MongoDBSource(mongodb_storage, symbols, TimeSpan.Day, backtest_from_time)

        history_compare_strategy = HistoryCosineSimilarityStrategy(mongodb_storage,
                                                                   data_from_time,
                                                                   backtest_from_time,
                                                                   indicators_to_compare=['sma5', 'sma20',
                                                                                          'cci7', 'cci14',
                                                                                          'rsi2', 'rsi7',
                                                                                          'stddev5', 'ema5', 'ema20'],
                                                                   return_field='ctc1', min_event_count=50,
                                                                   min_avg_return=0.3)

        cache_processor = CandleCache()
        strategy_processor = StrategyProcessor([history_compare_strategy], SimpleSumSignalsExecutor(), cache_processor)
        bucket_matcher = TechnicalsBucketsMatcher(bins_file_path, next_processor=strategy_processor)
        technical_normalizer = TechnicalsNormalizerProcessor(next_processor=bucket_matcher)
        processor = TechnicalsProcessor(technical_normalizer)

        return PipelineRunner(source, processor)
