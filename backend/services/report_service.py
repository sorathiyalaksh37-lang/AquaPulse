"""Report generation service for CPCB compliance and automated reports"""
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from config.config import Config

class ReportService:
    """Service for generating water quality reports"""
    
    def __init__(self):
        self.config = Config()
        self.reports_dir = self.config.REPORTS_DIR
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def generate_cpcb_report(self, readings_data, start_date, end_date, node_info=None):
        """Generate CPCB BIS 10500:2012 compliance report"""
        try:
            if not readings_data:
                return None, "No data available for report generation"
            
            df = pd.DataFrame(readings_data)
            
            # Calculate statistics for each parameter
            parameters_report = {}
            for param in ['pH', 'tds', 'turbidity', 'temperature', 'conductivity', 'dissolved_oxygen']:
                if param in df.columns:
                    values = df[param].values
                    
                    # Get CPCB standards
                    standard = self.config.CPCB_STANDARDS.get(param, {})
                    
                    # Calculate statistics
                    current = float(values[-1]) if len(values) > 0 else 0
                    min_val = float(np.min(values))
                    max_val = float(np.max(values))
                    avg_val = float(np.mean(values))
                    median_val = float(np.median(values))
                    std_dev = float(np.std(values))
                    
                    # Check compliance
                    is_compliant = (
                        standard.get('min', 0) <= current <= standard.get('max', float('inf'))
                    )
                    
                    # Calculate compliance percentage (readings within range)
                    compliant_readings = sum(
                        1 for v in values 
                        if standard.get('min', 0) <= v <= standard.get('max', float('inf'))
                    )
                    compliance_percentage = (compliant_readings / len(values)) * 100
                    
                    parameters_report[param] = {
                        'name': standard.get('name', param),
                        'current': round(current, 2),
                        'min': round(min_val, 2),
                        'max': round(max_val, 2),
                        'avg': round(avg_val, 2),
                        'median': round(median_val, 2),
                        'std_dev': round(std_dev, 2),
                        'unit': standard.get('unit', ''),
                        'cpcb_min': standard.get('min', 0),
                        'cpcb_max': standard.get('max', 0),
                        'is_compliant': is_compliant,
                        'compliance_percentage': round(compliance_percentage, 1),
                        'total_readings': len(values),
                        'compliant_readings': compliant_readings
                    }
            
            # Overall compliance score
            compliant_count = sum(1 for p in parameters_report.values() if p['is_compliant'])
            overall_compliance_score = round((compliant_count / len(parameters_report)) * 100, 2)
            
            # Determine overall status
            if overall_compliance_score == 100:
                overall_status = 'Fully Compliant'
            elif overall_compliance_score >= 80:
                overall_status = 'Mostly Compliant'
            elif overall_compliance_score >= 60:
                overall_status = 'Partially Compliant'
            else:
                overall_status = 'Non-Compliant'
            
            # Generate report ID
            report_id = f"CPCB-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            report_data = {
                'report_id': report_id,
                'report_type': 'cpcb_compliance',
                'title': f'CPCB BIS 10500:2012 Compliance Report',
                'generated_at': datetime.now().isoformat(),
                'start_date': start_date.isoformat() if isinstance(start_date, datetime) else start_date,
                'end_date': end_date.isoformat() if isinstance(end_date, datetime) else end_date,
                'node_info': node_info,
                'total_readings': len(df),
                'parameters': parameters_report,
                'compliance_score': overall_compliance_score,
                'overall_status': overall_status,
                'summary': self._generate_summary(parameters_report, overall_compliance_score),
                'recommendations': self._generate_recommendations(parameters_report)
            }
            
            return report_data, None
            
        except Exception as e:
            return None, f"Report generation failed: {str(e)}"
    
    def generate_daily_report(self, readings_data, date):
        """Generate daily summary report"""
        try:
            if not readings_data:
                return None, "No data available"
            
            df = pd.DataFrame(readings_data)
            
            # Count status distribution
            status_counts = {}
            if 'overall_status' in df.columns:
                status_counts = df['overall_status'].value_counts().to_dict()
            
            # Count anomalies
            anomaly_count = 0
            if 'is_anomaly' in df.columns:
                anomaly_count = df['is_anomaly'].sum()
            
            # Parameter averages
            parameter_averages = {}
            for param in ['pH', 'tds', 'turbidity', 'temperature', 'conductivity', 'dissolved_oxygen']:
                if param in df.columns:
                    parameter_averages[param] = round(df[param].mean(), 2)
            
            report_id = f"DAILY-{date.strftime('%Y%m%d')}"
            
            report_data = {
                'report_id': report_id,
                'report_type': 'daily_summary',
                'title': f'Daily Water Quality Report - {date.strftime("%B %d, %Y")}',
                'generated_at': datetime.now().isoformat(),
                'date': date.isoformat(),
                'total_readings': len(df),
                'status_distribution': status_counts,
                'anomaly_count': int(anomaly_count),
                'parameter_averages': parameter_averages,
                'summary': f"Collected {len(df)} readings on {date.strftime('%B %d, %Y')}. "
                          f"Detected {anomaly_count} anomalies."
            }
            
            return report_data, None
            
        except Exception as e:
            return None, f"Daily report generation failed: {str(e)}"
    
    def generate_weekly_report(self, readings_data, start_date, end_date):
        """Generate weekly compliance report"""
        try:
            if not readings_data:
                return None, "No data available"
            
            df = pd.DataFrame(readings_data)
            
            # Group by day
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            
            daily_stats = []
            for date in df['date'].unique():
                day_data = df[df['date'] == date]
                daily_stats.append({
                    'date': str(date),
                    'readings': len(day_data),
                    'safe_readings': len(day_data[day_data['overall_status'] == 'Safe']) if 'overall_status' in day_data.columns else 0,
                    'anomalies': day_data['is_anomaly'].sum() if 'is_anomaly' in day_data.columns else 0
                })
            
            report_id = f"WEEKLY-{start_date.strftime('%Y%m%d')}"
            
            report_data = {
                'report_id': report_id,
                'report_type': 'weekly_compliance',
                'title': f'Weekly Compliance Report',
                'generated_at': datetime.now().isoformat(),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_readings': len(df),
                'daily_breakdown': daily_stats,
                'summary': f"Weekly report from {start_date.strftime('%B %d')} to {end_date.strftime('%B %d, %Y')}. "
                          f"Total {len(df)} readings collected."
            }
            
            return report_data, None
            
        except Exception as e:
            return None, f"Weekly report generation failed: {str(e)}"
    
    def generate_monthly_report(self, readings_data, month, year):
        """Generate monthly trend report"""
        try:
            if not readings_data:
                return None, "No data available"
            
            df = pd.DataFrame(readings_data)
            
            # Calculate monthly trends
            trends = {}
            for param in ['pH', 'tds', 'turbidity', 'temperature', 'conductivity', 'dissolved_oxygen']:
                if param in df.columns:
                    values = df[param].values
                    trends[param] = {
                        'min': round(float(np.min(values)), 2),
                        'max': round(float(np.max(values)), 2),
                        'avg': round(float(np.mean(values)), 2),
                        'trend': self._calculate_trend(values)
                    }
            
            report_id = f"MONTHLY-{year}{month:02d}"
            
            report_data = {
                'report_id': report_id,
                'report_type': 'monthly_trend',
                'title': f'Monthly Trend Report - {datetime(year, month, 1).strftime("%B %Y")}',
                'generated_at': datetime.now().isoformat(),
                'month': month,
                'year': year,
                'total_readings': len(df),
                'trends': trends,
                'summary': f"Monthly analysis for {datetime(year, month, 1).strftime('%B %Y')}. "
                          f"Analyzed {len(df)} readings."
            }
            
            return report_data, None
            
        except Exception as e:
            return None, f"Monthly report generation failed: {str(e)}"
    
    def export_to_csv(self, report_data, filename=None):
        """Export report data to CSV"""
        try:
            if not filename:
                filename = f"{report_data['report_id']}.csv"
            
            filepath = os.path.join(self.reports_dir, filename)
            
            # Create DataFrame from parameters
            if 'parameters' in report_data:
                df = pd.DataFrame(report_data['parameters']).T
                df.to_csv(filepath)
                return filepath, None
            else:
                return None, "No parameter data to export"
                
        except Exception as e:
            return None, f"CSV export failed: {str(e)}"
    
    def export_to_pdf(self, report_data, filename=None):
        """Export report to PDF (placeholder)"""
        try:
            if not filename:
                filename = f"{report_data['report_id']}.pdf"
            
            filepath = os.path.join(self.reports_dir, filename)
            
            # TODO: Implement PDF generation using ReportLab or WeasyPrint
            # For now, create a simple text file
            with open(filepath.replace('.pdf', '.txt'), 'w') as f:
                f.write(f"Report: {report_data['title']}\n")
                f.write(f"Generated: {report_data['generated_at']}\n")
                f.write(f"Report ID: {report_data['report_id']}\n")
                f.write(f"\nSummary:\n{report_data.get('summary', 'N/A')}\n")
            
            return filepath, None
            
        except Exception as e:
            return None, f"PDF export failed: {str(e)}"
    
    def _generate_summary(self, parameters_report, compliance_score):
        """Generate executive summary"""
        compliant_params = [p['name'] for p in parameters_report.values() if p['is_compliant']]
        non_compliant_params = [p['name'] for p in parameters_report.values() if not p['is_compliant']]
        
        summary = f"Overall Compliance Score: {compliance_score}%\n\n"
        
        if compliance_score == 100:
            summary += "All water quality parameters are within CPCB BIS 10500:2012 safe limits. "
            summary += "Water quality is excellent and safe for consumption."
        elif compliance_score >= 80:
            summary += f"Most parameters are compliant. "
            if non_compliant_params:
                summary += f"Attention needed for: {', '.join(non_compliant_params)}."
        else:
            summary += f"Multiple parameters are out of safe range: {', '.join(non_compliant_params)}. "
            summary += "Immediate action required to improve water quality."
        
        return summary
    
    def _generate_recommendations(self, parameters_report):
        """Generate recommendations based on parameter status"""
        recommendations = []
        
        for param, data in parameters_report.items():
            if not data['is_compliant']:
                if param == 'pH':
                    if data['current'] < data['cpcb_min']:
                        recommendations.append({
                            'parameter': data['name'],
                            'issue': 'pH too low (acidic)',
                            'recommendation': 'Add alkaline substances to neutralize acidity. Check for industrial discharge.'
                        })
                    else:
                        recommendations.append({
                            'parameter': data['name'],
                            'issue': 'pH too high (alkaline)',
                            'recommendation': 'Add acid to neutralize alkalinity. Check for excessive detergent contamination.'
                        })
                
                elif param == 'tds':
                    recommendations.append({
                        'parameter': data['name'],
                        'issue': 'TDS exceeds safe limit',
                        'recommendation': 'Install RO filtration system. Check for industrial contamination or mineral deposits.'
                    })
                
                elif param == 'turbidity':
                    recommendations.append({
                        'parameter': data['name'],
                        'issue': 'High turbidity detected',
                        'recommendation': 'Improve filtration. Check for sediment in source water. Clean distribution system.'
                    })
                
                elif param == 'dissolved_oxygen':
                    recommendations.append({
                        'parameter': data['name'],
                        'issue': 'Low dissolved oxygen',
                        'recommendation': 'Improve aeration. Check for organic contamination or bacterial growth.'
                    })
        
        if not recommendations:
            recommendations.append({
                'parameter': 'Overall',
                'issue': 'All parameters within safe limits',
                'recommendation': 'Continue regular monitoring. Maintain current water treatment processes.'
            })
        
        return recommendations
    
    def _calculate_trend(self, values):
        """Calculate trend direction"""
        if len(values) < 2:
            return 'stable'
        
        # Simple linear regression
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        if abs(slope) < 0.01:
            return 'stable'
        elif slope > 0:
            return 'increasing'
        else:
            return 'decreasing'

# Singleton instance
report_service = ReportService()
