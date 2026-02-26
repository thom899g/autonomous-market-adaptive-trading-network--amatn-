"""
Base Agent Module
Abstract base class for all AMATN agents with common functionality
"""
import abc
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from amatn.config import config
from amatn.data.market_data import MarketDataCollector

class BaseAgent(abc.ABC):
    """
    Abstract base class for all AMATN agents.
    Provides common functionality for logging, error handling, and state management.
    """
    
    def __init__(self, agent_id: str