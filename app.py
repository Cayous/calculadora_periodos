# app.py
from flask import Flask, render_template, request, jsonify
from datetime import datetime
from dateutil.relativedelta import relativedelta

app = Flask(__name__)

def format_duration(start_date, end_date):
    duration = relativedelta(end_date, start_date)
    parts = []
    if duration.years > 0:
        parts.append(f"{duration.years} {'ano' if duration.years == 1 else 'anos'}")
    if duration.months > 0:
        parts.append(f"{duration.months} {'mês' if duration.months == 1 else 'meses'}")
    if duration.days > 0:
        parts.append(f"{duration.days} {'dia' if duration.days == 1 else 'dias'}")
    return ", ".join(parts)

def check_overlap(period1, period2):
    return (period1['start_date'] <= period2['end_date'] and 
            period1['end_date'] >= period2['start_date'])

def calculate_periods(file_content):
    try:
        # Processar as linhas do arquivo
        periods = [line.strip() for line in file_content.split('\n') if line.strip()]
        
        # Converter períodos para datas
        date_ranges = []
        for period in periods:
            start_str, end_str = period.split(" - ")
            start_date = datetime.strptime(start_str, "%d/%m/%Y")
            end_date = datetime.strptime(end_str, "%d/%m/%Y")
            date_ranges.append((start_date, end_date))

        # Calcular duração total
        total_start = min([start for start, end in date_ranges])
        total_end = max([end for start, end in date_ranges])
        total_duration = relativedelta(total_end, total_start)
        
        # Preparar períodos para processamento
        all_periods = []
        valid_periods = []

        for start_date, end_date in date_ranges:
            period = {
                'start_date': start_date,
                'end_date': end_date,
                'start_str': start_date.strftime('%d/%m/%Y'),
                'end_str': end_date.strftime('%d/%m/%Y'),
                'is_excluded': False
            }
            all_periods.append(period)

        # Ordenar períodos
        all_periods.sort(key=lambda x: x['start_date'])

        # Verificar sobreposições
        for period in all_periods:
            for valid_period in valid_periods:
                if check_overlap(valid_period, period):
                    period['is_excluded'] = True
                    break
            if not period['is_excluded']:
                valid_periods.append(period)

        # Preparar resultado
        result = {
            'total_duration': {
                'years': total_duration.years,
                'months': total_duration.months,
                'days': total_duration.days
            },
            'input_periods': periods,
            'analyzed_periods': []
        }

        for period in all_periods:
            result['analyzed_periods'].append({
                'period': f"{period['start_str']} a {period['end_str']}",
                'duration': format_duration(period['start_date'], period['end_date']),
                'is_excluded': period['is_excluded']
            })

        return result

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
