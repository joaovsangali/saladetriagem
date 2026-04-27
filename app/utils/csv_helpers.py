"""CSV export helpers: sanitization and response generation."""

import csv
from io import StringIO

from flask import make_response


def sanitize_csv_value(value):
    """Prevent CSV injection by escaping values that start with formula characters."""
    if value is None:
        return ''
    value = str(value)
    if value and value[0] in ('=', '+', '-', '@', '\t', '\r'):
        value = "'" + value
    return value


def generate_csv_response(data, filename):
    """Generate an HTTP response with a CSV file.

    :param data: Iterable of iterables (rows), each row is a list of values.
    :param filename: The filename for the Content-Disposition header.
    :returns: Flask response object.
    """
    output = StringIO()
    writer = csv.writer(output)

    for row in data:
        sanitized_row = [sanitize_csv_value(v) for v in row]
        writer.writerow(sanitized_row)

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response
