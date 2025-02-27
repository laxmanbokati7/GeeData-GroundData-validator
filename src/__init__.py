# Climate Data Fetcher package
import warnings

# Suppress the pandas FutureWarning about parse_dates
warnings.filterwarnings("ignore", message="Support for nested sequences for 'parse_dates'", category=FutureWarning)