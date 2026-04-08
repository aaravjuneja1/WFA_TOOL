import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_single_stock(filepath: str) -> pd.DataFrame | None:
    try:
        df = pd.read_csv(filepath)
        
        required_columns = {'date', 'open', 'high', 'low', 'close', 'volume'}
        df_columns_lower = {col.lower() for col in df.columns}
        
        if not required_columns.issubset(df_columns_lower):
            missing = required_columns - df_columns_lower
            logger.warning(f"File {filepath} missing required columns: {missing}")
            return None
        
        df.columns = df.columns.str.lower()
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        df = df.sort_index()
        
        for col in ['open', 'high', 'low', 'close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        df['volume'] = df['volume'].fillna(0).astype('int64')
        
        initial_rows = len(df)
        df = df[(df['open'] > 0) & (df['close'] > 0)]
        invalid_ohlc = initial_rows - len(df)
        
        if invalid_ohlc > 0:
            logger.info(f"File {filepath}: Dropped {invalid_ohlc} rows with invalid OHLC values")
        
        df = df[~df.index.duplicated(keep='last')]
        
        if len(df) < 500:
            logger.warning(f"File {filepath}: Only {len(df)} rows after cleaning (minimum 500 required)")
            return None
        
        if df.isnull().any().any():
            logger.warning(f"File {filepath}: Contains NaN values after cleaning")
            return None
        
        logger.info(f"Successfully loaded {filepath}: {len(df)} rows")
        return df
        
    except Exception as e:
        logger.error(f"Failed to load {filepath}: {str(e)}")
        return None

def load_all_stocks(stocks_dir: str) -> dict[str, pd.DataFrame]:
    stocks_path = Path(stocks_dir)
    
    if not stocks_path.exists():
        logger.error(f"Stocks directory {stocks_dir} does not exist")
        return {}
    
    stock_files = list(stocks_path.glob("*.csv"))
    
    if not stock_files:
        logger.warning(f"No CSV files found in {stocks_dir}")
        return {}
    
    loaded_stocks = {}
    skipped_count = 0
    
    for file_path in stock_files:
        ticker = file_path.stem
        df = load_single_stock(str(file_path))
        
        if df is not None:
            loaded_stocks[ticker] = df
        else:
            skipped_count += 1
    
    logger.info(f"Loaded {len(loaded_stocks)} stocks successfully")
    logger.info(f"Skipped {skipped_count} stocks")
    
    return loaded_stocks
