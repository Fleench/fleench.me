import datetime
def main(**context):
    return f"<p>Last built: {datetime.datetime.now().date()}</p>"