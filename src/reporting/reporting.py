import csv
import logging
from datetime import datetime
from pathlib import Path
from collections import defaultdict


class ReportGenerator:
    """Generates CSV reports of processed emails and statistics."""
    
    def __init__(self, base_path="output/reports"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.processed_emails = []
        self.category_counts = defaultdict(int)
        self.error_count = 0
        self.attachment_count = 0
        
        logging.info(f"Report generator initialized: {self.base_path}")
    
    def record_email(self, email_data, category, has_attachments=False, error=None):
        """Record a processed email for reporting."""
        record = {
            'timestamp': datetime.now().isoformat(),
            'sender': email_data.get('sender', ''),
            'subject': email_data.get('subject', ''),
            'date': email_data.get('date', ''),
            'category': category,
            'has_attachments': has_attachments,
            'attachment_count': len(email_data.get('attachments', [])),
            'error': error or ''
        }
        
        self.processed_emails.append(record)
        
        if error:
            self.error_count += 1
        else:
            self.category_counts[category] += 1
            if has_attachments:
                self.attachment_count += 1
    
    def generate_weekly_report(self):
        """Generate weekly CSV report with all processed emails."""
        if not self.processed_emails:
            logging.warning("No emails processed, skipping report generation")
            return None
        
        now = datetime.now()
        week_str = now.strftime("%Y-W%W")
        report_filename = f"email_report_{week_str}.csv"
        report_path = self.base_path / report_filename
        
        try:
            with open(report_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'timestamp', 'sender', 'subject', 'date', 
                    'category', 'has_attachments', 'attachment_count', 'error'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for record in self.processed_emails:
                    writer.writerow(record)
            
            logging.info(f"Weekly report generated: {report_path}")
            return report_path
            
        except Exception as e:
            logging.error(f"Failed to generate weekly report: {e}")
            return None
    
    def generate_summary_report(self):
        """Generate summary CSV report with category statistics."""
        if not self.processed_emails:
            return None
        
        now = datetime.now()
        week_str = now.strftime("%Y-W%W")
        summary_filename = f"summary_report_{week_str}.csv"
        summary_path = self.base_path / summary_filename
        
        try:
            with open(summary_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['category', 'count', 'percentage']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                total = len(self.processed_emails) - self.error_count
                if total > 0:
                    # Sort categories by count (descending)
                    sorted_categories = sorted(
                        self.category_counts.items(),
                        key=lambda item: item[1],
                        reverse=True
                    )
                    
                    for category, count in sorted_categories:
                        percentage = (count / total) * 100
                        writer.writerow({
                            'category': category,
                            'count': count,
                            'percentage': f"{percentage:.2f}%"
                        })
                
                if self.error_count > 0:
                    error_percentage = (self.error_count / len(self.processed_emails)) * 100
                    writer.writerow({
                        'category': 'ERRORS',
                        'count': self.error_count,
                        'percentage': f"{error_percentage:.2f}%"
                    })
                
                writer.writerow({
                    'category': 'TOTAL',
                    'count': len(self.processed_emails),
                    'percentage': '100.00%'
                })
            
            logging.info(f"Summary report generated: {summary_path}")
            logging.info(f"Total emails: {len(self.processed_emails)}")
            logging.info(f"Categories: {dict(self.category_counts)}")
            logging.info(f"Attachments: {self.attachment_count}")
            logging.info(f"Errors: {self.error_count}")
            
            return summary_path
            
        except Exception as e:
            logging.error(f"Failed to generate summary report: {e}")
            return None

    def generate_repartition_report(self):
        if not self.processed_emails:
            return None
        week_str = datetime.now().strftime("%Y-W%W")
        repartition_path = self.base_path / f"repartition_report_{week_str}.csv"
        fieldnames = ['category', 'sender', 'subject', 'date', 'has_attachments']
        try:
            sorted_emails = sorted(
                self.processed_emails,
                key=lambda r: (r['category'], r.get('date', ''), r.get('subject', '')))
            with open(repartition_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                for record in sorted_emails:
                    writer.writerow({k: record.get(k, False if k == 'has_attachments' else '') for k in fieldnames})
            logging.info(f"Repartition report generated: {repartition_path}")
            return repartition_path
        except Exception as e:
            logging.error(f"Failed to generate repartition report: {e}")
            return None

    def generate_reports(self):
        return (
            self.generate_weekly_report(),
            self.generate_summary_report(),
            self.generate_repartition_report(),
        )
    
    def reset(self):
        """Reset statistics for a new reporting period."""
        self.processed_emails = []
        self.category_counts = defaultdict(int)
        self.error_count = 0
        self.attachment_count = 0
