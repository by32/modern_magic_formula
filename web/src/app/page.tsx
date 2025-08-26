'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { TrendingUp, Shield, BarChart3, AlertCircle, CheckCircle, Clock, ChevronDown, ChevronUp, Info, Calculator, Target, DollarSign, ExternalLink, Download } from 'lucide-react';

interface StockData {
  ticker: string;
  company_name: string;
  sector: string;
  market_cap: number;
  earnings_yield: number;
  roc: number;
  f_score: number;
  magic_formula_rank: number;
  pe_ratio?: number;
  pb_ratio?: number;
  revenue?: number;
  net_income?: number;
  operating_income?: number;
  current_price?: number;
  momentum_6m?: number;
  debt_to_equity?: number;
}

interface QualityData {
  quality_score: number;
  last_updated: string;
  data_age_days: number;
  total_stocks: number;
  status: string;
}

export default function HomePage() {
  const [stocks, setStocks] = useState<StockData[]>([]);
  const [quality, setQuality] = useState<QualityData | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedStock, setExpandedStock] = useState<string | null>(null);
  const [totalStocksCount, setTotalStocksCount] = useState<number>(0);
  const [totalUniverseCount, setTotalUniverseCount] = useState<number>(0);
  const [filters, setFilters] = useState({
    limit: 20,
    min_fscore: 5,
    min_market_cap: 1000000000,
    exclude_financials: true
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [stocksRes, qualityRes] = await Promise.all([
        fetch(`/api/stocks?limit=${filters.limit}&min_fscore=${filters.min_fscore}&min_market_cap=${filters.min_market_cap}&exclude_financials=${filters.exclude_financials}`),
        fetch('/api/quality')
      ]);

      if (stocksRes.ok) {
        const stocksData = await stocksRes.json();
        setStocks(stocksData.stocks || []);
        setTotalStocksCount(stocksData.total || 0);
        setTotalUniverseCount(stocksData.total_universe || 0);
      }

      if (qualityRes.ok) {
        const qualityData = await qualityRes.json();
        setQuality(qualityData);
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const formatMarketCap = (value: number) => {
    if (value >= 1e12) return `$${(value / 1e12).toFixed(1)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
    return `$${value.toLocaleString()}`;
  };

  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

  const exportToCSV = () => {
    if (stocks.length === 0) return;

    const csvHeaders = [
      'Rank',
      'Ticker',
      'Company Name',
      'Sector', 
      'Market Cap',
      'Current Price',
      'Earnings Yield',
      'ROC',
      'F-Score',
      'Magic Formula Rank',
      '6M Momentum',
      'P/E Ratio',
      'P/B Ratio',
      'Revenue',
      'Net Income',
      'Operating Income'
    ];

    const csvData = stocks.map((stock, index) => [
      index + 1, // Display rank
      stock.ticker,
      stock.company_name,
      stock.sector,
      stock.market_cap,
      stock.current_price || 'N/A',
      (stock.earnings_yield * 100).toFixed(1) + '%',
      (stock.roc * 100).toFixed(1) + '%',
      stock.f_score,
      stock.magic_formula_rank,
      stock.momentum_6m ? (stock.momentum_6m * 100).toFixed(1) + '%' : 'N/A',
      stock.pe_ratio?.toFixed(1) || 'N/A',
      stock.pb_ratio?.toFixed(1) || 'N/A',
      stock.revenue || 'N/A',
      stock.net_income || 'N/A',
      stock.operating_income || 'N/A'
    ]);

    const csvContent = [
      csvHeaders.join(','),
      ...csvData.map(row => 
        row.map(cell => {
          // Escape cells that contain commas, quotes, or newlines
          if (typeof cell === 'string' && (cell.includes(',') || cell.includes('"') || cell.includes('\n'))) {
            return `"${cell.replace(/"/g, '""')}"`;
          }
          return cell;
        }).join(',')
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `magic-formula-stocks-${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getQualityColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getQualityIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="w-5 h-5" />;
      case 'warning': return <AlertCircle className="w-5 h-5" />;
      case 'critical': return <AlertCircle className="w-5 h-5" />;
      default: return <Clock className="w-5 h-5" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🎯 Modern Magic Formula
          </h1>
          <p className="text-xl text-gray-600 mb-2">
            DIY Stock Picks for Individual Investors
          </p>
          <p className="text-sm text-gray-500">
            Based on Joel Greenblatt&apos;s proven value investing strategy
          </p>
        </div>

        {/* Quality Status */}
        {quality && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className={getQualityColor(quality.status)}>
                  {getQualityIcon(quality.status)}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Data Quality</h3>
                  <p className="text-sm text-gray-600">
                    Score: {(quality.quality_score * 100).toFixed(1)}% | 
                    Updated: {quality.last_updated ? new Date(quality.last_updated).toLocaleDateString() : 'N/A'} | 
                    {quality.total_stocks} stocks analyzed
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-600">
                  {(quality.quality_score * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-gray-500">Quality Score</div>
              </div>
            </div>
          </div>
        )}

        {/* Key Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center space-x-3 mb-3">
              <TrendingUp className="w-8 h-8 text-blue-600" />
              <h3 className="font-semibold text-gray-900">Magic Formula</h3>
            </div>
            <p className="text-sm text-gray-600">
              Combines earnings yield and return on capital to find undervalued, profitable companies
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center space-x-3 mb-3">
              <Shield className="w-8 h-8 text-green-600" />
              <h3 className="font-semibold text-gray-900">Quality Filter</h3>
            </div>
            <p className="text-sm text-gray-600">
              F-Score analysis ensures financial strength and eliminates potential value traps
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center space-x-3 mb-3">
              <BarChart3 className="w-8 h-8 text-purple-600" />
              <h3 className="font-semibold text-gray-900">Diversification</h3>
            </div>
            <p className="text-sm text-gray-600">
              Automatic sector balancing to reduce concentration risk
            </p>
          </div>
        </div>

        {/* Magic Formula Explanation */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 mb-8 border border-blue-200">
          <div className="flex items-start space-x-3">
            <Info className="w-6 h-6 text-blue-600 mt-1" />
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 mb-3 text-lg">How the Magic Formula Works</h3>
              <div className="grid md:grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    <Calculator className="w-4 h-4 text-indigo-600" />
                    <span className="font-medium text-gray-900">Step 1: Calculate Earnings Yield</span>
                  </div>
                  <p className="text-gray-700 ml-6">
                    EBIT ÷ Enterprise Value = How much the business earns relative to its price.
                    Higher is better (cheap + profitable).
                  </p>
                </div>
                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    <Target className="w-4 h-4 text-indigo-600" />
                    <span className="font-medium text-gray-900">Step 2: Calculate Return on Capital</span>
                  </div>
                  <p className="text-gray-700 ml-6">
                    EBIT ÷ (Working Capital + Fixed Assets) = How efficiently the business generates profits.
                    Higher means better management.
                  </p>
                </div>
              </div>
              <div className="mt-4 p-3 bg-white rounded border border-blue-200">
                <div className="flex items-center space-x-2">
                  <DollarSign className="w-4 h-4 text-green-600" />
                  <span className="font-medium text-gray-900">Final Ranking</span>
                </div>
                <p className="text-gray-700 mt-1 text-sm">
                  Stocks are ranked on both metrics, then combined. The top-ranked stocks are both cheap AND high quality.
                  You&apos;re seeing the top {filters.limit} out of {totalStocksCount} qualifying stocks from the {totalUniverseCount || '~1000'} Russell 1000 universe.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h3 className="font-semibold text-gray-900 mb-4">Customize Your Picks</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Number of Stocks
              </label>
              <select
                value={filters.limit}
                onChange={(e) => setFilters({...filters, limit: parseInt(e.target.value)})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={15}>15 stocks</option>
                <option value={20}>20 stocks</option>
                <option value={25}>25 stocks</option>
                <option value={30}>30 stocks</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minimum F-Score
              </label>
              <select
                value={filters.min_fscore}
                onChange={(e) => setFilters({...filters, min_fscore: parseInt(e.target.value)})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={4}>4+ (Moderate)</option>
                <option value={5}>5+ (Good)</option>
                <option value={6}>6+ (Strong)</option>
                <option value={7}>7+ (Excellent)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minimum Market Cap
              </label>
              <select
                value={filters.min_market_cap}
                onChange={(e) => setFilters({...filters, min_market_cap: parseFloat(e.target.value)})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={1000000000}>$1B+ (Large Cap)</option>
                <option value={500000000}>$500M+ (Mid Cap)</option>
                <option value={100000000}>$100M+ (Small Cap)</option>
              </select>
            </div>
          </div>
          
          <div className="mt-4 border-t pt-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={filters.exclude_financials}
                onChange={(e) => setFilters({...filters, exclude_financials: e.target.checked})}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">
                Exclude Financial & Utility stocks (like magicformulainvesting.com)
              </span>
            </label>
            <p className="text-xs text-gray-500 mt-1">
              The official Magic Formula site excludes these sectors due to unique accounting practices.
            </p>
          </div>
        </div>

        {/* Stock Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-start">
            <div>
              <h3 className="font-semibold text-gray-900">
                Your Magic Formula Stock Picks
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Ranked by Magic Formula score • Updated daily
              </p>
              {stocks.length > 0 && (
                <p className="text-xs text-gray-500 mt-1">
                  Export includes all financial metrics, ratios, and rankings for portfolio tracking
                </p>
              )}
            </div>
            {stocks.length > 0 && (
              <button
                onClick={exportToCSV}
                className="inline-flex items-center px-3 py-2 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
              >
                <Download className="w-4 h-4 mr-2" />
                Export CSV
              </button>
            )}
          </div>

          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-gray-600 mt-2">Loading stock picks...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rank
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Company
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Sector
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Market Cap
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Earnings Yield
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      ROC
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      F-Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Research
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {stocks.map((stock, index) => (
                    <React.Fragment key={stock.ticker}>
                      <tr 
                        className="hover:bg-gray-50 cursor-pointer transition-colors"
                        onClick={() => setExpandedStock(expandedStock === stock.ticker ? null : stock.ticker)}
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-sm font-medium text-blue-600">
                              {index + 1}
                            </div>
                            <div className="ml-2">
                              {expandedStock === stock.ticker ? 
                                <ChevronUp className="w-4 h-4 text-gray-400" /> : 
                                <ChevronDown className="w-4 h-4 text-gray-400" />
                              }
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {stock.ticker}
                            </div>
                            <div className="text-sm text-gray-500 truncate max-w-48">
                              {stock.company_name}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">
                            {stock.sector}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatMarketCap(stock.market_cap)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatPercent(stock.earnings_yield)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatPercent(stock.roc)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="text-sm font-medium text-gray-900">
                              {stock.f_score}
                            </div>
                            <div className="ml-2 w-16 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-green-600 h-2 rounded-full"
                                style={{ width: `${(stock.f_score / 9) * 100}%` }}
                              ></div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <a
                            href={`https://finance.yahoo.com/quote/${stock.ticker}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()} // Prevent row expansion when clicking link
                            className="inline-flex items-center px-2 py-1 text-xs font-medium text-purple-700 bg-purple-100 rounded hover:bg-purple-200 transition-colors"
                          >
                            <ExternalLink className="w-3 h-3 mr-1" />
                            Yahoo
                          </a>
                        </td>
                      </tr>
                      {expandedStock === stock.ticker && (
                        <tr>
                          <td colSpan={8} className="px-6 py-4 bg-gray-50">
                            <div className="space-y-4">
                              <div className="flex items-center justify-between border-b pb-2">
                                <h4 className="font-semibold text-gray-900">Detailed Financial Metrics for {stock.ticker}</h4>
                                <span className="text-sm text-gray-500">Magic Formula Rank: #{stock.magic_formula_rank} of {totalUniverseCount}</span>
                              </div>
                              
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div>
                                  <div className="text-xs text-gray-500 uppercase">Current Price</div>
                                  <div className="text-lg font-medium text-gray-900">
                                    ${stock.current_price?.toFixed(2) || 'N/A'}
                                  </div>
                                </div>
                                <div>
                                  <div className="text-xs text-gray-500 uppercase">6M Momentum</div>
                                  <div className={`text-lg font-medium ${(stock.momentum_6m || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                    {stock.momentum_6m ? formatPercent(stock.momentum_6m) : 'N/A'}
                                  </div>
                                </div>
                                <div>
                                  <div className="text-xs text-gray-500 uppercase">P/E Ratio</div>
                                  <div className="text-lg font-medium text-gray-900">
                                    {stock.pe_ratio?.toFixed(1) || 'N/A'}
                                  </div>
                                </div>
                                <div>
                                  <div className="text-xs text-gray-500 uppercase">P/B Ratio</div>
                                  <div className="text-lg font-medium text-gray-900">
                                    {stock.pb_ratio?.toFixed(1) || 'N/A'}
                                  </div>
                                </div>
                              </div>

                              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                <div>
                                  <div className="text-xs text-gray-500 uppercase">Revenue</div>
                                  <div className="text-lg font-medium text-gray-900">
                                    {stock.revenue ? formatMarketCap(stock.revenue) : 'N/A'}
                                  </div>
                                </div>
                                <div>
                                  <div className="text-xs text-gray-500 uppercase">Operating Income</div>
                                  <div className="text-lg font-medium text-gray-900">
                                    {stock.operating_income ? formatMarketCap(stock.operating_income) : 'N/A'}
                                  </div>
                                </div>
                                <div>
                                  <div className="text-xs text-gray-500 uppercase">Net Income</div>
                                  <div className="text-lg font-medium text-gray-900">
                                    {stock.net_income ? formatMarketCap(stock.net_income) : 'N/A'}
                                  </div>
                                </div>
                              </div>

                              <div className="bg-blue-50 rounded p-3">
                                <div className="text-sm text-blue-900">
                                  <strong>Why this stock ranks #{stock.magic_formula_rank}:</strong>
                                  <p className="mt-1">
                                    This company has an earnings yield of {formatPercent(stock.earnings_yield)} (ranked in top tier for value) 
                                    and a return on capital of {formatPercent(stock.roc)} (efficiency rank). 
                                    The combination of being both cheap and profitable gives it a strong Magic Formula score.
                                  </p>
                                </div>
                              </div>

                              <div className="bg-gray-100 rounded p-3">
                                <div className="flex items-center justify-between mb-2">
                                  <h5 className="font-medium text-gray-900">Research {stock.ticker} Further</h5>
                                  <ExternalLink className="w-4 h-4 text-gray-500" />
                                </div>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                                  <a
                                    href={`https://finance.yahoo.com/quote/${stock.ticker}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center px-3 py-2 text-xs font-medium text-purple-700 bg-purple-100 rounded-md hover:bg-purple-200 transition-colors"
                                  >
                                    <ExternalLink className="w-3 h-3 mr-1" />
                                    Yahoo Finance
                                  </a>
                                  <a
                                    href={`https://www.morningstar.com/stocks/xnas/${stock.ticker}/quote`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center px-3 py-2 text-xs font-medium text-blue-700 bg-blue-100 rounded-md hover:bg-blue-200 transition-colors"
                                  >
                                    <ExternalLink className="w-3 h-3 mr-1" />
                                    Morningstar
                                  </a>
                                  <a
                                    href={`https://www.sec.gov/edgar/searchedgar/companysearch.html?q=${stock.ticker}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center px-3 py-2 text-xs font-medium text-green-700 bg-green-100 rounded-md hover:bg-green-200 transition-colors"
                                  >
                                    <ExternalLink className="w-3 h-3 mr-1" />
                                    SEC Filings
                                  </a>
                                  <a
                                    href={`https://www.google.com/search?q=${encodeURIComponent(stock.company_name + ' investor relations')}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center px-3 py-2 text-xs font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors"
                                  >
                                    <ExternalLink className="w-3 h-3 mr-1" />
                                    Company IR
                                  </a>
                                </div>
                                <p className="text-xs text-gray-600 mt-2">
                                  <strong>Due diligence reminder:</strong> Always research companies thoroughly before investing. 
                                  Check recent earnings, management changes, and industry trends.
                                </p>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Disclaimer */}
        <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <div className="flex">
            <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 mr-3 flex-shrink-0" />
            <div className="text-sm text-yellow-800">
              <h4 className="font-medium mb-1">Investment Disclaimer</h4>
              <p>
                This tool is for educational purposes only and does not constitute investment advice. 
                Past performance does not guarantee future results. Always conduct your own research 
                and consult with qualified financial advisors before making investment decisions.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
