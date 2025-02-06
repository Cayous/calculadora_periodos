# app.py
from flask import Flask, render_template, request, jsonify
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import os

app = Flask(__name__)

def format_duration(years, months, days):
    parts = []
    if years > 0:
        parts.append(f"{years} {'ano' if years == 1 else 'anos'}")
    if months > 0:
        parts.append(f"{months} {'mês' if months == 1 else 'meses'}")
    if days > 0 or not parts:
        parts.append(f"{days} {'dia' if days == 1 else 'dias'}")
    return " ".join(parts)

def merge_periods(periods):
    if not periods:
        return []
    
    sorted_periods = sorted([(start, end) for start, end in periods], key=lambda x: x[0])
    merged = [sorted_periods[0]]
    
    for current_start, current_end in sorted_periods[1:]:
        last_start, last_end = merged[-1]
        
        if current_start <= last_end:
            merged[-1] = (min(last_start, current_start), max(last_end, current_end))
        else:
            merged.append((current_start, current_end))
    
    final_merged = []
    for period in merged:
        start, end = period
        keep = True
        for other_start, other_end in merged:
            if period != (other_start, other_end) and other_start <= start and end <= other_end:
                keep = False
                break
        if keep:
            final_merged.append(period)
    
    adjustments = []
    for i in range(1, len(final_merged)):
        prev_end = final_merged[i-1][1]
        curr_start, curr_end = final_merged[i]
        if curr_start <= prev_end:
            new_start = prev_end + relativedelta(days=1)
            if new_start < curr_end:
                adjustments.append((new_start, curr_end))
    final_merged = final_merged[:1] + adjustments
    
    return sorted(final_merged, key=lambda x: x[0])

def sum_durations(durations):
    base_date = date(1, 1, 1)
    current_date = base_date
    
    for years, months, days in durations:
        current_date += relativedelta(
            years=years,
            months=months,
            days=days
        )
    
    total_delta = relativedelta(current_date, base_date)
    return (total_delta.years, total_delta.months, total_delta.days)

def calculate_periods(file_content):
    try:
        periods = [line.strip() for line in file_content.split('\n') if line.strip()]
        date_ranges = []
        
        for period in periods:
            start_str, end_str = period.split(" a ")
            start_date = datetime.strptime(start_str, "%d/%m/%Y").date()
            end_date = datetime.strptime(end_str, "%d/%m/%Y").date()
            date_ranges.append((start_date, end_date))
        
        merged_periods = merge_periods(date_ranges)
        durations = []
        
        for start, end in merged_periods:
            delta = relativedelta(end + relativedelta(days=1), start)
            durations.append((delta.years, delta.months, delta.days))
        
        total_years, total_months, total_days = sum_durations(durations)
        merged_tuples = set(merged_periods)
        analyzed_periods = []
        
        for original_start, original_end in date_ranges:
            original_tuple = (original_start, original_end)
            delta = relativedelta(original_end + relativedelta(days=1), original_start)
            duration_str = format_duration(delta.years, delta.months, delta.days)
            is_excluded = original_tuple not in merged_tuples
            
            analyzed_periods.append({
                'period': f"{original_start.strftime('%d/%m/%Y')} a {original_end.strftime('%d/%m/%Y')}",
                'duration': duration_str,
                'is_excluded': is_excluded
            })
        
        return {
            'total_duration': {
                'years': total_years,
                'months': total_months,
                'days': total_days
            },
            'input_periods': periods,
            'analyzed_periods': analyzed_periods
        }
    
    except Exception as e:
        return {'error': str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'})

    try:
        content = file.read().decode('utf-8')
        result = calculate_periods(content)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)