import os
import re
import pandas as pd
from PyPDF2 import PdfReader


class DataParser:
    """Parse financial data from various file formats"""

    @staticmethod
    def parse_csv(file_path, company_id):
        """Parse metrics from CSV file"""
        try:
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')

            metrics_data = []

            for _, row in df.iterrows():
                metric = {
                    'company_id': company_id,
                    'year': int(row.get('year', 0)) if pd.notna(row.get('year')) else None,
                    'quarter': int(row.get('quarter', 0)) if pd.notna(row.get('quarter')) else None,
                    'revenue': float(row.get('revenue', 0)) if pd.notna(row.get('revenue')) else None,
                    'arr': float(row.get('arr', 0)) if pd.notna(row.get('arr')) else None,
                    'carr': float(row.get('carr', 0)) if pd.notna(row.get('carr')) else None,
                    'larr': float(row.get('larr', 0)) if pd.notna(row.get('larr')) else None,
                    'gross_margin': float(row.get('gross_margin', 0)) if pd.notna(row.get('gross_margin')) else None,
                    'burn_rate': float(row.get('burn_rate', 0)) if pd.notna(row.get('burn_rate')) else None,
                    'cash_balance': float(row.get('cash_balance', 0)) if pd.notna(row.get('cash_balance')) else None,
                    'customer_count': int(row.get('customer_count', 0)) if pd.notna(row.get('customer_count')) else None,
                    'notes': str(row.get('notes', '')) if pd.notna(row.get('notes')) else None
                }

                if metric['year'] and metric['quarter']:
                    metrics_data.append(metric)

            return {'success': True, 'data': metrics_data, 'count': len(metrics_data)}

        except Exception as e:
            return {'success': False, 'error': str(e), 'data': []}

    @staticmethod
    def extract_text_from_pdf(file_path):
        """Extract text content from PDF file"""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return {'success': True, 'text': text}
        except Exception as e:
            return {'success': False, 'error': str(e), 'text': ''}

    @staticmethod
    def extract_metrics_from_text(text):
        """
        Attempt to extract financial metrics from text using pattern matching
        This is a best-effort approach for PDFs that may contain financial data
        """
        metrics = {}

        # Common patterns for financial metrics
        patterns = {
            'revenue': r'revenue[:\s]+\$?([\d,]+\.?\d*)[kKmMbB]?',
            'arr': r'(?:annual recurring revenue|arr)[:\s]+\$?([\d,]+\.?\d*)[kKmMbB]?',
            'carr': r'(?:committed annual recurring revenue|carr)[:\s]+\$?([\d,]+\.?\d*)[kKmMbB]?',
            'larr': r'(?:linear annual recurring revenue|larr)[:\s]+\$?([\d,]+\.?\d*)[kKmMbB]?',
            'gross_margin': r'gross margin[:\s]+([\d.]+)%?',
            'burn_rate': r'burn rate[:\s]+\$?([\d,]+\.?\d*)[kKmMbB]?',
            'cash_balance': r'cash balance[:\s]+\$?([\d,]+\.?\d*)[kKmMbB]?',
            'customer_count': r'(?:customers|customer count)[:\s]+([\d,]+)',
        }

        text_lower = text.lower()

        for metric_name, pattern in patterns.items():
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace(',', '')
                try:
                    value = float(value_str)

                    # Handle K, M, B suffixes
                    suffix_match = re.search(r'[\d.]+([kKmMbB])', match.group(0))
                    if suffix_match:
                        suffix = suffix_match.group(1).upper()
                        if suffix == 'K':
                            value *= 1_000
                        elif suffix == 'M':
                            value *= 1_000_000
                        elif suffix == 'B':
                            value *= 1_000_000_000

                    metrics[metric_name] = value
                except ValueError:
                    continue

        # Try to extract quarter and year
        quarter_match = re.search(r'Q([1-4])\s+(\d{4})', text, re.IGNORECASE)
        if quarter_match:
            metrics['quarter'] = int(quarter_match.group(1))
            metrics['year'] = int(quarter_match.group(2))

        return metrics

    @staticmethod
    def parse_pdf_for_metrics(file_path, company_id):
        """
        Parse PDF file and attempt to extract financial metrics
        """
        result = DataParser.extract_text_from_pdf(file_path)

        if not result['success']:
            return result

        extracted_metrics = DataParser.extract_metrics_from_text(result['text'])

        if extracted_metrics:
            extracted_metrics['company_id'] = company_id
            return {
                'success': True,
                'data': [extracted_metrics],
                'count': 1,
                'note': 'Metrics extracted from PDF using pattern matching. Please verify accuracy.'
            }
        else:
            return {
                'success': False,
                'error': 'No financial metrics found in PDF',
                'data': [],
                'text_preview': result['text'][:500]
            }

    @staticmethod
    def validate_metrics_data(metrics_list):
        """Validate metrics data before saving to database"""
        errors = []
        valid_metrics = []

        for idx, metric in enumerate(metrics_list):
            metric_errors = []

            # Required fields
            if not metric.get('year') or not isinstance(metric['year'], int):
                metric_errors.append(f"Row {idx + 1}: Invalid or missing year")

            if not metric.get('quarter') or metric['quarter'] not in [1, 2, 3, 4]:
                metric_errors.append(f"Row {idx + 1}: Invalid or missing quarter (must be 1-4)")

            # At least one financial metric should be present
            financial_fields = ['revenue', 'arr', 'carr', 'larr']
            if not any(metric.get(field) for field in financial_fields):
                metric_errors.append(f"Row {idx + 1}: At least one financial metric required")

            if metric_errors:
                errors.extend(metric_errors)
            else:
                valid_metrics.append(metric)

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'valid_metrics': valid_metrics,
            'total': len(metrics_list),
            'valid_count': len(valid_metrics)
        }
