'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, Shield, BarChart3, AlertCircle, CheckCircle, Clock } from 'lucide-react';

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
  const [filters, setFilters] = useState({
    limit: 20,
    min_fscore: 5,
    min_market_cap: 1000000000
  });

  useEffect(() => {
    loadData();
  }, [filters]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [stocksRes, qualityRes] = await Promise.all([
        fetch(`/api/stocks?limit=${filters.limit}&min_fscore=${filters.min_fscore}&min_market_cap=${filters.min_market_cap}`),
        fetch('/api/quality')
      ]);

      if (stocksRes.ok) {
        const stocksData = await stocksRes.json();
        setStocks(stocksData.stocks || []);
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
  };

  const formatMarketCap = (value: number) => {
    if (value >= 1e12) return `$${(value / 1e12).toFixed(1)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
    return `$${value.toLocaleString()}`;
  };

  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

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
            Based on Joel Greenblatt's proven value investing strategy
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
                    Updated: {quality.data_age_days} days ago | 
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
        </div>

        {/* Stock Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="font-semibold text-gray-900">
              Your Magic Formula Stock Picks
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Ranked by Magic Formula score • Updated daily
            </p>
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
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {stocks.map((stock, index) => (
                    <tr key={stock.ticker} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-sm font-medium text-blue-600">
                            {index + 1}
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
                    </tr>
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
