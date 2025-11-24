from datetime import datetime, timedelta
from sqlalchemy import func
from app.models import Company, QuarterlyMetrics


class DueDiligenceAnalytics:
    """Analyze portfolio company health and performance"""

    @staticmethod
    def get_company_health_score(company_id):
        """
        Calculate a health score for a company based on recent metrics
        Score is 0-100, with higher being better
        """
        # Get last 4 quarters of data
        metrics = QuarterlyMetrics.query.filter_by(company_id=company_id).order_by(
            QuarterlyMetrics.year.desc(), QuarterlyMetrics.quarter.desc()
        ).limit(4).all()

        if not metrics:
            return {'score': None, 'status': 'No data available'}

        latest = metrics[0]
        score = 0
        factors = []

        # Revenue growth (25 points)
        if len(metrics) >= 2:
            if latest.revenue and metrics[1].revenue and metrics[1].revenue > 0:
                revenue_growth = ((latest.revenue - metrics[1].revenue) / metrics[1].revenue) * 100
                if revenue_growth > 20:
                    score += 25
                    factors.append({'factor': 'Revenue Growth', 'value': f'{revenue_growth:.1f}%', 'points': 25})
                elif revenue_growth > 10:
                    score += 20
                    factors.append({'factor': 'Revenue Growth', 'value': f'{revenue_growth:.1f}%', 'points': 20})
                elif revenue_growth > 0:
                    score += 15
                    factors.append({'factor': 'Revenue Growth', 'value': f'{revenue_growth:.1f}%', 'points': 15})
                else:
                    factors.append({'factor': 'Revenue Growth', 'value': f'{revenue_growth:.1f}%', 'points': 0})

        # ARR growth (25 points)
        if len(metrics) >= 2:
            if latest.arr and metrics[1].arr and metrics[1].arr > 0:
                arr_growth = ((latest.arr - metrics[1].arr) / metrics[1].arr) * 100
                if arr_growth > 20:
                    score += 25
                    factors.append({'factor': 'ARR Growth', 'value': f'{arr_growth:.1f}%', 'points': 25})
                elif arr_growth > 10:
                    score += 20
                    factors.append({'factor': 'ARR Growth', 'value': f'{arr_growth:.1f}%', 'points': 20})
                elif arr_growth > 0:
                    score += 15
                    factors.append({'factor': 'ARR Growth', 'value': f'{arr_growth:.1f}%', 'points': 15})
                else:
                    factors.append({'factor': 'ARR Growth', 'value': f'{arr_growth:.1f}%', 'points': 0})

        # Gross margin (20 points)
        if latest.gross_margin:
            if latest.gross_margin >= 0.70:  # 70%+
                score += 20
                factors.append({'factor': 'Gross Margin', 'value': f'{latest.gross_margin*100:.1f}%', 'points': 20})
            elif latest.gross_margin >= 0.50:  # 50-70%
                score += 15
                factors.append({'factor': 'Gross Margin', 'value': f'{latest.gross_margin*100:.1f}%', 'points': 15})
            elif latest.gross_margin >= 0.30:  # 30-50%
                score += 10
                factors.append({'factor': 'Gross Margin', 'value': f'{latest.gross_margin*100:.1f}%', 'points': 10})
            else:
                factors.append({'factor': 'Gross Margin', 'value': f'{latest.gross_margin*100:.1f}%', 'points': 0})

        # Cash runway (15 points) - based on cash balance vs burn rate
        if latest.cash_balance and latest.burn_rate and latest.burn_rate > 0:
            runway_months = latest.cash_balance / latest.burn_rate
            if runway_months >= 18:
                score += 15
                factors.append({'factor': 'Cash Runway', 'value': f'{runway_months:.1f} months', 'points': 15})
            elif runway_months >= 12:
                score += 12
                factors.append({'factor': 'Cash Runway', 'value': f'{runway_months:.1f} months', 'points': 12})
            elif runway_months >= 6:
                score += 8
                factors.append({'factor': 'Cash Runway', 'value': f'{runway_months:.1f} months', 'points': 8})
            else:
                factors.append({'factor': 'Cash Runway', 'value': f'{runway_months:.1f} months (⚠️)', 'points': 0})

        # Customer growth (15 points)
        if len(metrics) >= 2:
            if latest.customer_count and metrics[1].customer_count and metrics[1].customer_count > 0:
                customer_growth = ((latest.customer_count - metrics[1].customer_count) / metrics[1].customer_count) * 100
                if customer_growth > 15:
                    score += 15
                    factors.append({'factor': 'Customer Growth', 'value': f'{customer_growth:.1f}%', 'points': 15})
                elif customer_growth > 5:
                    score += 10
                    factors.append({'factor': 'Customer Growth', 'value': f'{customer_growth:.1f}%', 'points': 10})
                elif customer_growth >= 0:
                    score += 5
                    factors.append({'factor': 'Customer Growth', 'value': f'{customer_growth:.1f}%', 'points': 5})
                else:
                    factors.append({'factor': 'Customer Growth', 'value': f'{customer_growth:.1f}%', 'points': 0})

        # Determine status
        if score >= 80:
            status = 'Excellent'
        elif score >= 60:
            status = 'Good'
        elif score >= 40:
            status = 'Fair'
        elif score >= 20:
            status = 'Needs Attention'
        else:
            status = 'Critical'

        return {
            'score': score,
            'status': status,
            'factors': factors,
            'latest_quarter': f'Q{latest.quarter} {latest.year}'
        }

    @staticmethod
    def get_growth_trends(company_id, periods=8):
        """Get growth trends over the specified number of periods"""
        metrics = QuarterlyMetrics.query.filter_by(company_id=company_id).order_by(
            QuarterlyMetrics.year.desc(), QuarterlyMetrics.quarter.desc()
        ).limit(periods).all()

        if len(metrics) < 2:
            return {'error': 'Insufficient data for trend analysis'}

        metrics.reverse()  # Chronological order

        trends = {
            'periods': [],
            'revenue': [],
            'arr': [],
            'carr': [],
            'larr': [],
            'gross_margin': [],
            'customer_count': []
        }

        for metric in metrics:
            period_label = f'Q{metric.quarter} {metric.year}'
            trends['periods'].append(period_label)
            trends['revenue'].append(metric.revenue or 0)
            trends['arr'].append(metric.arr or 0)
            trends['carr'].append(metric.carr or 0)
            trends['larr'].append(metric.larr or 0)
            trends['gross_margin'].append(metric.gross_margin or 0)
            trends['customer_count'].append(metric.customer_count or 0)

        # Calculate quarter-over-quarter growth rates
        growth_rates = {}
        for key in ['revenue', 'arr', 'carr', 'larr']:
            if len(trends[key]) >= 2 and trends[key][-2] > 0:
                qoq_growth = ((trends[key][-1] - trends[key][-2]) / trends[key][-2]) * 100
                growth_rates[f'{key}_qoq'] = round(qoq_growth, 2)

        return {
            'trends': trends,
            'growth_rates': growth_rates,
            'data_points': len(metrics)
        }

    @staticmethod
    def get_portfolio_overview():
        """Get overview of entire portfolio"""
        companies = Company.query.all()
        overview = []

        total_portfolio_arr = 0

        for company in companies:
            latest_metric = QuarterlyMetrics.query.filter_by(company_id=company.id).order_by(
                QuarterlyMetrics.year.desc(), QuarterlyMetrics.quarter.desc()
            ).first()

            if latest_metric:
                health = DueDiligenceAnalytics.get_company_health_score(company.id)

                company_data = {
                    'id': company.id,
                    'name': company.name,
                    'industry': company.industry,
                    'stage': company.stage,
                    'latest_revenue': latest_metric.revenue,
                    'latest_arr': latest_metric.arr,
                    'latest_quarter': f'Q{latest_metric.quarter} {latest_metric.year}',
                    'health_score': health.get('score'),
                    'health_status': health.get('status')
                }

                if latest_metric.arr:
                    total_portfolio_arr += latest_metric.arr

                overview.append(company_data)

        return {
            'companies': overview,
            'total_companies': len(companies),
            'companies_with_data': len(overview),
            'total_portfolio_arr': total_portfolio_arr
        }

    @staticmethod
    def get_quarterly_comparison(company_id, year, quarter):
        """Compare a specific quarter against previous quarters"""
        current = QuarterlyMetrics.query.filter_by(
            company_id=company_id, year=year, quarter=quarter
        ).first()

        if not current:
            return {'error': 'Quarter not found'}

        # Get previous quarter
        if quarter == 1:
            prev_quarter, prev_year = 4, year - 1
        else:
            prev_quarter, prev_year = quarter - 1, year

        previous = QuarterlyMetrics.query.filter_by(
            company_id=company_id, year=prev_year, quarter=prev_quarter
        ).first()

        # Get same quarter last year
        yoy = QuarterlyMetrics.query.filter_by(
            company_id=company_id, year=year - 1, quarter=quarter
        ).first()

        comparison = {
            'current': current.to_dict(),
            'previous_quarter': previous.to_dict() if previous else None,
            'year_ago': yoy.to_dict() if yoy else None
        }

        # Calculate changes
        if previous:
            comparison['qoq_changes'] = {
                'revenue': DueDiligenceAnalytics._calculate_change(current.revenue, previous.revenue),
                'arr': DueDiligenceAnalytics._calculate_change(current.arr, previous.arr),
                'customers': DueDiligenceAnalytics._calculate_change(current.customer_count, previous.customer_count)
            }

        if yoy:
            comparison['yoy_changes'] = {
                'revenue': DueDiligenceAnalytics._calculate_change(current.revenue, yoy.revenue),
                'arr': DueDiligenceAnalytics._calculate_change(current.arr, yoy.arr),
                'customers': DueDiligenceAnalytics._calculate_change(current.customer_count, yoy.customer_count)
            }

        return comparison

    @staticmethod
    def _calculate_change(current, previous):
        """Calculate percentage change between two values"""
        if previous and previous > 0 and current is not None:
            change = ((current - previous) / previous) * 100
            return {
                'absolute': round(current - previous, 2),
                'percentage': round(change, 2)
            }
        return None
